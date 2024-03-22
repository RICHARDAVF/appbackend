import io
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from apirest.credenciales import Credencial
from datetime import datetime
from apirest.querys import CAQ
from num2words import num2words

from apirest.view.pdf.views import PDF
class TicketFactura(GenericAPIView):
    credencial : object = None
    anio : int = datetime.now().year
    def numero_text(self,numero)->str:
        parte_entera = int(numero)
        parte_decimal = int(numero-int(numero))
        return f"SON: {num2words(parte_entera,lang='es')} CON {parte_decimal}/100 SOLES"
    def text_formater(self,text):
        cadena = ''
        for i in range(0,len(text),48):
            cadena+=f"[C]{text[i:i+48]}\n"
        return cadena
    def post(self,request,*args,**kwagrs):
        data = {}
        datos = request.data
        self.credencial = Credencial(datos['credencial'])
        try:
            sql = f"""SELECT
                        a.MOV_COMPRO,
                        a.ROU_TVENTA,
                        b.AUX_NOMBRE,
                        b.AUX_DOCUM,
                        a.MOV_FECHA,
                        c.ubi_direc,
                        c.ubi_telef,
                        a.doc_compro,
                        a.mov_moneda,
                        a.ROU_TVENTA,
						a.ROU_IGV,
						a.rou_dscto,
                        a.fac_serie,
                        a.fac_docum,
                        a.rou_bruto,
                        a.rou_submon
                    FROM guic{self.anio} AS a
                    LEFT JOIN t_auxiliar AS b ON b.AUX_CLAVE = a.MOV_CODAUX
                    LEFT JOIN t_ubicacion AS c ON c.ubi_codigo=a.ubi_codigo
                    WHERE  a.MOV_COMPRO=?
                """
           
            s,result1 = CAQ.request(self.credencial,sql,(datos['pedido'],),'get',0)

            if not s:
                raise Exception('Ocurrio un error al recuperar los datos del pedido')

            sql = f"""
                    SELECT
                        a.mom_cant,
                        a.mom_valor,
                        a.mom_punit,
                        b.ART_NOMBRE,
                        a.mom_dscto1

                    FROM guid{self.anio} AS a

                    LEFT JOIN t_articulo AS b ON b.ART_CODIGO=a.ART_CODIGO

                    WHERE  a.mov_compro=?
                """
            s,result2 = CAQ.request(self.credencial,sql,(datos['pedido'],),'get',1)
       
            if not s:
                raise Exception('Error al recuperar los items de la factura')
            sql = "SELECT emp_razon,emp_ruc,emp_direc FROM t_empresa"
            s,result3 = CAQ.request(self.credencial,sql,(),'get',0)
            if not s:
                raise Exception('Error al recuperar el nombre de la empresa')
            formato = ''
            formato+=f'[C]<b>{result3[0].strip()}</b>\n'
            formato+=f'[C]<b>RUC: {result3[1].strip()}</b>\n'
            formato+= self.text_formater(result1[5].strip())
            sql = "select top 1 par_email from fe_parametro"
            s,result4 = CAQ.request(self.credencial,sql,(),'get',0)
            if not s:
                raise Exception('Error al recuperar el correo')
            formato+=f'[C]Email: {result4[0].strip()}\n'
            formato+=f'[C]Telf: {result1[6].strip()}\n'
            text='BOLETA DE VENTA ELECTRONICA' if result1[7].strip()=='07' else 'FACTURA ELECTRONICA'
            formato+=f'[C]{text}\n'
            formato+=f'[C]N°: {result1[12].strip()}-{result1[13].strip()}\n'
            formato+=f"[L]Cliente: {result1[2].strip()}\n"
            formato+=f'[L]Documento:{result1[3].strip()}\n'
            formato+=f"[L]Moneda:{'SOLES' if result1[8].strip()=='S' else 'DOLARES'}\n"
            formato+=f"[L]Fecha Emision: {result1[4].strftime('%d/%m/%Y')}\n"
            formato+=f'{self.__item(result2)}'
            formato+='[L]'+'-'*47+'\n'

            icon_moneda = 'S/' if result1[8].strip()=='S' else '$'
            if result1[7].strip()=='06':
                formato+=f"[R]{'OP GRAVADA:'} {icon_moneda} {float(result1[15]):>10}\n"
                formato+=f"[R]{'DESCUENTO:'} {icon_moneda} {float(result1[11]):>10}\n"
                formato+=f"[R]SUB TOTAL: {icon_moneda} {float(result1[14]):>10}\n"
                formato+=f"[R]IGV: {icon_moneda} {float(result1[10]):>10}\n"
            formato+=f"[R]{'IMPORTE TOTAL: '}{icon_moneda} {float(result1[9]):>10}\n"
            formato+='[L]'+'-'*48+'\n'
            formato+=f"[L]{self.numero_text(float(result1[9]))}\n"
            nombre_documento = 'boleta' if result1[7].strip()=='07' else 'factura'

            tipo_documento='6' if len(result1[3].strip())==11 else '1'
            formato+=f"\n[C]<qrcode>{result3[1].strip()}|{result1[7].strip()}|{result1[12].strip()}|{result1[13].strip()}|{float(result1[9])}|{float(result1[10])}|{result1[4].strftime('%Y-%m-%d')}|{tipo_documento}|{result1[3].strip()}</qrcode>\n"
            text = f"Representacion grafica de la {nombre_documento} Resolucion N° 034-030-0000103/SUNAT"
            formato+='\n'+self.text_formater(text)
            formato+=f'[C]Consulta comprobante\n'
            formato+=f'[C]app.facturaonline.pe/invitado\n'
            formato+=f"\n[C]GRACIAS POR SU PREFERENCIA\n"
            formato+=f'[L]\n'
            formato+=f'[L]\n'

            data['format']=formato
        except Exception as e:
            data['error'] = str(e)
        return Response(data)
    
    def __item(self,items):
        cadena = f"[L]<b>{'Descripcion':<47}</b>\n"
        cadena+=f"[L]<b>{'Cant':<6}{'Precio':>8}{'Monto':>8}{'Dsto %':>8}{'Dsto V.':>8}{'Sub T.':>9}</b>\n"
        cadena+='[L]'+'-'*48+'\n'

        for item in items:
            if len(item[3].strip())>47:
                des = item[3].strip()
                for i in range(0,len(des),47):
                        cadena+=f"[L]{des[i:i+47]}\n"    
            else:
                cadena+=f"[L]{item[3].strip()}\n"
            total = float(item[0])*float(item[2])
            descuento_valor = round(abs(total-float(item[1])),2)

            cadena+=f"[L]<b>{str(int(item[0])):<6}{str(float(item[2])):>8}{round(total,2):>8}{str(float(item[4])):>8}{str(descuento_valor):>8}{str(float(item[1])):>9}</b>"
        return cadena

    def numero_text(self,numero)->str:
        parte_entera = int(numero)
        parte_decimal = str(numero).split('.')[-1]
        return f"SON: {num2words(parte_entera,lang='es').upper()} Y {parte_decimal}/100 SOLES"
class TicketNP(GenericAPIView):
    credencial : object = None
    anio : int = datetime.now().year
    def numero_text(self,numero)->str:
        parte_entera = int(numero)
        parte_decimal = str(numero).split('.')[-1]
        return f"SON: {num2words(parte_entera,lang='es').upper()} Y {parte_decimal}/100 SOLES"
    def post(self,request,*args,**kwagrs):
        data = {}
        datos = request.data
        self.credencial = Credencial(datos['credencial'])
        try:
            sql = f"""SELECT
                        a.MOV_COMPRO,
                        a.ROU_TVENTA,
                        b.AUX_NOMBRE,
                        b.AUX_DOCUM,
                        a.MOV_FECHA,
                        a.mov_moneda
                    FROM cabepedido AS a
                    LEFT JOIN t_auxiliar AS b ON b.AUX_CLAVE = a.MOV_CODAUX
                    WHERE  a.MOV_COMPRO=?
                """
           
            s,result1 = CAQ.request(self.credencial,sql,(datos['pedido'],),'get',0)

            if not s:
                raise Exception('Ocurrio un error al recuperar los datos del pedido')
            sql = f"""
                    SELECT
                        a.mom_cant,
                        a.mom_valor,
                        a.mom_punit,
                        b.ART_NOMBRE,
                        a.mom_dscto1
                       
                    FROM movipedido AS a

                    LEFT JOIN t_articulo AS b ON b.ART_CODIGO=a.ART_CODIGO

                    WHERE  a.mov_compro=?
                """
         
            s,result2 = CAQ.request(self.credencial,sql,(datos['pedido'],),'get',1)
            if not s:
                raise Exception('Ocurrio un error al recuperar los items')

            formato=''
            formato+=f"[C]<b>{datos['credencial']['razon_social']}</b>\n"
            formato+=f"[C]<b>PEDIDO N° {result1[0].strip()}</b>\n"
            formato+=f"[L]<b>Cliente: {result1[2].strip()}</b>\n"
            formato+=f"[L]<b>Documento: {result1[3].strip()}</b>\n"
            formato+=f"[L]<b>Fecha Emision: {result1[4].strftime('%Y-%m-%d')}  {datetime.now().strftime('%H:%M:%S')}</b>\n"
            formato+='[L]'+'-'*48+'\n'
            formato+=f"{self.__item(result2)}"
            formato+='[L]'+'-'*47+'\n'
            formato+=f"""[L]<b><font size='normal'>{f"IMPORTE TOTAL: {'S/' if result1[5].strip()=='S' else '$ '}{float(result1[1])}":>47}<font></b>\n"""
            formato+='[L]'+'-'*48+'\n'
            formato+=f'[L]{self.numero_text(float(result1[1]))}\n'
            formato+='[L]\n'
            formato+='[L]\n'
          
            data['format'] = formato
        
        except Exception as e:
            data['error'] = str(e)
        return Response(data)

    
    def __item(self,items):
        cadena = f"[L]<b>{'Descripcion':<47}</b>\n"
        cadena+=f"[L]<b>{'Cant':<6}{'Precio':>8}{'Monto':>8}{'Dsto %':>8}{'Dsto V.':>8}{'Sub T.':>9}</b>\n"
        cadena+='[L]'+'-'*48+'\n'

        for item in items:
            if len(item[3].strip())>47:
                des = item[3].strip()
                for i in range(0,len(des),47):
                        cadena+=f"[L]{des[i:i+47]}\n"
            else:
                cadena+=f"[L]{item[3].strip()}\n"
            total = float(item[0])*float(item[2])
            descuento_valor = round(abs(total-float(item[1])),2)
            cadena+=f"[L]<b>{str(int(item[0])):>6}{str(float(item[2])):>8}{round(total,2):>8}{str(float(item[4])):>8}{str(descuento_valor):>8}{str(float(item[1])):>9}</b>"
        return cadena
    
class TicketCuadreCaja(GenericAPIView):
    def post(self,request,*args,**kwargs):
        data = {}
        datos = request.data
        self.credencial = Credencial(datos['credencial'])
        self.tarjetas = []
        
        try:
            formato = ''
            sql = "SELECT emp_razon FROM t_empresa"
            s,result1 = CAQ.request(self.credencial,sql,(),'get',0)
            formato+=f"[C]<b>{result1[0].strip()}</b>\n"
            sql = f"""SELECT 
                        a.cua_codigo,
                        a.cua_fecha,
                        b.ubi_nombre,
                        a.cua_tc,
                        a.cua_totdia,
                        a.cua_totdev,
                        a.cua_totven,
                        a.cua_efecti,
                        a.cua_credi,
                        a.cua_nc,
                        a.cua_senant,
                        a.cua_otros,
                        a.cua_totefe,
                        a.cua_taring,
                        a.cua_moning,
                        a.cua_egre01,
                        a.cua_egre02,
                        a.cua_egre03,
                        a.cua_egre04,
                        a.cua_egre05,
                        a.cua_egre06,
                        a.cua_egre07,
                        a.cua_senman,
                        a.cua_totgas,
                        a.cua_taregr,
                        a.cua_monegr,
                        a.cua_saldo,
                        a.cua_dissol,
                        a.cua_disdol,
                        a.cua_dissal,
                        a.cua_disegr,
                        a.cua_total,
                        a.cua_sobra,
                        a.cua_falta,
                        a.cua_totpre,
                        a.cua_totprd,
                        a.cua_numfac,
                        a.cua_dhfact,
                        a.cua_numbol,
                        a.cua_dhbole,
                        a.cua_numncr,
                        a.cua_dhncre,
                        a.cua_numtfa,
                        a.cua_dhtfac,
                        a.cua_numtbo,
                        a.cua_dhtbol
                    FROM m_cuadre AS a 
                    LEFT JOIN t_ubicacion AS b ON a.ubi_codigo=b.ubi_codigo 
            WHERE 
                a.cua_codigo=?
               
            """
            s,result2 = CAQ.request(self.credencial,sql,(datos['numero'],),'get',0)
            if not s:
                raise Exception('Error al recuperar el cuadre de caja')
            formato+=f"[L]<b>N° Cuadre</b> [R]<b>{int(result2[0])}</b>\n"
            formato+=f"[L]Fecha [R]{result2[1].strftime('%d/%m/%Y')}\n"
            formato+=f"[L]Tienda [R]{result2[2].strip()}\n"
            formato+=f"[L]T. Cambio [R]{result2[3]:.3f}\n"
            formato+=f"[L]VENTAS DEL DIA [R]{result2[4]:.2f}\n"
            formato+=f"[L]DEVOLUCION DEL DIA [R]{result2[5]:.2f}\n"
            formato+=f"[L]<b>TOTAL VENTAS</b> [R]{result2[6]:.2f}\n"
            formato+=f"[C]<b>INGRESOS</b>\n"
            formato+=f"[L]VENTAS EFECTIVO [R]{result2[7]:.2f} \n"
            formato+=f"[L]VENTAS AL CREDITO [R]{result2[8]:.2f} \n"
            formato+=f"[L]VENTAS N. CREDITO [R]{result2[9]:.2f} \n"
            formato+=f"[L]SENCILLO ANTERIOR [R]{result2[10]:.2f} \n"
            formato+=f"[L]OTROS [R]{result2[11]:.2f} \n"
            formato+=f"\n\n"
            formato+=f"[L]<b>TOTAL EFECTIVO</b>[R]<b>{result2[12]:.2f}</b> \n"
            formato+=f"{self.get_tarjetas()}"
            formato+=f"[L]<b>TOTAL TARJ. ING.</b>[R]{result2[13]:.2f}\n"
            formato+=f"[L]<b>TOTAL INGRESOS</b>[R]{result2[14]:.2f}\n"
            formato+=f"[C]<b>EGRESOS</b>\n"
            formato+=f"[L]DEVOLUCION [R]{result2[15]:.2f}\n"
            formato+=f"[L]GASTOS C. CHICA [R]{result2[16]:.2f}\n"
            formato+=f"[L]GASTOS ADMIN. [R]{result2[17]:.2f}\n"
            formato+=f"[L]GASTOS LOCAL [R]{result2[18]:.2f}\n"
            formato+=f"[L]GASTOS PROVEE. [R]{result2[19]:.2f}\n"
            formato+=f"[L]GASTOS LETRAS [R]{result2[20]:.2f}\n"
            formato+=f"[L]DEPOSITOS BANC. [R]{result2[21]:.2f}\n"
            formato+=f"[L]SENCILLO MAÑANA [R]{result2[22]:.2f}\n"
            formato+=f"[L]<b>TOTAL GASTOS</b> [R]<b>{result2[23]:.2f}</b>\n"
            formato+=f"{self.get_tarjetas()}"
            formato+=f"[L]<b>TOTAL TARJ. EGR.</b> [R]<b>{result2[24]:.2f}</b>\n"
            formato+=f"[L]<b>TOTAL EGRESOS</b> [R]<b>{result2[25]:.2f}</b>\n"
            formato+="-"*48+'\n'
            formato+=f"[L]SALDO (ING-EGR) [R]{result2[26]:.2f}\n"
            formato+=f"[L]DISPONIBLE CAJA [R]{result2[27]:.2f}\n"
            formato+=f"[L]US$ [R]{result2[28]:.2f}\n"
            formato+=f"[L]SALDO DISPONIBLE [R]{result2[29]:.2f}\n"
            formato+=f"[L]+ EGRESOS [R]{result2[30]:.2f}\n"
            formato+=f"[L]<b>TOTAL S/</b> [R]<b>{result2[31]:.2f}</b>\n"
            formato+=f"[L]SOBRANTE [R]{result2[32]:.2f}\n"
            formato+=f"[L]FALTANTE [R]{result2[33]:.2f}\n"
            formato+=f"[L]<b>TOTAL A DEPOSITAR</b> [R]<b>{result2[7]:.2f}</b>\n"
            formato+=f"[L]<b>TOTAL TARJETAS</b> [R]<b>{result2[24]:.2f}</b>\n"
            formato+=f"[L]<b>TOTAL PRENDAS</b> [R]<b>{result2[34]:.2f}</b>\n"
            formato+=f"[L]<b>TOTAL PRENDAS DEVUELTAS</b> [R]<b>{result2[35]:.2f}</b>\n"
            formato+=f"[L]NUMERO. FACTURAS [R]{int(result2[36])}\n"
            formato+=f"[L]DESDE-HASTA  {result2[37].strip()}\n"
            formato+=f"[L]NUMERO. BOLETAS [R]{int(result2[38])}\n"
            formato+=f"[L]DESDE-HASTA  {result2[39].strip()}\n"
            formato+=f"[L]NUMERO N. CREDITO [R]{int(result2[40])}\n"
            formato+=f"[L]DESDE-HASTA  {result2[41].strip()}\n"
            formato+=f"[L]NUMERO TICKET FACTURA [R]{int(result2[42])}\n"
            formato+=f"[L]DESDE-HASTA  {result2[43].strip()}\n"
            formato+=f"[L]NUMERO TICKET BOLETA [R]{int(result2[44])}\n"
            formato+=f"[L]DESDE-HASTA  {result2[45].strip()}\n"
            data['format'] = formato
            data['pdf'] = PDF(result1[0].strip(),'','').ticket(result2,self.tarjetas)
        except Exception as e:
            data['error'] = str(e)
        return Response(data)
    def get_tarjetas(self):
        try:
            sql = "SELECT tar_nombre, cua_monto FROM m_tarjeta WHERE cua_codigo=?"
            s,result = CAQ.request(self.credencial,sql,(self.request.data['numero'],),'get',1)
            if not s:
                raise Exception('Error al recuperar las tarjetas y sus montos')
            formato = ''
            self.tarjetas = result
            for item in result:
                formato+=f"[L]{item[0].strip()}[R]{item[1]}\n"
            return formato
        except Exception as e:
            raise Exception (str(e))

        