from django.contrib import admin
from .models import UsuarioCredencial,VersionApp
from rest_framework.authtoken.models import Token
# Register your models here.

class AdminViewUsuario(admin.ModelAdmin):
    list_display=('id','ruc','razon_social','bdhost',\
                  'bdname','bduser','bdpassword','bdport','tallas','lote','status')
    list_editable = ('ruc','razon_social','bdhost','bdname','bduser','bdpassword','bdport','tallas','lote','status')
    


        
admin.site.register(UsuarioCredencial,AdminViewUsuario)

class AdminViewVersionApp(admin.ModelAdmin):
    list_display = ('id','nombre','version','fecha')
admin.site.register(VersionApp,AdminViewVersionApp)

