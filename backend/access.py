"""Local role access. Tokens never enter research exports."""
import base64,hashlib,hmac,json,os,secrets,time
from pathlib import Path

class Access:
    def __init__(self, root):
        keyfile=Path(root)/'.access-key'
        try:
            with keyfile.open('xb') as f:f.write(secrets.token_bytes(32))
        except FileExistsError:pass
        self.key=keyfile.read_bytes()
        self.password=os.environ.get('EYETRACK_RESEARCHER_PASSWORD') or secrets.token_urlsafe(18)
        self.failures={}
        if not os.environ.get('EYETRACK_RESEARCHER_PASSWORD'):
            print('EyeTrack researcher login password (this run): '+self.password,flush=True)
    def issue(self,role,sid=''):
        payload=base64.urlsafe_b64encode(json.dumps({'role':role,'sid':sid,'exp':time.time()+(28800 if role=='researcher' else 604800)}).encode()).decode().rstrip('=')
        signature=hmac.new(self.key,payload.encode(),hashlib.sha256).hexdigest()
        return payload+'.'+signature
    def verify(self,token):
        try:
            payload,signature=token.split('.')
            if not hmac.compare_digest(signature,hmac.new(self.key,payload.encode(),hashlib.sha256).hexdigest()):return None
            value=json.loads(base64.urlsafe_b64decode(payload+'='*(-len(payload)%4)))
            return value if value['exp']>time.time() else None
        except (ValueError,KeyError,TypeError):return None
    def login(self,password,client):
        now=time.monotonic();recent=[t for t in self.failures.get(client,[]) if now-t<60]
        if len(recent)>=5:return None
        if not isinstance(password,str) or not secrets.compare_digest(password,self.password):
            self.failures[client]=recent+[now];return None
        self.failures.pop(client,None)
        return self.issue('researcher')
