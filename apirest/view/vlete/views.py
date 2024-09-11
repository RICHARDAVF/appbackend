from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from apirest.credenciales import Credencial
from apirest.querys import CAQ
from datetime import datetime
class FleteView(GenericAPIView):
    fecha : datetime = datetime.now()
    def get(self,request,*args,**kwargs):
        data = {}
        try:
            pass
        except Exception as e:
            data['error'] = f"Ocurrio un error :{str(e)}"
        return Response(data)
    def post(self,request,*args,**kwargs):
        data = {}
        datos = request.data['codigo']
        self.credencial = Credencial(datos['crendencial'])
        try:
            codigos = ','.join(f"'{i}'" for i in datos['codigos'])
            sql = f"SELECT art_flegra FROM t_articulo WHERE art_codigo IN ({codigos})"
            s,res = CAQ.request(self.credencial,sql,(),'get',1)
            
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
            
            if self.validar_flete(res):
                pass
            sql = """
                SELECT a.ubi_codigo,b.AUX_NOMBRE,a.ubi_flete FROM mk_ubigeo AS a
                INNER JOIN t_auxiliar AS b ON a.ubi_CODIGO = b.AUX_EDI
                WHERE b.AUX_CLAVE = 'CL000481'
            """
        except Exception as e:
            data['error'] = f"Ocurrio un error :{str(e)}"
        return Response(data)
    def validar_flete(self,data)->bool:
        for value in data:
            if int(value[0])==1:
                return True
        return False