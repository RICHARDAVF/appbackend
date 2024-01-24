from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from datetime import datetime
from apirest.crendeciales import Credencial
from apirest.querys import CAQ

class NotaPedido(GenericAPIView):
    anio = datetime.now().year
    credencial = None
    def post(self,request,*args,**kwargs):
        data = {}
        self.credencial = Credencial(request.data['credencial'])
        try:
            data['almacen'] = self.almacen()
            data['ubicacion'] = self.ubicacion()
            data['lista_precios'] = self.lista_precios()
           
        except:
            data['error'] = f"Ocurrio un error recuperar datos para la nota de pedido"
        return Response(data)
    def almacen(self):
        data = {}
       
        sql = """SELECT ALM_CODIGO,ALM_NOMBRE FROM t_almacen WHERE alm_grupo in(1,2) AND alm_nomost=0 ORDER BY ALM_CODIGO"""
        s,result = CAQ.request(self.credencial,sql,(),'get',1)
        if not s:
            data['error'] = 'Ocurririo un error al recuperar los almacenes'
            return Response(data)
        
        data = [
            {
                "id":index,
                'label':value[1].strip(),
                'value':value[0].strip()
            }
            for index,value in enumerate(result)
        ]
        return data
    def ubicacion(self):
        data = {}
        datos = self.request.data
       
        sql =  """SELECT 
                    ubi_codigo,ubi_nombre 
                FROM t_ubicacion 
                WHERE modifica=1 ORDER BY ubi_codigo"""
        params = ()
        
        if datos['ubicacion']!='':
            sql = """
                    SELECT
                        ubi_codigo,ubi_nombre 
                    FROM t_ubicacion 
                    WHERE  
                        ubi_codigo=? 
                        OR ubi_mosiem=1 
                    ORDER BY ubi_codigo"""
            params = (datos['ubicacion'],)
        s,result = CAQ.request(self.credencial,sql,params,'get',1)
        
        if not s:
            data['error'] = 'Ocurrio un error al recuperar las ubicaciones'
            return Response(data)
        data = [
            {
                "id":index,
                "label":value[1].strip(),
                "value":value[0].strip()
            }
            for index,value in enumerate(result)
        ]
        return data
    def lista_precios(self):
        data = {}
       
        sql = "SELECT lis_codigo,lis_nombre FROM t_tipolista ORDER BY lis_codigo"
        s,result = CAQ.request(self.credencial,sql,(),'get',1)
        if not s:
            data['error'] = 'Ocurrio un error al intentar recuperar los precios'
            return Response(data)
        data = [
            {
                "id":index,
                'value':value[0].strip(),
                'label':value[1].strip()
            }
            for index,value in enumerate(result)
        ]
        return data