"""Bounded application events, not a command shell or raw environment dump."""
import re
import threading
from collections import deque
from datetime import datetime, timezone
class ActivityConsole:
    def __init__(self, secrets=()):
        self.secrets=tuple(s for s in secrets if s)
        self.events=deque(maxlen=300); self.lock=threading.RLock()
    def redact(self,text):
        value=str(text)[:2000]
        for secret in self.secrets: value=value.replace(secret,"[redacted]")
        value=re.sub(r"(?i)(authorization|x-director-key|token|password|secret)\s*[:=]\s*[^\s,;]+",r"\1=[redacted]",value)
        return re.sub(r"\b(?:hf_[A-Za-z0-9]{8,}|Bearer\s+[^\s]+)","[redacted]",value,flags=re.I)
    def add(self,stage,message,level="info"):
        with self.lock:
            event={"time":datetime.now(timezone.utc).isoformat(),"stage":self.redact(stage),"message":self.redact(message),"level":level}
            if self.events and all(self.events[-1][k]==event[k] for k in ("stage","message","level")):
                self.events[-1]["count"]=self.events[-1].get("count",1)+1
                self.events[-1]["time"]=event["time"]
            else: self.events.append(event)
    def read(self):
        with self.lock: return {"events":list(self.events)}
    def clear(self):
        with self.lock: self.events.clear()
