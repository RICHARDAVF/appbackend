
from rest_framework import generics
from rest_framework.response import Response
from apirest.crendeciales import Credencial
from apirest.querys import CAQ, Querys
from datetime import datetime
from apirest.views import QuerysDb

class ClienteCreateView(generics.GenericAPIView):
    def post(self,request,*args,**kwargs):
        datos = request.data[0]
      
        user = request.data[1]
        maa_codigo = 'CL'
        maa_nombre = 'CLIENTES'
        if(datos['tipo_doc']==4 and datos['tipo_persona']==1):
            maa_codigo = 'CE'
            maa_nombre = 'CLIENTE EXTRANJERO'
        data = {}
        
        sql = "SELECT*FROM t_auxiliar WHERE MAA_CODIGO=? AND AUX_DOCUM=?"
        result = Querys(kwargs).querys(sql,(maa_codigo,datos['doc']),'get',0)
       
        if result is not None:
            return Response({'error':'El usuario ya existe'})
        sql = """
            SELECT can_codigo,
                CASE
                    WHEN
                        (SELECT ofi_ventas FROM mk_oficina WHERE OFI_CODIGO = ?) = 0
                    THEN lis_codig1
                    ELSE lis_codig2
                END AS list_codigo
            FROM t_canal
            WHERE can_codigo = (SELECT can_codigo FROM t_categoria WHERE cat_codigo = ?)
        """
        result= Querys(kwargs).querys(sql,(datos['codigo_familia'],datos['codigo_client']),'get',0)
        
        if result is None:
            can_codigo,lis_codigo  = '',''
        else:
            can_codigo,lis_codigo = result
        sql = f"SELECT cta_clisol,cta_clidol FROM t_parrametro WHERE par_anyo={datetime.now().year}"
        result = Querys(kwargs).querys(sql,(),'get',0)
     
        aux_cuenta,aux_cuentad = result
        sql = """
                SELECT MAX(AUX_CODIGO) 
                FROM t_auxiliar
                WHERE MAA_CODIGO=?
                """
 
        result = Querys(kwargs).querys(sql,(maa_codigo,),'get',0)

        if result is None:
            result = ['0']
   
        try:
            params = (maa_codigo,str(int(result[0])+1).zfill(6),f"{maa_codigo}{str(int(result[0])+1).zfill(6)}",datos['nombre_c'],datos['nombre_rs'],user['codigo'],maa_nombre,datos['direccion'],
                        datos['departamento'],datos['provincia'],datos['distrito'],datos['tipo_persona'],datos['doc'],datos['celular'],datetime.now(),datos['ubigeo'],user['cod'],datos['tipo_doc'],
                        datos['email'],datos['red_social'],datetime.now().strftime('%Y-%m-%d'),datos['codigo_client'],datos['codigo_fuente'],datos['codigo_familia'],'02',can_codigo.strip(),lis_codigo.strip(),
                        aux_cuenta.strip(),aux_cuentad.strip(),datos['condicion'],datos['estado'])
        
            sql = f"""
                INSERT INTO t_auxiliar
                    (MAA_CODIGO,AUX_CODIGO,AUX_CLAVE,AUX_NOMBRE,AUX_RAZON,VEN_CODIGO,MAA_NOMBRE,AUX_DIRECC,
                    DEP_CODIGO,PRO_CODIGO,DIS_CODIGO,AUX_TIPOPE,AUX_DOCUM,AUX_TELEF,AUX_CREADO,AUX_EDI,USUARIO,
                    aux_tipdoc,AUX_EMAIL,aux_dircor,aux_fecing,cat_codigo,reg_codigo,ofi_codigo,PAG_CODIGO,
                    can_codigo,lis_codigo,aux_cuenta,aux_cuentd,aux_condic,aux_estado) VALUES({','.join('?' for i in params)})
                """
            result = Querys(kwargs).querys(sql,params,'post')
            data = result
            if 'error' in result:
                data['error'] = result['error']
        except Exception as e:
            print(str(e))
            data['error'] = f"Ocurrio un error : {str(e)}"
        return Response(data)
class FamiliaView(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        data = {}
        host = kwargs['host']
        bd = kwargs['db']
        user = kwargs['user']
        password = kwargs['password']
        data = {}
        try:
            sql = """
                SELECT OFI_CODIGO,OFI_NOMBRE FROM mk_oficina
                """
            conn = QuerysDb.conexion(host,bd,user,password)
            cursor = conn.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            conn.commit()
            conn.close()
            data = []
            for index,value in enumerate(result):
                d = {'id':index,'codigo':value[0].strip(),'nombre':value[1].strip()}
                data.append(d)
        except Exception as e:
            data['error'] = f'Ocurrio un error : {str(e)}'
        return Response(data)
class FuenteView(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        data = {}
        host = kwargs['host']
        bd = kwargs['db']
        user = kwargs['user']
        password = kwargs['password']
        data = {}
        try:
            sql = """
                SELECT REG_CODIGO,REG_NOMBRE FROM mk_region
                """
            conn = QuerysDb.conexion(host,bd,user,password)
            cursor = conn.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            conn.commit()
            conn.close()
            data = []
            for index,value in enumerate(result):
                d = {'id':index,'codigo':value[0].strip(),'nombre':value[1].strip()}
                data.append(d)
        except Exception as e:
            data['error'] = f'Ocurrio un error : {str(e)}'
        return Response(data)
class TypeClienteView(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        data = {}
        try:
            sql = """
                    SELECT
                        cat_codigo,
                        cat_nombre
                    FROM t_categoria
                    """
            result = Querys(kwargs).querys(sql,(),'get')
            data = []
            for index,value in enumerate(result):
                d = {'id':index,'codigo':value[0].strip(),'nombre':value[1].strip()}
                data.append(d)
        except Exception as e:
            data['error'] = f"ocurrio un error : {str(e)}"
        return Response(data) 
class ClientList(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        data = {}
        cadena = kwargs['cadena']
        try:

            params = ('C',)
  
            sql = f"""SELECT {
                "TOP 100 " if cadena=='x' else '' 
            }
                            aux_razon,aux_clave,aux_docum,'direccion'=ISNULL(aux_direcc,''),aux_telef,aux_email ,'codigo_vendedor'=ISNULL(b.ven_codigo,''),'nombre_vendedor'=ISNULL(b.VEN_NOMBRE,''),a.aux_desac,
                            'distrio'=ISNULL(dis_codigo,''),'provincia'=ISNULL(pro_codigo,''),'region'=ISNULL(dep_codigo,'')
                        FROM t_auxiliar AS  a LEFT JOIN t_vendedor AS b on a.VEN_CODIGO=b.VEN_CODIGO 
                        WHERE 
                                substring(aux_clave,1,1)=?
                                {
                                    f'''AND (
                                        aux_docum LIKE '%{cadena}%'
                                        OR aux_razon LIKE '%{cadena}%') ''' if cadena!='x' else ''
                                } 
                        ORDER BY  aux_razon ASC"""
            result = Querys(kwargs).querys(sql,params,'get',1)
            data = [
                {
                    'id':index+1,
                    'nombre':client[0].strip(),
                    'codigo':client[1].strip(),
                    'ruc':client[2].strip(),
                    'direccion':f"{client[3].strip()} {client[9].strip()} {client[10].strip()} {client[11].strip()}",
                    'telefono':client[4].strip(),
                    'correo':client[5].strip(),
                    'vendedor_codigo':client[6].strip(),
                    'vendedor_nombre':client[7].strip(),
                    'activo':int(client[8])==0
                    } for index,client in enumerate(result)]
           
        except Exception as e:
            print(str(e),'listado de clientes')
            data['error'] = 'Ocurrio un error al listar los clientes'
        return Response(data)
class ValidarCliente(generics.GenericAPIView):
    credencial : object = None
    def post(self,request,*args,**kwargs):

        data = {}
        datos = request.data
        self.credencial = Credencial(datos['credencial'])
        try:
            sql = "SELECT AUX_DOCUM FROM t_auxiliar WHERE AUX_DOCUM=? AND MAA_CODIGO='CT' "
            s,result = CAQ.request(self.credencial,sql,(datos['documento'],),'get',0)
        
            if not s:
                raise Exception('Error en la busqueda del cliente')
            if result is None:
                raise Exception('El cliente no esta en la base de datos,registrarlo por favor')
            data['success'] = True
        except Exception as e:
            data['error'] = str(e)
        return Response(data)
class RegisterSampleClient(generics.GenericAPIView):
    credencial : object = None
    fecha :datetime = datetime.now()
    def post(self,request,*args,**kwargs):
        data = {}
        datos = request.data
        user = datos['user']
        self.credencial = Credencial(datos['credencial'])
        try:
           
            maa_codigo='CT'
            sql = f"SELECT cta_clisol,cta_clidol FROM t_parrametro WHERE par_anyo={datetime.now().year}"
            s,result = CAQ.request(self.credencial,sql,(),'get',0)
            if not s:
                raise Exception('Error al obtener las cuentas para el cliente')
            if result is None:
                raise Exception('No hay cuentas para asignar al cliente')
            aux_cuenta,aux_cuentad = result
            sql = """
                SELECT MAX(AUX_CODIGO) 
                FROM t_auxiliar
                WHERE MAA_CODIGO=?
                """
            s,result = CAQ.request(self.credencial,sql,(maa_codigo,),'get',0)
   
            if not s:
                raise Exception('Error al obtener correlativo para el cliente')
            if result[0] is None:
                result = ['0']

            tipo_persona = 2 if (len(datos['documento'])==11 and datos['documento'][:2]=='20') else 1
            tipo_documento = 1 if len(datos['documento'])==11 else 2
            aux_codigo = str(int(result[0])+1).zfill(6)
            params = (maa_codigo,aux_codigo,f"{maa_codigo}{aux_codigo}",datos['razon_social'],datos['razon_social'],user['codigo'],datos['direccion'],
                      datos['departamento'],datos['provincia'],datos['distrito'],tipo_persona,datos['documento'],datos['telefono'],self.fecha.strftime('%Y-%m-%d'),
                      datos['ubigeo'],user['cod'],tipo_documento,datos['email'],self.fecha.strftime('%Y-%m-%d'),aux_cuenta,aux_cuentad)
            sql = f"""INSERT INTO t_auxiliar (maa_codigo,aux_codigo,aux_clave,aux_nombre,aux_razon,ven_codigo,aux_direcc,
                    dep_codigo,pro_codigo,dis_codigo,aux_tipope,aux_docum,aux_telef,aux_creado,aux_edi,usuario,aux_tipdoc,
                    aux_email,aux_fecing,aux_cuenta,aux_cuentd) VALUES({','.join('?' for i in params)})"""
            res = CAQ.request(self.credencial,sql,params,'post')
            print(res)
        except Exception as e:
            data['error'] = str(e)
        return Response(data)