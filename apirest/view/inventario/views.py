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
        try:
            host = kwargs['host']
            db = kwargs['db']
            user = kwargs['user']
            password = kwargs['password']
            codigo = kwargs['codigo']
            conn = QuerysDb.conexion(host,db,user,password)
            cursor = conn.cursor()
            sql = "SELECT usu_doctom FROM t_usuario WHERE USU_CODIGO=?"
            cursor.execute(sql,(codigo,))
            result = cursor.fetchone()
            conn.commit()
            conn.close()
            if len(result[0].strip())==0:
                data['error']='El usuario no tiene asignado un correlativo' 
        except Exception as e:
            data['error'] = f"ocurrio un error: {str(e)}"
        return Response(data)
    def save(self,codigo,talla,color):
        date = self.request.data
        data = {}
        try:

            mom_d_int = date['mom_d_int']
            user = date['user']['toma_inventario'].split('-')
            if mom_d_int == '':
                sql = "SELECT doc_docum from t_documento WHERE DOC_CODIGO=? AND DOC_SERIE=? "
                result = Querys(self.kwargs).querys(sql,(user[0],user[1]),'get',0)
                numero_documento = result[0].strip()
                mom_d_int = f"{user[1]}-{str(int(numero_documento)).zfill(7)}"
            else :
                mom_d_int = date['mom_d_int']
            params = (date['almacen'],str(datetime.now().month).zfill(2),datetime.now().strftime('%Y-%m-%d'),
                    codigo,date['operacion'],date['ubicacion'],date['cantidad'],date['observacion'],
                    color,talla,date['user']['cod'],user[0],'E',datetime.now().strftime('%Y-%m-%d'),f"{mom_d_int}")
            sql = f"""
                    INSERT INTO toma{datetime.now().year} (ALM_CODIGO,MOM_MES,MOM_FECHA,
                    ART_CODIGO,OPE_CODIGO,UBI_COD1,MOM_CANT,mom_glosa,col_codigo,
                    tal_codigo,usuario,doc_cod1,mom_tipmov,fechausu, mom_d_int) 
                    VALUES({','.join('?' for i in params)})
                """
            data = Querys(self.kwargs).querys(sql,params,'post',1)
            if 'success' in data and date['mom_d_int']=='':
                sql = "UPDATE  t_documento SET doc_docum=? WHERE DOC_CODIGO=? AND DOC_SERIE=?"
                params = (str(int(numero_documento)+1).zfill(7),user[0],user[1])
                data['success'] = Querys(self.kwargs).querys(sql,params,'post',1)['success']
                data['mom_d_int'] = mom_d_int
            else:
                data['mom_d_int'] = mom_d_int
                data['success'] = "Se guardo con exito"
            data['dates'] = self.articulos(mom_d_int)
           
        except Exception as e:
            data['error'] = f"Ocurrio un error: {str(e)}"
        return data
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
            talla_color = datos['codigo'][int(longitud):]
            color = ''
            talla = ''
            sql = "SELECT art_codigo FROM t_articulo WHERE art_codigo = ? OR art_provee=?"
            result1 = Querys(kwargs).querys(sql,(codigo,codigo),'get',0)
            if result1 is None:
                data['error'] = "No existe articulo con este codigo"
                return Response(data)
            if len(datos['codigo'])>longitud:
                sql = "SELECT col_codigo FROM t_colores WHERE col_codigo = ?"
                result = Querys(kwargs).querys(sql,(talla_color if len(talla_color)<2 else talla_color[:2],),'get',0)
          
                if result is not None:
                    color = result[0].strip()
                    talla = talla_color[len(color):]
                else:
                    talla = talla_color
            data = self.save(result1[0].strip(),talla,color)
        except Exception as e:
            data['error'] = f'Ocurrio un error : {str(e)}'
        return Response(data)
    def articulos(self,mom_d_int):
        data = {}
        try:
            sql = f"SELECT a.ART_CODIGO,ISNULL(b.ART_NOMBRE,''),a.MOM_CANT,a.tal_codigo,a.IDENTI FROM toma{datetime.now().year} AS a LEFT JOIN t_articulo AS b ON a.ART_CODIGO=b.ART_CODIGO WHERE MOM_D_INT=?"
            result = Querys(self.kwargs).querys(sql,(mom_d_int,),'get',1)
            data = [
                {
                    'id':index,
                    'codigo':item[0].strip(),
                    'nombre':item[1].strip(),
                    'cantidad':item[2],
                    'talla':item[3].strip(),
                    'identi':item[4],
                 
                 }
                  for index,item in enumerate(result)
            ]
        except Exception as e:
            data['error'] = f'Ocurrio un error :{str(e)} '
        return data


class DeleteInventario(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        data = {}
        try:
            sql = f"DELETE FROM toma{datetime.now().year} WHERE IDENTI=?"
            res = Querys(kwargs).querys(sql,(kwargs['identi'],),'post',1)
            if 'success' in res:
                data['success'] = "Se elimino el articulo  del inventario"
        except Exception as e:
            data['error'] = f"Ocurrio un error : {str(e)}"
        data['dates'] = self.articulos(kwargs['mom_d_int'])
        return Response(data)
    def articulos(self,mom_d_int):
        data = {}
        try:
            sql = f"SELECT a.ART_CODIGO,ISNULL(b.ART_NOMBRE,''),a.MOM_CANT,a.tal_codigo,a.IDENTI FROM toma{datetime.now().year} AS a LEFT JOIN t_articulo AS b ON a.ART_CODIGO=b.ART_CODIGO WHERE MOM_D_INT=?"
            result = Querys(self.kwargs).querys(sql,(mom_d_int,),'get',1)
            data = [
                {
                    'id':index,
                    'codigo':item[0].strip(),
                    'nombre':item[1].strip(),
                    'cantidad':item[2],
                    'talla':item[3].strip(),
                    'identi':item[4],
                 
                 }
                  for index,item in enumerate(result)
            ]
          
        except Exception as e:
            data['error'] = f'Ocurrio un error :{str(e)} '
        return data