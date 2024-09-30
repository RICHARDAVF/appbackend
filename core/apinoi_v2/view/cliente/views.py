from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from apirest.credenciales import Credencial,CAQ
from apirest.view.generate_id import gen_id


class ListadoClientes(GenericAPIView):
    def post(self,request,*args,**kwargs):
        data = {}
        datos = request.data
        try:
            self.credencial = Credencial(datos['credencial'])
            cadena = datos['cadena']
            params = ('C',)
            sql = f"""SELECT {
                "TOP 100 " if cadena=='x' else '' 
            }
                            aux_razon,
                            aux_clave,
                            aux_docum,
                            'direccion'=ISNULL(aux_direcc,''),
                            aux_telef,
                            aux_email ,
                            'codigo_vendedor'=ISNULL(b.ven_codigo,''),
                            'nombre_vendedor'=ISNULL(b.VEN_NOMBRE,''),
                            a.aux_desac,
                            'distrio'=ISNULL(dis_codigo,''),
                            'provincia'=ISNULL(pro_codigo,''),
                            'region'=ISNULL(dep_codigo,''),
                            a.lis_codigo,
                            a.ofi_codigo
                        FROM t_auxiliar AS  a LEFT JOIN t_vendedor AS b on a.VEN_CODIGO=b.VEN_CODIGO 
                        WHERE 
                                substring(aux_clave,1,1)=?
                                {
                                    f'''AND (
                                        aux_docum LIKE '%{cadena}%'
                                        OR aux_razon LIKE '%{cadena}%') ''' if cadena!='x' else ''
                                } 
                        ORDER BY  aux_razon ASC"""
            s,res = CAQ.request(self.credencial,sql,params,'get',1)
            if not s:
                raise ValueError(res['error'])
            data = [
                {
                    'id':gen_id(),
                    'nombre':client[0].strip(),
                    'codigo':client[1].strip(),
                    'ruc':client[2].strip(),
                    'direccion':f"{client[3].strip()} {client[9].strip()} {client[10].strip()} {client[11].strip()}",
                    'telefono':client[4].strip(),
                    'correo':client[5].strip(),
                    'vendedor_codigo':client[6].strip(),
                    'vendedor_nombre':client[7].strip(),
                    'activo':int(client[8])==0,
                    'lista_precio':client[12].strip(),
                    "familia":client[13].strip()
                    } for client in res]
           
        except Exception as e:
            print(str(e),'listado de clientes')
            data['error'] = 'Ocurrio un error al listar los clientes'
        return Response(data)