from time import time
from hmac import new
from hashlib import sha256
from rest_framework import generics
from rest_framework.response import Response
from apirest.querys import Validation
import requests
from datetime import datetime
class SearchDNIRUC(generics.GenericAPIView):
    def get(self,request,*args,**kwagrs):
        doc = kwagrs['doc']
        tipo = kwagrs['tipo']
        data = {}
        try:
            data = Validation(doc,tipo).valid()
         
        except Exception as e:
            data ['error'] = f"Ocurrio un error : {str(e)}"
        return Response(data)
class TipoCambio:
    @classmethod
    def tipo_cambio(self):
        res = requests.get(f"https://api.apis.net.pe/v1/tipo-cambio-sunat?fecha={datetime.now().strftime('%Y-%m-%d')}")
        return res['venta']

class GenerateToken:
    def __init__(self,access_key:str,secret_key:str):
        self.access_key = access_key
        self.secret_key = secret_key
        self.timestatp = str(int(time()))
        self.signature = f"{self.access_key}|{self.timestatp}"

    def encryptdates(self)->tuple[str,str]:
        return new(self.secret_key.encode(),self.signature.encode(),sha256).hexdigest(),self.timestatp