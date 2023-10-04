from rest_framework import generics
from rest_framework.response import Response


class ViewPrueba(generics.GenericAPIView):
    def post(self,request,*args,**kwargs):
        return Response({"data":'post'})
    def get(self,request,*args,**kwargs):
        return Response({"peticion":"get"})