from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from apirest.credenciales import Credencial
from apirest.querys import CAQ
class UbicacionesCondicionados(GenericAPIView):
    credencial : object = None
    def post(self,request,*args,**kwargs):
        data = {}
        datos = self.request.data
        self.credencial = Credencial(datos['credencial'])
        try:
            sql =  """SELECT 
                        ubi_codigo,ubi_nombre 
                    FROM t_ubicacion 
                    WHERE modifica=1 ORDER BY ubi_codigo"""
            params = ()
            if datos['ubicacion']!='' and datos['credencial']['codigo'] in ['1','2']:
        
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
            
                raise Exception('Error al recuperar las ubicaciones')
            if result[0] is None:
                raise Exception('No se encontro ninguna ubicacion')
            data = [
                {
                    "id":index,
                    "label":value[1].strip(),
                    "value":value[0].strip()
                }
                for index,value in enumerate(result)
            ]
        except Exception as e:
            data['error'] = str(e)
        return Response(data)
