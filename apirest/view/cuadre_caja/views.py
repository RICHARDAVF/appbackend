from rest_framework import generics
from rest_framework.response import Response

from apirest.views import QuerysDb
class CuadreCajaView(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        data = {}
        host = kwargs['host']
        db = kwargs['db']
        user = kwargs['user']
        password = kwargs['password']
        try:
            conn = QuerysDb.conexion(host,db,user,password)
            sql = f"""
                    SELECT 
                        tar_codigo,
                        tar_nombre,
                        'cua_monto'=0 
                    FROM t_tarjetas 
                    ORDER BY tar_nombre
                    """
            cursor = conn.cursor()
            cursor.execute(sql)
            datos = cursor.fetchall()
            conn.commit()
            conn.close()
            data = []
            for index, item in enumerate(data):
                d = {'id':index}
        except Exception as e:
            data['error'] = str(e)

        return Response(data)