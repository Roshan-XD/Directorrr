"""Metadata-only official Hugging Face discovery; never repository execution."""
import json
import re
import secrets
import threading
from functools import wraps
from urllib.parse import urlsplit, parse_qs
import httpx
from director.installations.schemas import ManagerError
from director.models.validation import repository_id

REPOSITORY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}/[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$")
def serialized(method):
    @wraps(method)
    def call(self, *args, **kwargs):
        with self.lock: return method(self, *args, **kwargs)
    return call

class Discovery:
    def __init__(self, fetch=None):
        self.fetch=fetch or self._fetch
        self.cache={}
        self.details_cache={}
        self.cursors={}
        self.next_link=None
        self.lock=threading.RLock()
        self.cache_storage=None
    def attach_cache(self,storage):
        with self.lock:
            self.cache_storage=storage
            path=storage.path("discovery-cache.json")
            if path.exists():
                try:
                    storage.ensure_owned();value=storage.read_json(path)
                    if value.get("version")!=1:raise ValueError()
                    self.cache={k:v for k,v in list(value.get("search",{}).items())[-20:] if isinstance(v,dict) and isinstance(v.get("items"),list)}
                    self.details_cache={k:v for k,v in list(value.get("details",{}).items())[-10:] if REPOSITORY.fullmatch(k) and isinstance(v,dict) and re.fullmatch(r"[0-9a-f]{40}",str(v.get("revision")))}
                    for item in self.cache.values():item["next_cursor"]=None
                except (OSError,ValueError,TypeError,AttributeError):
                    self.cache={};self.details_cache={}
    def _persist(self):
        if not self.cache_storage:return
        value={"version":1,"search":self.cache,"details":self.details_cache}
        while len(json.dumps(value).encode())>3*1024*1024 and self.details_cache:self.details_cache.pop(next(iter(self.details_cache)))
        try:
            self.cache_storage.ensure_owned();self.cache_storage.write_json(self.cache_storage.path("discovery-cache.json"),value)
        except (OSError,ValueError):pass # Live metadata remains usable if the cache cannot be saved.
    @serialized
    def _fetch(self,path,params=None):
        # Fixed host, no redirects, credentials, model downloads or trust in repository URLs.
        with httpx.Client(timeout=10,trust_env=False,follow_redirects=False) as client:
            with client.stream("GET","https://huggingface.co"+path,params=params) as response:
                response.raise_for_status(); data=bytearray()
                self.next_link=response.links.get("next",{}).get("url")
                for chunk in response.iter_bytes():
                    data.extend(chunk)
                    if len(data)>(128*1024 if "/raw/" in path else 2*1024*1024): raise ValueError("Metadata response too large")
                return data.decode("utf-8") if "/raw/" in path else json.loads(data)
    @serialized
    def search(self,query, *, author="", task="", sort="downloads", cursor=None):
        if not 0<=len(query.strip())<=80 or any(ord(c)<32 for c in query):
            raise ManagerError("invalid_search","Enter a search of 1 to 80 characters",422)
        if author and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,95}",author):
            raise ManagerError("invalid_author","Invalid publisher",422)
        if task not in {"","text-to-video","image-to-video","text-to-image","image-to-image","text-to-audio","automatic-speech-recognition"} or sort not in {"downloads","lastModified","likes","trendingScore"}:
            raise ManagerError("invalid_filter","Unsupported catalog filter",422)
        identity=(query.strip().casefold(),author,task,sort)
        key=str((identity,cursor))
        params={"search":query.strip(),"limit":12,"full":"true","cardData":"true","sort":sort,"direction":-1}
        if author: params["author"]=author
        if task: params["pipeline_tag"]=task
        if cursor:
            record=self.cursors.get(cursor)
            if not record or record[0]!=identity:
                raise ManagerError("invalid_cursor","Search page expired; restart the search",422)
            params=record[1]
        try:
            self.next_link=None
            raw=self.fetch("/api/models",params)
            if not isinstance(raw,list): raise ValueError("Invalid metadata")
            items=[]
            for item in raw[:12]:
                repository=item.get("id","") if isinstance(item,dict) else ""
                if not REPOSITORY.fullmatch(repository): continue
                try: repository_id(repository)
                except ValueError: continue
                card=item.get("cardData") or {}
                if not isinstance(card,dict): card={}
                items.append({"id":repository,"title":repository,"source":"https://huggingface.co/"+repository,
                    "license":str(card.get("license","unknown"))[:160],
                    "pipeline":str(item.get("pipeline_tag","unknown"))[:80],
                    "downloads":item.get("downloads") if isinstance(item.get("downloads"),int) else None,
                    "likes":item.get("likes") if type(item.get("likes")) is int else None,
                    "updated":item.get("lastModified") if isinstance(item.get("lastModified"),str) else None,
                    "gated":item.get("gated") in (True,"auto","manual"),
                    "license_state":license_state(str(card.get("license","unknown"))),
                    "status":"discovered_not_runnable", "revision":item.get("sha") if re.fullmatch(r"[0-9a-f]{40}",str(item.get("sha",""))) else None})
            next_cursor=None
            if self.next_link:
                link=urlsplit(self.next_link)
                if link.scheme=="https" and link.netloc=="huggingface.co" and link.path=="/api/models":
                    next_params=parse_qs(link.query)
                    # Follow only a server-provided same-endpoint cursor, never a client URL.
                    if "cursor" in next_params and len(link.query)<8192:
                        next_cursor=secrets.token_hex(16)
                        if len(self.cursors)>=100: self.cursors.pop(next(iter(self.cursors)))
                        self.cursors[next_cursor]=(identity,{**params,"cursor":next_params["cursor"][0]})
            result={"items":items,"cached":False,"next_cursor":next_cursor,"message":"Discovery does not install or establish Director compatibility."}
            if len(self.cache)>=20: self.cache.pop(next(iter(self.cache)))
            self.cache[key]=result
            self._persist()
            return result
        except (httpx.HTTPError,ValueError,TypeError,KeyError):
            if key in self.cache: return {**self.cache[key],"cached":True,"message":"Offline: showing the last successful metadata result."}
            raise ManagerError("discovery_unavailable","Hugging Face metadata is unavailable. Installed models remain usable.",502)

    @serialized
    def details(self,repository):
        if not REPOSITORY.fullmatch(repository): raise ManagerError("invalid_repository","Invalid repository identity",422)
        try:
            repository_id(repository)
            metadata=self.fetch("/api/models/"+repository,{"blobs":"true"})
            revision=metadata.get("sha")
            if not re.fullmatch(r"[0-9a-f]{40}",str(revision)): raise ValueError("Unpinned metadata")
            # Re-query the immutable revision: a moving branch may change during inspection.
            pinned=self.fetch("/api/models/"+repository+"/revision/"+revision,{"blobs":"true"})
            if not isinstance(pinned,dict) or pinned.get("sha")!=revision:
                raise ValueError("Metadata revision changed")
            card=self.fetch("/"+repository+"/raw/"+revision+"/README.md")
            if not isinstance(card,str) or len(card.encode())>128*1024: raise ValueError("Model card too large")
            siblings=pinned.get("siblings",[])
            if not isinstance(siblings,list) or len(siblings)>1000:
                raise ValueError("File inventory exceeds inspection limit")
            files=[]
            for item in siblings:
                if not isinstance(item,dict): raise ValueError("Invalid file metadata")
                name=item.get("rfilename")
                if not isinstance(name,str) or len(name)>512 or any(ord(c)<32 for c in name):
                    raise ValueError("Invalid file identity")
                size=item.get("size")
                if size is not None and (type(size) is not int or size<0):
                    raise ValueError("Invalid file size")
                lfs=item.get("lfs") or {}
                digest=lfs.get("sha256") if isinstance(lfs,dict) else None
                if digest is not None and not re.fullmatch(r"[0-9a-f]{64}",str(digest)):
                    raise ValueError("Invalid published hash")
                files.append({"name":name,"size":size,"sha256":digest})
            tags=pinned.get("tags",[])
            if not isinstance(tags,list): tags=[]
            card_data=pinned.get("cardData") or {}
            if not isinstance(card_data,dict): card_data={}
            # Plain text only. The frontend renders this as text, never HTML/Markdown execution.
            result={"repository":repository,"revision":revision,"card_text":card,"runnable":False,
                    "publisher":repository.split("/")[0],"gated":pinned.get("gated") in (True,"auto","manual"),
                    "downloads":pinned.get("downloads") if type(pinned.get("downloads")) is int else None,
                    "likes":pinned.get("likes") if type(pinned.get("likes")) is int else None,
                    "license_state":license_state(str(card_data.get("license","unknown"))),
                    "license":str(card_data.get("license","unknown"))[:160],
                    "pipeline":str(pinned.get("pipeline_tag","unknown"))[:80],
                    "updated":pinned.get("lastModified") if isinstance(pinned.get("lastModified"),str) else None,
                    "tags":[t[:160] for t in tags[:40] if isinstance(t,str)],"files":files,
                    "repository_bytes":sum(f["size"] for f in files) if all(f["size"] is not None for f in files) and files else None,
                    "cached":False,"message":"Published repository inventory, not a selected installation recipe or Director validation."}
            if len(self.details_cache)>=20: self.details_cache.pop(next(iter(self.details_cache)))
            self.details_cache[repository]=result
            self._persist()
            return result
        except (httpx.HTTPError,ValueError,KeyError,TypeError) as exc:
            if repository in self.details_cache:
                return {**self.details_cache[repository],"cached":True,"message":"Offline: showing the last inspected immutable revision."}
            raise ManagerError("metadata_unavailable","Bounded model-card metadata is unavailable",502) from exc

def license_state(identifier):
    if identifier in {"apache-2.0","mit","bsd-2-clause","bsd-3-clause","isc","cc0-1.0"}:
        return "known_permissive_declaration"
    if identifier in {"unknown","", "None"}: return "unknown"
    return "restricted_or_other_terms_review_required"
