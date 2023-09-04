from django.db import models
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
    class Meta :
        verbose_name = 'UsuarioCredencial'
        verbose_name_plural = 'UsuarioCredencials'
        db_table = 'usuariocredencial'
        ordering = ['id']