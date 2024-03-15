from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from datetime import datetime
from numpy import array
from apirest.credenciales import Credencial
from apirest.querys import CAQ
class CuadreCajaView(GenericAPIView):
    credencial : object = None
    fecha : datetime = datetime.now()
    condicion_pago : str = None
    def post(self,request,*args,**kwargs):
        data = {}
        datos = request.data
        ubicacion = datos['ubicacion']
        self.credencial = Credencial(datos['credencial'])
        self.dates : dict = {
                    'ventas_efectivo':0,
                    'ventas_credito':0,
                    'ventas_nota_credito':0,
                    'total_tarjetas_ingresos':0,
        }
        try:
            sql = f"""SELECT pag_codigo FROM t_parrametro WHERE par_anyo='{self.fecha.year}' """
            s,result = CAQ.request(self.credencial,sql,(),'get',0)
            if not s:
                raise Exception('Error al recuper datos de parametros')
            if result is None:
                raise Exception('Error, no existe una condicion de pago para el año actual')
            self.condicion_pago  = result[0].strip()
            sql = "SELECT tar_codigo,tar_nombre FROM t_tarjetas"
            s,result = CAQ.request(self.credencial,sql,(),'get',1)
            if not s:
                raise Exception('Error al recuperar las tarjetas')
            
            self.process_tarjetas(result)
            sql = f"""SELECT 
                            tie_tarj01,tie_mon01,tie_tarj02,tie_mon02,tie_tarj03,
                            tie_mon03,fac_coddoc,ROU_TVENTA,tie_efesol,tie_efedol,
                            tie_vuesol,tie_monnc,pag_codigo,fac_serie,fac_docum,tie_monnc
                        FROM GUIC{self.fecha.year}
                        WHERE 
                            gui_motivo=1 
                            AND mov_fecha=? 
                            {
                                f" AND ubi_codigo= '{ubicacion}' " if  ubicacion!='' else ''
                            }
                            AND elimini=0 
                            AND doc_codigo='03'
                """
            params = (datos['fecha'],)
 
            s,result = CAQ.request(self.credencial,sql,params,'get',1)
            
            if not s:
                raise Exception('Error al recuperar los datos')
            if result is None:
                raise Exception('No existen registro para la fecha')
            self.process_data(result)
            self.process_documentos(result)
            sql = f"""SELECT 
                        gas_elecon,
                        gas_import 
                    FROM m_gastos 
                    WHERE 
                        gas_fecha=?
                        {
                            f"AND ubi_codigo={datos['ubicacion']} " if datos['ubicacion']!='' else ''
                        }
                        AND elimini=0
                    """
            s,result = CAQ.request(self.credencial,sql,(datos['fecha'],),'get',1)
            if not s:
                raise Exception('Error al recuperar los gatos')
            self.process_gastos(result)
            data =self.dates
        except Exception as e:
        
            data['error'] = str(e)
        return Response(data)
    def process_tarjetas(self,datos):
        try:
            tarjetas = {}
            for item in datos:
                tarjetas[item[0].strip()] = {'nombre':item[1].strip(),'monto':0}
            self.dates['tarjetas'] = tarjetas
        except Exception as e:
            raise Exception(str(e))
    def process_data(self,datos):
        try:
            for item in datos:
                if item[6].strip()!='07' and self.condicion_pago==item[12].strip():
                    self.dates['ventas_efectivo']+=float(item[8])+float(item[9])-float(item[10])
                if item[6].strip()!='07' and self.condicion_pago!=item[12].strip():
                    self.dates['ventas_credito']+=float(item[8])+float(item[9])-float(item[10])
                if item[6].strip()!='07':
                    self.dates['ventas_nota_credito']+=float(item[11])
                self.dates['total_tarjetas_ingresos']+=float(item[1])+float(item[3])+float(item[5])
                if item[0].strip()!='':
                    self.dates['tarjetas'][item[0].strip()]['monto']+=float(item[1]) 
                if item[2].strip()!='':
                    self.dates['tarjetas'][item[2].strip()]['monto']+=float(item[2])
                if item[4].strip()!='':
                    self.dates['tarjetas'][item[4].strip()]['monto']+=float(item[5])
            self.dates['total_ingreso'] = self.dates['ventas_efectivo']+self.dates['ventas_credito']+self.dates['ventas_nota_credito']+self.dates['total_tarjetas_ingresos']
        except Exception as e:
            raise Exception(str(e))
    def process_gastos(self,datos):
        gastos = {'devolucion_dinero':0,'gastos_administrativos':0,'gastos_proveedores':0,'depositos_bancarios':0,'gastos_caja_chica':0,'gastos_local':0,'gastos_letras':0}
        keys_ = list(gastos.keys())
        for item in datos:
            if int(item[0]) in [1,2,3,4,5,6,7]:
                gastos[keys_[int(item[0])]]+=float(item[1])
        self.dates['gastos'] = gastos
        self.dates['total_gastos'] = sum(list(gastos.values()))
        self.dates['total_tarjetas_egresos'] = self.dates['total_tarjetas_ingresos']
        self.dates['total_egreso'] = self.dates['total_gastos']+self.dates['total_tarjetas_egresos']
    def process_documentos(self,datos):
        documentos = {
            'factura':{
                'cantidad':0,
                'rango':'',
            },
            'boleta':{
                'cantidad':0,
                'rango':''
            },
            'nota_credito':{
                'cantidad':0,
                'rango':''
            },
            'factura_ticket':{
                'cantidad':0,
                'rango':''
            },
            'boleta_ticket':{
                'cantidad':0,
                'rango':''
            }
        }
        docs_ = {'01':'factura','03':'boleta','07':'nota_credito','11':'factura_ticket','12':'boleta_ticket'}
        def method_group(documentos,documento):
         
            docs = []
            for item in documentos:
                if item[6].strip()==documento:
                    docs.append(f"{documento}-{item[13].strip()}-{item[14]}")
            return sorted(docs)
        for item in datos:
            try:
                res = method_group(datos,item[6].strip())
                key_ = docs_[item[6].strip()]
                documentos[key_]['cantidad'] = len(res)
                documentos[key_]['rango'] = f"{res[0]} / {res[-1]}"
            except Exception as e:
    
                pass
        self.dates['documentos'] = documentos

class SaveCuadreCaja(GenericAPIView):

    def post(self,request,*args,**kwargs):
        data = {}
        datos = request.data
        self.fecha = datetime.now()
        user = datos['usuario']
        self.credencial = Credencial(datos['credencial'])
        self.numero : int = 0
        try:
            params = (user['cod'],self.fecha)
            sql = "INSERT INTO correcuadre (usuario,fechausu) VALUES(?,?)"
            s,_ = CAQ.request(self.credencial,sql,params,'post')
            if not s:
                raise Exception('Error al generar el correlativo')
            sql = "SELECT numero FROM correcuadre WHERE usuario=? AND fechausu=?"
            s,result = CAQ.request(self.credencial,sql,(user['cod'],self.fecha),'get',0)
            if not s:
                raise Exception('Error al recuperar el correlativo')
            if result is None:
                raise Exception('No existe correlativo para el usuario con la fecha actual')
            self.numero = int(result[0])
            saldo = datos['total_ingresos']-datos['total_egresos']
            documentos = datos['dates']['documentos']
            params = (self.numero,datos['fecha'],user['ubicacion'],datos['ventas_efectivo'],datos['ventas_nota_credito'],datos['sencillo_anterior'],
                      datos['otros'],datos['total_ingresos'],datos['devolucion_dinero'],datos['gastos_caja_chica'],datos['gastos_administrativos'],
                      datos['gastos_local'],datos['gastos_proveedores'],datos['gastos_letras'],datos['depositos_bancarios'],datos['sencillo_ma'],
                      datos['total_egresos'],saldo,datos['total'],datos['sobrante'],datos['faltante'],user['cod'],self.fecha,datos['total_tarjetas_ingresos'],
                      datos['total_tarjetas_egresos'],datos['total_efectivo'],datos['total_gastos'],documentos['factura']['cantidad'],
                      documentos['boleta']['cantidad'],documentos['nota_credito']['cantidad'],documentos['factura_ticket']['cantidad'],documentos['boleta_ticket']['cantidad'],
                      documentos['factura']['rango'],documentos['boleta']['rango'],documentos['nota_credito']['rango'],documentos['factura_ticket']['rango'],documentos['boleta_ticket']['rango']
                      )
            sql = f"""INSERT INTO m_cuadre (cua_codigo,cua_fecha,ubi_codigo,cua_efecti,cua_nc,cua_senant,cua_otros,cua_moning,cua_egre01,cua_egre02,
            cua_egre03,cua_egre04,cua_egre05,cua_egre06,cua_egre07,cua_senman,cua_monegr,cua_saldo,cua_total,cua_sobra,cua_falta,usuario,fechausu,cua_taring,
            cua_taregr,cua_totefe,cua_totgas,cua_numfac,cua_numbol,cua_numncr,cua_numtfa,cua_numtbo,
            cua_dhfact,cua_dhbole,cua_dhncre,cua_dhtfac,cua_dhtbol) VALUES({','.join('?' for i in params)})"""
            
            s,_ = CAQ.request(self.credencial,sql,params,'post')
            if not s:
                raise Exception('Error al guardar  los movimientos de caja')
            # for i,j in zip(result[0],params):
            #     print(i,type(i),j,type(j))
            data['success'] = 'El cuadre de caja se guardo exitosamente'
        except Exception as e:
            data['error'] = str(e)
        return Response(data)