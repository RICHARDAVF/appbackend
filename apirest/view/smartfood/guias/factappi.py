from time import time
from hmac import new
from hashlib import sha256
class RequestAPI:
    def __init__(self,access_key:str,secret_key:str):
        self.access_key = access_key
        self.secret_key = secret_key
        self.timestatp = str(int(time()))
        self.signature = f"{self.access_key}|{self.timestatp}"
    def encryptdates(self):
        return new(self.secret_key.encode(),self.signature.encode(),sha256).hexdigest(),self.timestatp