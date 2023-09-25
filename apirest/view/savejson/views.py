from rest_framework import generics
from rest_framework.response import Response
class SaveJSON(generics.GenericAPIView):
    def post(self,request,*args,**kwargs):
        res = {}
        res['response'] = "respuesta"
        return Response(res)