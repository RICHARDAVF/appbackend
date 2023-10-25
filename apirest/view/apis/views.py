from typing import Any
from rest_framework import generics
from rest_framework.response import Response
from apirest.querys import Validation
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
