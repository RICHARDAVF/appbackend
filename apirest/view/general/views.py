from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from apirest.querys import Querys
class Almacenes(GenericAPIView):
    def get(self,request,*args,**kwargs):
        data = {}
        try:
            sql = "SELECT ALM_CODIGO,ALM_NOMBRE FROM t_almacen WHERE alm_grupo in(1,2) AND alm_nomost=0 ORDER BY ALM_CODIGO"
            result = Querys(kwargs).querys(sql,(),'get',1)
            data['almacenes'] = [{'label':value[1],'value':value[0]} for value in result]
        except:
            data['error'] = 'No se pudo cargar los alamacenes'
        return Response(data)
class Operaciones(GenericAPIView):
    def get(self,request,*args,**kwargs):
        data = {}
        try:
            sql = """
                    SELECT
                        OPE_CODIGO,
                        OPE_NOMBRE 
                    FROM 
                        t_operacion 
                    WHERE 
                        ope_activo=0
                    """
            result = Querys(kwargs).querys(sql,(),'get',1)
            
            data['operaciones'] = [{'value':value[0].strip(),'label':value[1].strip()} for value in result]
           
        except Exception as e:
          
            data['error'] = f"No se pudo cargar las operaciones"
        return Response(data)
class Proveedores(GenericAPIView):
    def get(self,request,*args,**kwargs):
        data = {}
        try:
            sql = """SELECT 
                    aux_razon,aux_clave FROM t_auxiliar 
                WHERE 
                    SUBSTRING(aux_clave,1,2) = 'PP'
                    AND  aux_desac=0
                    AND AUX_RAZON<>''
                ORDER BY AUX_RAZON"""
            result = Querys(kwargs).querys(sql,(),'get',1)
            data['proveedores'] = [{'value':value[1].strip(),'label':value[0].strip()} for value in result]
        except Exception as e:
            data['error'] = 'No se pudo cargar los proveedores'
        return Response(data)
class Articulos(GenericAPIView):
    def get(self,request,*args,**kwargs):
        data = {}
        try:
            sql = "SELECT art_codigo,art_nombre FROM t_articulo WHERE ALM_CODIGO=?"
            result = Querys(kwargs).querys(sql,(kwargs['alm'],),'get',1)
            data['articulos'] = [{'id':index,'codigo':value[0].strip(),'nombre':value[1].strip()} for index,value in enumerate(result)]
        except Exception as e:
            data['error'] = 'No se pudo cargar los articulos'
        return Response(data)
class Trabajador(GenericAPIView):
    def get(self,request,*args,**kwargs):
        data = {}
        try:
            if kwargs['codigo'] =='':
                data['error'] = 'Ingrese un codigo valido'
                return Response(data)
            sql = """
            SELECT 
                TRA_CODIGO,TRA_APATER,TRA_AMATER,TRA_NOMBRE 
            FROM TRABAJADOR
            WHERE TRA_CODIGO=?
            """
            result = Querys(kwargs).querys(sql,(kwargs['codigo'],),'get',0)
            if result is None:
                data['error'] = "El trabajador no esta registrado"
                return Response(data)
            data['trabajador'] = {
                'codigo':result[0].strip(),
                'nombre':f"{result[1].strip()} {result[2].strip()} {result[3].strip()}"
                }
        except Exception as e:
            data["error"] = 'Ocurrio un error al buscar el trabajador'
        return Response(data)
class Ubicaciones(GenericAPIView):
    def get(self,request,*args,**kwargs):
        data = {}
        try:
            sql = "SELECT ubi_codigo,ubi_nombre FROM t_ubicacion"
            result = Querys(kwargs).querys(sql,(),'get',1)
            data['ubicaciones'] = [{'value':value[0].strip(),'label':value[1].strip()} for value in result]
        except Exception as e:
            data['error'] = "No se pudo cargar las ubicaciones"
        return Response(data)
class Incidencia(GenericAPIView):
    def get(self,request,*args,**kwargs):
        data = {}
        try:
            sql = """SELECT
                        inc_codigo,inc_nombre,inc_tipo
                    FROM t_incidencia

            """
            result = Querys(kwargs).querys(sql,(),'get',1)
            data = [
                {
                    'id':index,
                    'codigo':f"{value[0].strip()}-{value[2]}",
                    'nombre':value[1].strip()
                } for index,value in enumerate(result)
            ]
        except Exception as e:
            data['error'] = 'Ocurrioun error al recuperar las incidencias'
        return Response(data)
