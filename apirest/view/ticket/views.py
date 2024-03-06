from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from apirest.crendeciales import Credencial
from datetime import datetime
from apirest.querys import CAQ
from num2words import num2words
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
            formato+='[L]'+'-'*48+'\n'

            icon_moneda = 'S/' if result1[8].strip()=='S' else '$'
            if result1[7].strip()=='06':
                formato+=f"[R]{'OP GRAVADA:'} {icon_moneda} {float(result1[15]):>6}\n"
                formato+=f"[R]{'DESCUENTO:'} {icon_moneda} {float(result1[11]):>6}\n"
                formato+=f"[R]SUB TOTAL: {icon_moneda} {float(result1[14]):>6}\n"
                formato+=f"[R]IGV: {icon_moneda} {float(result1[10]):>6}\n"
            formato+=f"[R]{'IMPORTE TOTAL: '}{icon_moneda} {float(result1[9]):>6}\n"
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
        cadena = f"[L]<b>{'Descripcion':<48}</b>\n"
        cadena+=f"[L]<b>{'Cant':<6}{'Precio':>8}{'Monto':>8}{'Dsto %':>8}{'Dsto V.':>8}{'Sub T.':>10}</b>\n"
        cadena+='[L]'+'-'*48+'\n'

        for item in items:
            if len(item[3].strip())>48:
                des = item[3].strip()
                for i in range(0,len(des),48):
                        cadena+=f"[L]{des[i:i+48]}\n"    
            else:
                cadena+=f"[L]{item[3].strip()}\n"
            total = float(item[0])*float(item[2])
            cadena+=f"[L]<b>{str(int(item[0])):>6}{str(float(item[2])):>8}{round(total,2):>8}{str(float(item[4])):>8}{str(total*float(item[4])):>8}{str(float(item[1])):>10}</b>"
        return cadena

    def numero_text(self,numero)->str:
        parte_entera = int(numero)
        parte_decimal = str(numero).split('.')[-1]
        return f"SON: {num2words(parte_entera,lang='es').upper()} Y {parte_decimal}/100 SOLES"
class TickeNP(GenericAPIView):
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
            formato+='[L]'+'-'*48+'\n'
            formato+=f"""[L]<b><font size='normal'>{f"IMPORTE TOTAL: {'S/' if result1[5].strip()=='S' else '$ '}{float(result1[1])}":>48}<font></b>\n"""
            formato+='[L]'+'-'*48+'\n'
            formato+=f'[L]{self.numero_text(float(result1[1]))}\n'
            formato+='[L]\n'
            formato+='[L]\n'
          
            data['format'] = formato
        
        except Exception as e:
            data['error'] = str(e)
        return Response(data)

    
    def __item(self,items):
        cadena = f"[L]<b>{'Descripcion':<48}</b>\n"
        cadena+=f"[L]<b>{'Cant':<6}{'Precio':>8}{'Monto':>8}{'Dsto %':>8}{'Dsto V.':>8}{'Sub T.':>10}</b>\n"
        cadena+='[L]'+'-'*48+'\n'

        for item in items:
            if len(item[3].strip())>48:
                des = item[3].strip()
                for i in range(0,len(des),48):
                        cadena+=f"[L]{des[i:i+48]}\n"
                
                   
            else:
                cadena+=f"[L]{item[3].strip()}\n"
            total = float(item[0])*float(item[2])
            cadena+=f"[L]<b>{str(int(item[0])):>6}{str(float(item[2])):>8}{round(total,2):>8}{str(float(item[4])):>8}{str(total*float(item[4])):>8}{str(float(item[1])):>10}</b>"
        return cadena