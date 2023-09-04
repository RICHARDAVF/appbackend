from rest_framework import generics
from rest_framework.response import Response
from apirest.views import QuerysDb
class TrasladoView(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        host = kwargs['host']
        db = kwargs['db']
        user = kwargs['user']
        password = kwargs['password']
        data = {}
        try:
            conn = QuerysDb.conexion(host,db,user,password)
            cursor = conn.cursor()
            sql = f"""
                    SELECT
                        OPE_CODIGO,
                        OPE_NOMBRE 
                    FROM 
                        t_operacion 
                    WHERE 
                        ope_activo=0
                    """
            cursor.execute(sql)
            datos = cursor.fetchall()
            conn.commit()
            conn.close()
            data = []
            for index,item in enumerate(datos):
                d = {'id':index,'value':item[0],'label':item[1].strip()}
                data.append(d)
        except Exception as e:
            data['error'] = str(e)
        return Response(data)

    def post(self,request,*args,**kwargs):
        data = {}
        if request.data['action'] == 1:
            credenciales = request.data['cred']
            conn = QuerysDb.conexion(credenciales['bdhost'],credenciales['bdname'],credenciales['bduser'],credenciales['bdpassword'])
            cursor = conn.cursor()
            sql = f"""
                
                    """
            cursor.execute(sql)
            datos = cursor.fetchall()

        return Response(data)