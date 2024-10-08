from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
import os
from django.conf import settings
class UsuarioCredencial(models.Model):
    ruc = models.CharField(max_length=50,verbose_name="RUC",null=True,blank=True)
    razon_social = models.CharField(max_length=254,verbose_name='Razon Social',null=True,blank=True)
    bdhost = models.CharField(max_length=254,verbose_name='Direccion IP o Host ',null=True,blank=True)
    bdname = models.CharField(max_length=254,verbose_name='Nombre de la BD',null=True,blank=True)
    bduser = models.CharField(max_length=254,verbose_name='Usuario de la BD',null=True,blank=True)
    bdpassword = models.CharField(max_length=254,verbose_name='Password de la BD',null=True,blank=True)
    bdport = models.CharField(max_length=254,verbose_name='Port de la BD',null=True,blank=True)
    tallas = models.BooleanField(verbose_name='Meneja Tallas', default=False)
    lote = models.BooleanField(verbose_name='Meneja Lote', default=False)
    status = models.BooleanField(verbose_name="Estado",default=False)
    codigo = models.CharField(max_length=10,verbose_name="Codigo cliente",null=True,blank=True)
    class Meta :
        verbose_name = 'UsuarioCredencial'
        verbose_name_plural = 'UsuarioCredencials'
        db_table = 'usuariocredencial'
        ordering = ['id']
    def __str__(self) -> str:
        return self.razon_social
class ConfigCliente(models.Model):
    cliente = models.ForeignKey(UsuarioCredencial,on_delete=models.CASCADE)
    separacion_pedido = models.BooleanField(default=False,verbose_name="Separacion de pedido")
    cliente_user = models.BooleanField(verbose_name='Cliente asignado por usuario',default=False)
    guid_lote = models.BooleanField(verbose_name='El campo Lote es string',default=False)
    valida_stock = models.BooleanField(verbose_name="Valida stock",default=True)
    class Meta:
        verbose_name = "Configuracion del Cliente"
        verbose_name_plural = "Configuracion de Clientes"
        db_table = 'config_cliente'
    def __str__(self):
        return self.cliente.razon_social
class VersionApp(models.Model):
    nombre = models.CharField(max_length=50,verbose_name="Nombre de la version")
    version = models.CharField(max_length=50,verbose_name="Version de la applicacion")
    fecha = models.DateField(auto_created=False,verbose_name="Fecha de la ultima actualizacion")
    apk_file = models.FileField(upload_to='apk/',verbose_name="Archivo de al aplicacion",null=True,blank=True)
    class Meta:
        verbose_name = "version"
        verbose_name_plural = "Versiones"
        db_table = 'versiones'
    def get_file(self):
        if self.apk_file:
            return f"{os.path.join(settings.MEDIA_ROOT,self.apk_file)}"
        return os.path.join(settings.MEDIA_ROOT,'app-release.apk')

@receiver(post_save,sender=UsuarioCredencial)
def add_automatic_c(sender,instance,created,**kwargs):
    if created:
        ConfigCliente.objects.create(cliente_id=instance.id)
