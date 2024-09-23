from django.contrib import admin
from .models import UsuarioCredencial,VersionApp,ConfigCliente
from rest_framework.authtoken.models import Token
# Register your models here.

class AdminViewUsuario(admin.ModelAdmin):
    list_display=('id','ruc','razon_social','bdhost',\
                  'bdname','bduser','bdpassword','bdport','tallas','lote','status','codigo')
    list_editable = ('ruc','razon_social','bdhost','bdname','bduser','bdpassword','bdport','tallas','lote','status','codigo')
admin.site.register(UsuarioCredencial,AdminViewUsuario)

class AdminViewVersionApp(admin.ModelAdmin):
    list_display = ('id','nombre','version','fecha')
admin.site.register(VersionApp,AdminViewVersionApp)

class AdminViewConfigCLient(admin.ModelAdmin):
    list_display = ('cliente','separacion_pedido','cliente_user','guid_lote','valida_stock')
    list_editable = ('separacion_pedido','cliente_user','guid_lote','valida_stock')
admin.site.register(ConfigCliente,AdminViewConfigCLient)