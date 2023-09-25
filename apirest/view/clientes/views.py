from rest_framework import generics
from rest_framework.response import Response
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication


@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
class ViewPrueba(generics.GenericAPIView):
    def post(self,request,*args,**kwargs):
        return Response({"data":'post'})
    def get(self,request,*args,**kwargs):
        return Response({"peticion":"get"})