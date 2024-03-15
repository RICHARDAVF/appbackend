from datetime import datetime
import json
from apirest.querys import CAQ
from apirest.view.apis.views import GenerateToken
import requests
import os
from django.conf import settings
from dotenv import load_dotenv
load_dotenv()
class GUIC:
    def __init__(self,credencial,serie,numero):
        self.serie = serie
        self.numero = numero
        self.razon_social = ''
        self.ruc = ''
        self.condicion_pago = ''
        self.fecha_vencimiento :datetime =  None
        self.obs : str = ''
        self.direccion : str = ''
        self.numero_pedido : str = ''
        self.base_imponible : float = 0
        self.importe_total : float = 0
        self.igv : float = 0
        self.moneda : str = ''
        self.emails : list[str] = None
        self.get_boleta_factura(credencial)
    def get_boleta_factura(self,credencial):
        sql = f"""SELECT
                    c.aux_razon,
                    a.gui_ruc,
                    'codigo_pago'=ISNULL((SELECT b.pag_nombre FROM t_maepago AS b WHERE b.pag_codigo=a.pag_codigo),''),
                    a.MOV_FECHA,
                    a.gui_exp001,
                    a.gui_direc,
                    a.mov_compro,
                    a.rou_bruto,
                    a.rou_tventa,
                    c.AUX_EMAIL,
                    a.mov_moneda,
                    a.rou_igv
                FROM guic{datetime.now().year} AS a
                LEFT JOIN t_auxiliar AS c ON a.gui_ruc=c.aux_docum
                WHERE a.fac_serie=? AND a.fac_docum=? """
        params = (self.serie,self.numero)

        _,result = CAQ.request(credencial,sql,params,'get',0)
    
        self.razon_social = result[0].strip()
        self.ruc = result[1].strip()
        self.condicion_pago = result[2].strip()
        self.fecha_vencimiento = result[3].strftime('%Y-%m-%d')
        self.obs = result[4].strip()
        self.direccion = result[5].strip()
        self.numero_pedido = result[6].strip()
        self.base_imponible = float(result[7])
        self.importe_total = float(result[8])
        self.emails = result[9].strip()
        self.moneda = result[10].strip()
        self.igv = float(result[11])

class Factura:
    def __init__(self,credencial,serie,numero):
        self.serie = serie
        self.numero = numero
        self.credencial = credencial
        self.guic = GUIC(self.credencial,self.serie,self.numero)
        self.json = {}
    def generate_json(self):
        try:
            self.json['tipoOperacion'] = '0101'
            self.json['serie'] = self.serie
            self.json['numero'] = self.numero
            self.json['fechaEmision']  = datetime.now().strftime('%Y-%m-%d')
            self.json['horaEmision'] = datetime.now().strftime('%H:%M:%S')
            self.receptor()
            self.adicional()
            self.items()
            self.json['totalVentaGravada'] = self.guic.base_imponible
            self.json['totalVentaInafecta'] = 0
            self.json['totalVentaExonerada'] = 0
            self.json['sumatoriaIgv'] = self.guic.igv
            self.json['montoTotalImpuestos'] = self.guic.igv
            self.json['importeTotal'] = self.guic.importe_total
            self.json['tipoMoneda'] = 'PEN' if self.guic.moneda == 'S' else 'USD'
            data = json.dumps(self.json,indent=4)
            ruta = os.path.join(settings.BASE_DIR,'media/json/factura')
            with open(ruta+f"{self.guic.ruc}.json",'w') as file:
                file.write(data)
        except Exception as e:
            raise Exception(str(e))
    def receptor(self):
        data = {
            'tipo':1 if len(self.guic.ruc)==8 else 6,
            'nro':self.guic.ruc,
            'razonSocial':self.guic.razon_social
        }
        self.json['receptor'] = data
    def adicional(self):
        data = {
            'condPago':self.guic.condicion_pago,
            'email':self.get_emails(self.guic.emails),
            'fechaVencimiento':self.guic.fecha_vencimiento,
            'codigoSunatEstablecimiento':'',
            'observacion':self.guic.obs,
            'dirAlternativa':self.guic.direccion
        }
     
        self.json['adicional'] = data
    def get_emails(self,emails:str):
        if len(emails)!=0:
            return emails.replace(";",',').split(',')
        sql = "SELECT TOP 1  par_email FROM fe_parametro "
        s,result = CAQ.request(self.credencial,sql,(),'get',0)
        return [result[0].strip()]
    def items(self):
        sql = f"""SELECT a.ART_CODIGO,b.art_nombre,a.mom_cant,a.mom_valor,a.MOM_PUNIT,a.mom_dscto1, c.ume_sunat FROM GUID{datetime.now().year} AS a 
                LEFT JOIN t_articulo AS b ON a.art_codigo=b.art_codigo
                LEFT JOIN t_umedida AS c ON c.UME_CODIGO=b.UME_CODIGO
                WHERE 
                    a.mov_compro=?
                """
        params = (self.guic.numero_pedido,)
        s,result = CAQ.request(self.credencial,sql,params,'get',1)
        if not s:
            raise Exception('Error al recuperar los articulos para la factura')
        data = []
        for item in result:
     
            precio_venta_unitario = float(item[4])*(1-float(item[5])/100)
            precio = float(item[4])
            cantidad = float(item[2])
            importe_total = precio_venta_unitario*cantidad/1.18
            valor = cantidad*precio
            d =    {
                'unidadMedidaCantidad':item[6].strip(),
                'codigoProducto':item[0].strip(),
                'descripcion':item[1].strip(),
                'cantidad':cantidad,
                'precioVentaUnitario':round(precio_venta_unitario,2),
                'tipoPrecioVentaUnitario':'01',
                'tipoAfectacionIgv':'10',
                'codigoTributo':'1000',
                'porcentajeImpuesto':18,
                'baseAfectacionIgv':round(importe_total,2),
                'montoAfectacionIgv':round(importe_total*.18,2),
                'montoTotalImpuestosItem':round(importe_total*.18,2),
                'valorUnitario':round(precio/1.18,2),
                'valorVenta':round(importe_total,2),
                'adicional':{}
            }
            if float(item[5])>0:
                d['cargosDescuentosItem'] = [{
                    'indicador':'descuento',
                    'codigoCargoDescuento':'00',
                    'factorCargoDescuento':float(item[5])/100,
                    'montoCargoDescuento':round(valor*float(item[5])/118,2),
                    'baseCargoDescuento':round(valor/1.18,2)
                }]
            data.append(d)
     
        self.json['items'] = data
    def enviar(self):
        sql = "SELECT  TOP 1 par_url,par_acekey,par_seckey FROM fe_parametro"
        s,result = CAQ.request(self.credencial,sql,(),'get',0)
        url = result[0].strip()
        access_key = result[1].strip()
        secret_key = result[2].strip()
        # access_key = os.getenv('ACCESS_KEY')
        # secret_key=os.getenv('SECRET_KEY')
        token,timestap = GenerateToken(access_key=access_key,secret_key=secret_key).encryptdates()
        ruta = 'boleta' if self.serie[0]=='B' else ('factura' if self.serie[0]=='F' else 'error')
        if ruta=='error':
            raise Exception('Tipo de documento no aceptado')
        res = requests.post(
            url=url+ruta,
            headers={
                'Authorization':f'Fo {access_key}:{token}:{timestap}',
            },
            json=self.json
            )
        res = res.json()
        if 'serie' in res and 'numero' in res:
            self.update_guic()
        else:
            raise Exception(f"{res}")
    def update_guic(self):
        try:
            sql = f"UPDATE  guic{datetime.now().year} SET gui_envife=? WHERE fac_serie=? AND fac_docum=?"
            params = (1,self.serie,self.numero)
            s,_ =  CAQ.request(self.credencial,sql,params,'post')
            if not s:
                raise Exception('Error al actualizar el estado de la recepcion')
            
        except Exception as e:
            raise Exception(str(e))