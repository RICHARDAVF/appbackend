import requests
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from datetime import datetime
from apirest.credenciales import Credencial

from apirest.querys import CAQ
from apirest.view.apis.views import GenerateToken
from apirest.view.facturacion.factura import Factura
class EmisionDocumentos (GenericAPIView):
    fecha : datetime = datetime.now()
    credencial :object = None
    def post(self,request,*args,**kwargs):
        data = {}
        datos = request.data
        self.credencial = Credencial(datos['credencial'])
        s,desde,hasta = self.range_years(datos['desde'],datos['hasta'])
        try:
            resultados = []
            if  s:
                raise Exception('Error en el rango de fecha')
            for y in range(int(desde[:4]),int(hasta[:4])+1,1):
                sql = self.command_sql(y)
                
                s,res = CAQ.request(self.credencial,sql,(desde,hasta),'get',1)
              
                if not s:
                    raise Exception ('Error el sonsultar pro los documentos')
                if res is None:
                    continue
                else:
                    resultados+=res
                    
            data = [
                {
                    'id':index,
                    'serie':value[0].strip(),
                    'numero':value[1].strip(),
                    'cliente':value[2].strip(),
                    'total':float(value[3]),
                    'fecha':value[4].strftime('%Y-%m-%d'),
                    'numero_pedido':value[5].strip()
                } for index,value in enumerate(resultados)
            ]
        except Exception as e:
            data['error'] = str(e)
        return Response(data)
    def range_years(self,desde,hasta):
        desde_ =  '-'.join(str(i) for i in desde.split('/'))
        hasta_ =  '-'.join(str(i) for i in hasta.split('/'))
        return desde>hasta,desde_,hasta_
    def command_sql(self,year):
        sql = f"""
                SELECT 
                    a.fac_serie,
                    a.fac_docum,
                    b.aux_razon,
                    a.ROU_TVENTA,
                    a.MOV_FECHA,
                    a.MOV_COMPRO
                FROM GUIC{year} AS a 
                LEFT JOIN t_auxiliar AS b ON a.mov_codaux=b.aux_clave 
                WHERE 
                    a.MOV_FECHA BETWEEN ? AND ? 
                    AND a.doc_codigo='01' 
                    --AND a.elimini=0 
                    --AND a.gui_cdrfe=0 
                    AND a.doc_compro IN ('01','06','07','08','20') 
                    AND LEFT(a.fac_serie,1) IN ('B','F')
                ORDER BY a.mov_fecha DESC 
                    """
        return sql
class EnviarDocumento(GenericAPIView):
    credencial :object = None
    def post(self,request,*args,**kwagrs):
        data = {}
        datos = request.data
        self.credencial = Credencial(datos['credencial'])
        try:
            instance = Factura(self.credencial,datos['serie'],datos['numero'])
            instance.generate_json()
            instance.enviar()
            data['msg'] = 'El documento fue enviado correctamente.'
        except Exception as e:
            data['error'] = str(e)
        return Response(data)
class VerificarEstado(GenericAPIView):
    credencial : object = None
    def post(self,request,*args,**kwagrs):
        data = {}
        datos = request.data
        self.credencial = Credencial(datos['credencial'])
        try:
            sql = f"""
                SELECT TOP 1 par_url,par_acekey,par_seckey FROM fe_parametro
                """
            s,result = CAQ.request(self.credencial,sql,() ,'get',0)
       
            
            if not s:
                raise Exception('Error al recuperar los parametros de facturacion/boleta')
            if result is None:
                raise Exception('No tiene credenciales para generar documentos electronicos')
            url = result[0].strip()
            access_key = result[1].strip()
            secret_key = result[2].strip()
            token,timestap = GenerateToken(access_key,secret_key).encryptdates()
            part_url = 'boleta' if datos['serie'][0]=='B' else ('factura' if datos['serie'][0]=='F' else 'error')
            if part_url =='error':
                raise Exception('Serie no valida')
            url = f"{url}{part_url}/{datos['serie']}{datos['numero']}/constancia"

            res = requests.get(url=url,headers={
                'Authorization':f"Fo {access_key}:{token}:{timestap}",
                'Content-Type':'application/json'
            })
            values = res.json()
            print(values)
            if ('codigo' in values) and (values['codigo']=='0'):
                data['msg'] = values['descripcion']
            elif ('codigo' in values) and (values['codigo']!='0'):
                data['msg'] = values['descripcion']

                self.update_documento(int(values['fechaEmision'][:4]),datos['serie'],datos['numero'])
            else:
                data['error'] = values['message']
        except Exception as e:
            data['error'] = str(e)
        return Response(data)
    def update_documento(self,year,serie,numero):
        try:
            sql = f"""UPDATE guic{year} SET gui_recefe=1,gui_cdrfe=1 
            WHERE 
                fac_serie=?
                AND fac_docum=?"""
            s,_ = CAQ.request(self.credencial,sql,(serie,numero),'post')
            print(s,_)
            if not s:
                raise Exception('Error al actualizar estado de recepcion')
        except Exception as e:
            raise Exception(str(e))