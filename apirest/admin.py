from django.contrib import admin
from .models import UsuarioCredencial
from rest_framework.authtoken.models import Token
# Register your models here.

class AdminViewUsuario(admin.ModelAdmin):
    list_display=('id','ruc','razon_social','bdhost',\
                  'bdname','bduser','bdpassword','bdport','tallas','lote','status')
    list_editable = ('ruc','razon_social','bdhost','bdname','bduser','bdpassword','bdport','tallas','lote','status')
    


        
admin.site.register(UsuarioCredencial,AdminViewUsuario)

