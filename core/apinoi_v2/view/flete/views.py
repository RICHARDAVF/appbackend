from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from apirest.credenciales import Credencial
from apirest.querys import CAQ
from datetime import datetime

from apirest.view.generate_id import gen_id
class FleteView1(GenericAPIView):
    fecha : datetime = datetime.now()
    def post(self,request,*args,**kwargs):
        data = {}
        datos = request.data
        self.credencial = Credencial(datos['credencial'])
        self.flete = 0
        try:
            codigos = ','.join(f"'{i}'" for i in datos['codigos'])
            sql = f"SELECT art_flegra FROM t_articulo WHERE art_codigo IN ({codigos})"
           
            s,res_articulos = CAQ.request(self.credencial,sql,(),'get',1)
            if not s:
                raise ValueError(res['error'])
            sql = f"""SELECT par_delart,par_delmon,par_delmo2,par_delmo3 FROM t_parrametro where par_anyo='{self.fecha.year}' """
            s,res = CAQ.request(self.credencial,sql,(),'get',0)
            if not s:
                raise ValueError(res['error'])
            codigo_articulo_flete = res[0].strip()
            cercano = float(res[1])
            lejano = float(res[2])
            provincia = float(res[3])
            sql = f""" SELECT  art_codigo,art_nombre FROM t_articulo where art_codigo=? """
            s,res_art_flete = CAQ.request(self.credencial,sql,(codigo_articulo_flete,),'get',0)
          
            if not s:
                raise ValueError(res_art_flete['error'])
            if self.validar_flete(res_articulos):
                self.flete = 1
            sql = """
                SELECT a.ubi_codigo,a.ubi_flete FROM mk_ubigeo AS a
                INNER JOIN t_auxiliar AS b ON a.ubi_CODIGO = b.AUX_EDI
                WHERE b.AUX_CLAVE = ?
            """
            params = (datos['codigo_cliente'])
            s,res = CAQ.request(self.credencial,sql,params,'get',0)
            if not s:
                raise ValueError(res['error'])
            data = {
                    'id':gen_id(),
                    'codigo':res_art_flete[0].strip(),
                    'nombre':res_art_flete[1].strip(),
                    'precio':self.eval_ubigeo_for_precio(cercano,lejano,provincia,res[0].strip(),res[1],datos['monto']),
                    'monto':self.eval_ubigeo_for_precio(cercano,lejano,provincia,res[0].strip(),res[1],datos['monto']),
                    'cantidad':1,
                    "descuento":0,
                    "total":self.eval_ubigeo_for_precio(cercano,lejano,provincia,res[0].strip(),res[1],datos['monto']),
                    "tipo":"F",
                    "talla":'x',
                    "lote":'',
                    "lista_precio":"",
                    "precio_parcial":0,
                    "peso":0,
                    'fecha':'',
                    'obs':'',
                    'flete_gratis':self.flete,
                    'adicional':{
                        "cantidad":1,
                        "combo":[]
                    }
            }
        except Exception as e:
            data['error'] = f"Ocurrio un error :{str(e)}"
        return Response(data)
    def validar_flete(self,data)->bool:
        for value in data:
            if int(value[0])==1:
                return True
        return False
    def eval_ubigeo_for_precio(self,monto1,monto2,monto3,ubigeo:str,flete,monto):
        precio = 0
        if (ubigeo.startswith('1501') or ubigeo.startswith('0701')) and flete==0:
            precio = monto1
            if monto>=600:
                self.flete = 1
          
        elif (ubigeo.startswith('1501') or ubigeo.startswith('0701')) and flete==1:
            precio = monto2
            if monto>=1000:
                self.flete = 1
        else:
            precio = monto3
      
        return precio
class FleteView2(GenericAPIView):
    fecha :datetime = datetime.now()
    def post(self,request,*args,**kwargs):
        data = {}
        datos = request.data
        self.credencial = Credencial(datos['credencial'])
        try:
            sql = f"""SELECT 
                a.par_delar2,
                b.art_nombre,
                a.par_monde2 
                FROM t_parrametro AS a
                LEFT JOIN t_articulo AS b ON a.par_delar2=b.art_codigo
                WHERE 
                    par_anyo='{self.fecha.year}' """
            s,res = CAQ.request(self.credencial,sql,(),'get',0)
            if not s:
                raise ValueError(res['error'])
            data = {
                    'id':gen_id(),
                    'codigo':res[0].strip(),
                    'nombre':res[1].strip(),
                    'precio':res[2],
                    'monto':res[2],
                    'cantidad':1,
                    "descuento":0,
                    "total":res[2],
                    "tipo":"F",
                    "talla":'x',
                    "lote":'',
                    "lista_precio":"",
                    "precio_parcial":0,
                    "peso":0,
                    'fecha':'',
                    'obs':'',
                    'flete_gratis':0,
                    'adicional':{
                        "cantidad":1,
                        "combo":[]
                    }
            }
        except Exception as e:
            data['error'] = f"Ocurrio un error: {str(e)}"
        return Response(data)
class POSView(GenericAPIView):
    fecha :datetime = datetime.now()
    def post(self,request,*args,**kwargs):
        data = {}
        datos = request.data
        self.credencial = Credencial(datos['credencial'])
        try:
            sql = f"""SELECT 
                a.par_posart,
                b.art_nombre,
                a.par_pospor 
                FROM t_parrametro AS a
                LEFT JOIN t_articulo AS b ON a.par_posart=b.art_codigo
                WHERE 
                    par_anyo='{self.fecha.year}' """
            s,res = CAQ.request(self.credencial,sql,(),'get',0)
            if not s:
                raise ValueError(res['error'])
            data = {
                    'id':gen_id(),
                    'codigo':res[0].strip(),
                    'nombre':res[1].strip(),
                    'precio':res[2],
                    'monto':res[2],
                    'cantidad':1,
                    "descuento":0,
                    "total":res[2],
                    "tipo":"P",
                    "talla":'x',
                    "lote":'',
                    "lista_precio":"",
                    "precio_parcial":0,
                    "peso":0,
                    'fecha':'',
                    'obs':'',
                    'flete_gratis':0,
                    'adicional':{
                        "cantidad":1,
                        "combo":[]
                    }
            }
        except Exception as e:
            data['error'] = f"Ocurrio un error: {str(e)}"
        return Response(data)
class ValeMonto(GenericAPIView):
    def post(self,request,*args,**kwargs):
        data = {}
        datos = request.data
        self.credencial = Credencial(datos['credencial'])
        try:
            monto = datos['monto']
            codigo = datos['codigo_vale']
            sql = f"""
                SELECT 
                    vig_numero,
                    prm_monto,
                    prm_dscto,
                    prm_usado 
                FROM t_descuento_vale
                WHERE 
                    VIG_DESDE<=GETDATE() AND VIG_HASTA>=GETDATE()
                    AND vig_numero=?
                """
            s,res = CAQ.request(self.credencial,sql,(codigo,),'get',0)
            if not s:
                raise ValueError(res['error'])
            elif res is None:
                raise ValueError('El numero de vale no es valido')
            elif res[3]==1:
                raise ValueError("El vale ya fue usado")
            elif res[1]>monto:
                raise ValueError("El monto de la venta no aplica para el vale")
            data = {
                "vale_codigo":res[0].strip(),
                "vale_monto":res[2],
                "vale_monto_ref":res[1]
            }
        except Exception as e:
            data['error'] = f"Ocurrio un error:{str(e)}"
        return Response(data)