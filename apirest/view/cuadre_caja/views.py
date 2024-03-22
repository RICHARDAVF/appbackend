from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from datetime import datetime
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
        if ubicacion=='':
            raise Exception('El usuario no tiene una ubicacion.')
        self.credencial = Credencial(datos['credencial'])
        self.dates : dict = {
                    'ventas_efectivo':0,
                    'ventas_credito':0,
                    'ventas_nota_credito':0,
                    'total_tarjetas_ingresos':0,
                    'total_ventas':0,
                    'total_devoluciones':0,
                    'total_prendas':0,
                    'total_prendas_devueltas':0
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
                             AND ubi_codigo= ?
                            AND elimini=0 
                            AND doc_codigo='03'
                """
            params = (datos['fecha'],datos['ubicacion'])
    
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
                        
                        AND ubi_codigo=?

                        AND elimini=0
                    """
            s,result = CAQ.request(self.credencial,sql,(datos['fecha'],datos['ubicacion']),'get',1)
            if not s:
                raise Exception('Error al recuperar los gatos')
            self.process_gastos(result)
            sql = f"""SELECT
                        'total_prendas'=SUM(CASE WHEN b.fac_coddoc<>'07' THEN a.mom_cant ELSE 0 END),
                        'total_prendas_devueltas'=SUM(CASE WHEN b.fac_coddoc='07' THEN a.mom_cant ELSE 0 END)
                        FROM GUID{self.fecha.year} AS a 

                        INNER JOIN GUIC{self.fecha.year} AS b ON a.mov_compro=b.MOV_COMPRO
                        WHERE 
                            b.mov_fecha=?
                            AND b.ELIMINI=0
                            AND b.ubi_codigo=?
                        """
            s,result = CAQ.request(self.credencial,sql,(datos['fecha'],datos['ubicacion']),'get',0)
 
            if result[0] is None:
                raise Exception('No hay articulos relacionados con las ventas de la tienda')
            self.dates['total_articulos'] = float(result[0])
            self.dates['total_articulos_devueltos'] = float(result[1])
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
                    self.dates['ventas_efectivo']+=round(float(item[8])+float(item[9])-float(item[10]),2)
                if item[6].strip()!='07' and self.condicion_pago!=item[12].strip():
                    self.dates['ventas_credito']+=round(float(item[8])+float(item[9])-float(item[10]),2)
                if item[6].strip()!='07':
                    self.dates['ventas_nota_credito']+=float(item[11])
                    self.dates['total_ventas']+= float(item[7])
                
                if item[6].strip()=='07':
                    self.dates['total_devoluciones']+=float(item[7]) 
                if item[0].strip()!='':
                    self.dates['tarjetas'][item[0].strip()]['monto']+=float(item[1])
                    self.dates['total_tarjetas_ingresos']+=float(item[1]) 
                if item[2].strip()!='':
                    self.dates['tarjetas'][item[2].strip()]['monto']+=float(item[3])
                    self.dates['total_tarjetas_ingresos']+=float(item[3]) 
                if item[4].strip()!='':
                    self.dates['tarjetas'][item[4].strip()]['monto']+=float(item[5])
                    self.dates['total_tarjetas_ingresos']+=float(item[5]) 

            
            self.dates['total_venta_dia'] = self.dates['total_ventas']-self.dates['total_devoluciones']
            self.dates['total_ingreso'] = self.dates['ventas_efectivo']
        except Exception as e:
            raise Exception(str(e))
    def process_gastos(self,datos):
        gastos = {'devolucion_dinero':0,'gastos_caja_chica':0,'gastos_administrativos':0,'gastos_local':0,'gastos_proveedores':0,'gastos_letras':0,'depositos_bancarios':0}
        keys_ = list(gastos.keys())
        for item in datos:
            if int(item[0]) in [1,2,3,4,5,6,7]:
                gastos[keys_[int(item[0])-1]]+=float(item[1])
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
                    docs.append(f"{documento}-{item[13].strip()}-{str(item[14]).strip()}")
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
            total = datos['total_egresos']+datos['s_']
            params = (self.numero,datos['fecha'],user['ubicacion'],datos['ventas_efectivo'],datos['ventas_nota_credito'],datos['sencillo_anterior'],
                      datos['otros'],datos['total_ingresos'],datos['devolucion_dinero'],datos['gastos_caja_chica'],datos['gastos_administrativos'],
                      datos['gastos_local'],datos['gastos_proveedores'],datos['gastos_letras'],datos['depositos_bancarios'],datos['sencillo_ma'],
                      datos['total_egresos'],saldo,total,datos['sobrante'],datos['faltante'],user['cod'],self.fecha,datos['total_tarjetas_ingresos'],
                      datos['total_tarjetas_egresos'],datos['total_efectivo'],datos['total_gastos'],documentos['factura']['cantidad'],
                      documentos['boleta']['cantidad'],documentos['nota_credito']['cantidad'],documentos['factura_ticket']['cantidad'],documentos['boleta_ticket']['cantidad'],
                      documentos['factura']['rango'],documentos['boleta']['rango'],documentos['nota_credito']['rango'],documentos['factura_ticket']['rango'],
                      documentos['boleta_ticket']['rango'],datos['total_egresos'],datos['total_ventas'],datos['total_devoluciones'],str(datos['total_articulos']),datos['total_venta_dia'],
                      datos['s_'],datos['saldo_disponible'],datos['total_articulos_devueltos']
                      )

            sql = f"""INSERT INTO m_cuadre (cua_codigo,cua_fecha,ubi_codigo,cua_efecti,cua_nc,cua_senant,cua_otros,cua_moning,cua_egre01,cua_egre02,
            cua_egre03,cua_egre04,cua_egre05,cua_egre06,cua_egre07,cua_senman,cua_monegr,cua_saldo,cua_total,cua_sobra,cua_falta,usuario,fechausu,cua_taring,
            cua_taregr,cua_totefe,cua_totgas,cua_numfac,cua_numbol,cua_numncr,cua_numtfa,cua_numtbo,cua_dhfact,cua_dhbole,cua_dhncre,cua_dhtfac,cua_dhtbol,
            cua_disegr,cua_totven,cua_totdev,cua_totpre,cua_totdia,cua_dissol,cua_dissal,cua_totprd) VALUES({','.join('?' for i in params)})"""
            
            s,_ = CAQ.request(self.credencial,sql,params,'post')
            if not s:
                raise Exception('Error al guardar  los movimientos de caja')
            sql = f"""
            INSERT INTO m_tarjeta (cua_codigo,tar_codigo,tar_nombre,cua_monto,usuario,fechausu) VALUES (?,?,?,?,?,?)"""
            tarjetas = datos['dates']['tarjetas']
            for item in tarjetas:
       
                params = (self.numero,item,tarjetas[item]['nombre'],tarjetas[item]['monto'],user['cod'],datos['fecha'])
                s,_ = CAQ.request(self.credencial,sql,params,'post')
                if not s:
                    raise Exception('Error al guardar las tarjetas')
            data['success'] = 'El cuadre de caja se guardo exitosamente'
        except Exception as e:
            data['error'] = str(e)
        return Response(data)

class ListCuadreCaja(GenericAPIView):
    def post(self,request,*args,**kwargs):
        data = {}
        datos = request.data
        desde = datos['desde'].replace('/','-')
        hasta = datos['hasta'].replace('/','-')
        self.credencial = Credencial(datos['credencial'])
        try:
            sql = f"""SELECT a.cua_codigo,a.cua_fecha,b.ubi_nombre 
            FROM m_cuadre AS a LEFT JOIN t_ubicacion AS b ON a.ubi_codigo=b.ubi_codigo 
            WHERE  
                a.ELIMINI=0
                AND a.cua_fecha BETWEEN '{desde}' AND '{hasta}'
                AND a.ubi_codigo=?
                """
      
            s,result = CAQ.request(self.credencial,sql,(datos['ubicacion'],),'get',1)
            if not s:
                raise Exception('Error al recuperar los cuadres de caja')
            data = [
                {
                    "id":index,
                    "ubicacion":value[2].strip(),
                    "numero":int(value[0]),
                    "fecha":value[1].strftime('%Y-%m-%d')
                } for index,value in enumerate(result)
            ]
        except Exception as e:
            data['error'] = str(e)
        return Response(data)