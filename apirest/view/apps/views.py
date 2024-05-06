from rest_framework.generics import GenericAPIView
from django.http import FileResponse,HttpResponse
import os
from django.conf import settings
class DownloadAppView(GenericAPIView):
    def get(self,request,*args,**kwargs):
        apk = os.path.join(settings.BASE_DIR,'media',r'apk\app-release.apk')
        return FileResponse(open(apk,'rb'),as_attachment=True)
class DownloadAppV1(GenericAPIView):
    def get(self,request,*args,**kwargs):
        apk = os.path.join(settings.BASE_DIR,'media',r'apk\app-release.apk')
        return FileResponse(open(apk,'rb'),as_attachment=True)
class DownloadAppMapring(GenericAPIView):
    def get(self,request,*args,**kwargs):
        apk = os.path.join(settings.BASE_DIR,'media',r'apk\mapring.apk')
        return FileResponse(open(apk,'rb'),as_attachment=True)