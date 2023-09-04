from rest_framework import generics
from apirest.views import QuerysDb
from rest_framework.response import Response
from datetime import datetime
class InventarioView(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        host = kwargs['host']
        db = kwargs['db']
        user = kwargs['user']
        password = kwargs['password']
        conn = QuerysDb.conexion(host,db,user,password)
        datos={}
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
        datos['almacen'] = alms
        conn = QuerysDb.conexion(host,db,user,password)
        sql = """
            SELECT ubi_codigo,ubi_nombre FROM t_ubicacion ORDER BY ubi_codigo
            """
        ubicacion = self.querys(conn,sql,(),'get')
        ubis = []
        for index,value in enumerate(ubicacion):
            d = {'id':index,'value':value[0].strip(),'label':value[1].strip()}
            ubis.append(d)
        datos['ubicacion']=ubis
        sql = """
            SELECT ope_codigo,OPE_NOMBRE FROM t_operacion ORDER BY OPE_NOMBRE
            """
        conn = QuerysDb.conexion(host,db,user,password)
        operacion = self.querys(conn,sql,(),'get')
        opes = []
        for index,value in enumerate(operacion):
            d = {'id':index,'value':value[0].strip(),'label':value[1].strip()}
            opes.append(d)
        datos['operacion']=opes
        return Response({'message':datos})
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
        host = kwargs['host']
        db = kwargs['db']
        user = kwargs['user']
        password = kwargs['password']
        codigo = kwargs['codigo']
        serie = kwargs['serie']
        conn = QuerysDb.conexion(host,db,user,password)
        cursor = conn.cursor()
        sql = "SELECT usu_doctom FROM t_usuario WHERE USU_CODIGO=?"
        cursor.execute(sql,(codigo,))
        data = cursor.fetchone()
       
        respuesta = {}
        # if len(data[0].strip())==0:
        #     respuesta['error']='El usuario no tiene asignado un correlativo'
        #     conn.commit()
        #     conn.close()
        #     return Response({'message':respuesta})
        # sql = "SELECT ART_CODIGO FROM t_articulo WHERE ART_CODIGO=?"
        # cursor.execute(sql,(serie,))
        # data = cursor.fetchone()
        # if data is None:
        #     respuesta['error'] = "El codigo no existe"
        #     conn.commit()
        #     conn.close()
        #     return Response({'message':respuesta})
        return Response({'message':'SUCCESS'})
class QRscanView(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        "Procesamiento de losdatos obtenidos con el lector QR"
        "Procesamiento de losa datp obtenidos al scanera el lector de barras"
        return Response({"message"})
class ProcessLote:
    def __init__(self,data):
        self.data = data
    def proces(self):
        return self.data

    
