from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from apirest.querys import Querys
from datetime import datetime
class RegistroIncidecias(GenericAPIView):
    def get(self,request,*args,**kwrgs):
        data = {}
        try:
            sql = """
                    SELECT 
                        a.tra_codigo,
                        c.TRA_NOMBRE,
                        b.inc_tipo,
                        b.inc_nombre,
                        a.inc_observ,
                        a.fechausu 
                    FROM m_trabajador_incidencia AS a
                    INNER JOIN t_incidencia AS b ON a.inc_codigo=b.inc_codigo
                    INNER JOIN TRABAJADOR AS c on a.tra_codigo=c.TRA_CODIGO
                    ORDER BY a.FECHAUSU DESC
                """
            result = Querys(kwrgs).querys(sql,(),'get',1)
            data = [
                {
                    'id':index,
                    'tra_codigo':value[0].strip(),
                    'tra_nombre':value[1].strip(),
                    'inc_tipo':value[2],
                    'inc_nombre':value[3].strip(),
                    'obs':value[4].strip(),
                    'fecha':value[5].strftime('%Y-%m-%d %H:%M:%S')
                } for index,value in enumerate(result)
            ]
         
        except Exception as e:
            print(str(e),'listado de incidencias')
            data['error'] = 'ocurrio un error al recuperar las incidencias'
        return Response(data)
    def post(self,request,*args,**kwargs):
        data = {}
        try:
            datos = request.data
            if datos['inc_codigo']=='' or datos['tra_codigo']=='':
                data['error'] = 'Complete el formulario por favor'
                return Response(data)
            
            inc_codigo = datos['inc_codigo'].split('-')[0]
            fecha = datetime.now()
            params = (datos['tra_codigo'],inc_codigo,fecha.strftime('%Y-%m-%d'),datos['obs'],datos['usuario'],fecha.strftime('%Y-%m-%d %H:%M:%S'))
            sql = f"""
                    INSERT INTO m_trabajador_incidencia(tra_codigo,inc_codigo,inc_fecha,inc_observ,USUARIO,FECHAUSU) VALUES({','.join('?' for i in params)})
            """
            data = Querys(kwargs).querys(sql,params,'post')
            if 'error' in data:
                data['error']= data['error']
                return Response(data)
        except Exception as e:
            print(str(e),'Registro de incidencia')
            data['error'] = 'Ocurrio un error al registrar la incidencia'
        return Response(data)