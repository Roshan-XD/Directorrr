"""Explicit metadata-only rehearsal. No transfers, inference or Resolve mutations."""
import json
import urllib.request
import urllib.error
from pathlib import Path
from urllib.parse import urlencode

BASE="http://127.0.0.1:5173/api"
HEADERS={"Origin":"http://127.0.0.1:5173","X-Director-Session":"launcher"}
def read(path,headers=HEADERS):
    request=urllib.request.Request(BASE+path,headers=headers)
    try:
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request,timeout=35) as reply:
            return reply.status,json.load(reply)
    except urllib.error.HTTPError as exc:return exc.code,{"error":"HTTP "+str(exc.code)}
def main():
    report={"metadata_only":True,"downloads_started":0,"inference_started":0,"resolve_mutations":0,"searches":[]}
    for path in ("/product/models","/product/studio","/product/downloads","/dev/generation/config"):
        status,data=read(path);report[path]={"status":status}
        if path.endswith("models"):report[path]["models"]=[{"id":m["id"],"runnable":m["runnable"],"installed":m["installed"]} for m in data.get("models",[])]
    report["missing_key_status"]=read("/product/studio",{})[0]
    report["untrusted_origin_status"]=read("/product/studio",{**HEADERS,"Origin":"http://evil.example"})[0]
    for query in ("Qwen3","stable-diffusion","whisper"):
        status,data=read("/product/discovery?"+urlencode({"q":query,"sort":"downloads"}))
        result={"query":query,"status":status,"count":len(data.get("items",[])),"cached":data.get("cached"),"repositories":[i["id"] for i in data.get("items",[])]}
        if data.get("items"):
            repository=data["items"][0]["id"]
            code,card=read("/product/discovery/details?"+urlencode({"repository":repository}))
            result["details"]={"status":code,"repository":repository,"revision":card.get("revision"),"files":len(card.get("files",[])),"runnable":card.get("runnable"),"cached":card.get("cached")}
        report["searches"].append(result)
        print(json.dumps(result))
    root=Path(__file__).resolve().parents[1]
    (root/"docs/creative-studio-live-check.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print("Saved sanitized metadata-only rehearsal report")
if __name__=="__main__":main()
