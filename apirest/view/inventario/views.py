from rest_framework import generics
from apirest.querys import Querys
from apirest.views import QuerysDb
from rest_framework.response import Response
from datetime import datetime
class InventarioView(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        host = kwargs['host']
        db = kwargs['db']
        user = kwargs['user']
        password = kwargs['password']
        try:
            conn = QuerysDb.conexion(host,db,user,password)
            data={}
            sql = """
                SELECT 
                    a.ALM_CODIGO,
                    a.ALM_NOMBRE
                FROM t_almacen AS a
                INNER JOIN t_parrametro AS b
                ON a.ALM_CODIGO=b.alm_codigo
                WHERE
                    par_anyo=YEAR(GETDATE()) 
                ORDER BY a.alm_nombre
                """
            almacen = self.querys(conn,sql,(),'get')
            alms = []
            for index,value in enumerate(almacen):
                d = {'id':index,'value':value[0].strip(),'label':value[1].strip()}
                alms.append(d)
            data['almacenes'] = alms
            conn = QuerysDb.conexion(host,db,user,password)
            sql = """
                SELECT ubi_codigo,ubi_nombre FROM t_ubicacion ORDER BY ubi_codigo
                """
            ubicacion = self.querys(conn,sql,(),'get')
            ubis = []
            for index,value in enumerate(ubicacion):
                d = {'id':index,'value':value[0].strip(),'label':value[1].strip()}
                ubis.append(d)
            data['ubicaciones']=ubis
            sql = """
                SELECT ope_codigo,OPE_NOMBRE FROM t_operacion ORDER BY OPE_NOMBRE
                """
            conn = QuerysDb.conexion(host,db,user,password)
            operacion = self.querys(conn,sql,(),'get')
            opes = []
            for index,value in enumerate(operacion):
                d = {'id':index,'value':value[0].strip(),'label':value[1].strip()}
                opes.append(d)
            data['operaciones']=opes
        except Exception as e:
            data['error'] = f"Ocurrio un error : {str(e)}"
        return Response(data)
    def post(self,request,*args,**kwargs):
        host = kwargs['host']
        db = kwargs['db']
        user = kwargs['user']
        password = kwargs['password']
        data = request.data
        respuesta={}
        sql = f"""
                INSERT INTO toma{datetime.now().year}(ALM_CODIGO,MOM_MES,MOM_FECHA,ART_CODIGO,OPE_CODIGO,UBI_COD,MOM_CANT,MOM_GLOAS) 
                VALUES(?,?,?,?,?,?,?)
            """
        params = (data['almacen'],str(datetime.now().month).zfill(2),datetime.now(),data['codigo'],data['operacion'],data['ubicacion'],data['cantidad'],data['observacion'])
        try:
            conn = QuerysDb.conexion(host,db,user,password)
            cursor = conn.cursor()
            cursor.execute(sql,params)
            conn.commit()
            conn.close()
            respuesta['success'] = "Se guardo con exito"
        except Exception as e:
            respuesta['error'] = str(e)
       
        return Response({'message':respuesta})
    def querys(self,conn,sql,params,request):
        cursor = conn.cursor()
        cursor.execute(sql,params)
        if request == "get":
            datos= cursor.fetchall()
        elif request == 'post':
            datos = "SUCCESS"
        conn.commit()
        conn.close()
        return datos

class ValidateView(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        data = {}
        host = kwargs['host']
        db = kwargs['db']
        user = kwargs['user']
        password = kwargs['password']
        codigo = kwargs['codigo']
        conn = QuerysDb.conexion(host,db,user,password)
        cursor = conn.cursor()
        sql = "SELECT usu_doctom FROM t_usuario WHERE USU_CODIGO=?"
        cursor.execute(sql,(codigo,))
        data = cursor.fetchone()
        if len(data[0].strip())==0:
            data['error']='El usuario no tiene asignado un correlativo'
            conn.commit()
            conn.close()
            return Response(data)
        return Response({'message':'SUCCESS'})
    def post(self,request,*args,**kwargs):
        data = {}
        datos = request.data
        try:
            sql = "SELECT  'longitud' = cre_long1+cre_long2+cre_long3+cre_long4+cre_long5+cre_long7+cre_long8 FROM t_creacodigo WHERE alm_codigo=?"
            result = Querys(kwargs).querys(sql,(datos['almacen'],),'get',0)

            if result is None:
                data['error'] = "El codigo no existe en la base de datos"
                return Response(data)
            longitud = result[0]
            codigo = datos['codigo'][:int(longitud)]

            color = datos['codigo'][int(longitud):int(longitud)+2]
         
            sql = "SELECT art_codigo FROM t_articulo WHERE art_codigo = ?"
            result = Querys(kwargs).querys(sql,(codigo,),'get',0)
            if result is None:
                data['error'] = "No existe articulo con este codigo"
                return Response(data)
            if len(datos['codigo'])>11:
                sql = "SELECT col_codigo FROM t_colores WHERE col_codigo = ?"
                result = Querys(kwargs).querys(sql,(color,),'get',0)
                if result is None:
                    data['error'] = "No existe el color"
        except Exception as e:
            data['error'] = f'Ocurrio un error : {str(e)}'
        return Response(data)
class QRscanView(generics.GenericAPIView):
    def post(self,request,*args,**kwargs):
        data = {}
        datos = request.data

        try:
            pass
        except Exception as e:
            data['error'] = f"Ocurrio un error :{str(e)}"
        return Response({"message"})
class ProcessLote:
    def __init__(self,data):
        self.data = data
    def proces(self):
        return self.data

    
