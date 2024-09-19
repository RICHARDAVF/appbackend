from dataclasses import dataclass
from datetime import datetime
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from django.http import HttpResponse
from apirest.credenciales import Credencial
from apirest.querys import CAQ
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.platypus.flowables import PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
import logging
import traceback

from apirest.view.pdf.views import PDF


logger = logging.getLogger('django')
def agrupar(datos):
    datos_agrupados = {}
    for item in datos:
        codigo = item['codigo']
        nombre = item['nombre']
        talla = item['talla']
        cantidad = item['cantidad']
        precio = item['precio']
        total = item['total']
        if nombre in datos_agrupados:
            datos_agrupados[nombre]['talla'].append(talla)
            datos_agrupados[nombre]['cantidad'].append(cantidad)
            datos_agrupados[nombre]['total'].append(total)
        else:
            datos_agrupados[nombre] = {'codigo': codigo, 'nombre': nombre, 'talla': [talla], 'cantidad': [cantidad],'precio':precio,'total':[total]}
    return datos_agrupados
@dataclass
class CABECERA:
    numero_pedido : str = None
    fecha_emision : datetime = None
    direccion : str = None
    documento : str = None
    vendedor : str = None
    observacion : str = None
    subtotal : float = None
    descuento : float = None
    base_imponible : float = None
    igv : float = None
    venta_total : float = None
    cliente : str = None
    moneda : str = None
    p_igv : float = None
class PedidoPDF(GenericAPIView):
    credencial : object = None
    def order(self):
        
        sql = """SELECT 
                    a.ART_CODIGO,
                    'MOM_CANT'=sum(a.MOM_CANT),
                    a.tal_codigo,
                    a.MOM_PUNIT,
                    b.ART_NOMBRE,
                    b.art_partes,
                    'mom_valor'=sum(a.mom_valor)
            FROM movipedido AS a INNER JOIN t_articulo AS b ON a.ART_CODIGO=b.art_CODIGO WHERE MOV_COMPRO=?
            group by a.ART_CODIGO,a.tal_codigo,
                                a.MOM_PUNIT,
                                b.ART_NOMBRE,
                                b.art_partes
            order by b.ART_NOMBRE
            """
        params = (self.request.data['numero_pedido'],)
        s,res = CAQ.request(self.credencial,sql,params,'get',1)
        
        datos = []
        for item in res:
            d = {'codigo':item[0].strip(),'cantidad':int(item[1]),'talla':item[2].strip(),'precio':float(item[3]),'nombre':item[4].strip(),'parte':int(item[5]),'total':round(item[6],2)}
            datos.append(d)
        return self.ordenPartes(datos)
    def agruparTallas(self,datos):
        result  = agrupar(datos)
        tallas = sorted(list({item['talla'] for item in datos}))
        talla_orden = {'SS': 1, 'MM': 2, 'LL': 3, 'XL': 4}
        if "XL" or 'SS' in tallas:
            tallas = sorted(tallas, key=lambda x: talla_orden.get(x, 99))
        tallas_header= ["S" if item =='SS' else ('M' if item=='MM' else ('L' if item=='LL' else item)) for item in tallas ]
        for item in result:
            lista = ['']*len(tallas)
            for i, j in zip(result[item]['talla'],result[item]['cantidad']):
                id = tallas.index(i)
                lista[id] = int(j)
            result[item]['talla'] = tallas
            result[item]['cantidad'] = lista   
        return result,tallas_header
    def ordenPartes(self,data):
        partes = {}
        for item in data:
            parte = item['parte']
            if parte in partes:
                partes[parte].append(item)
            else:
                partes[parte] = [item]
        return partes
    def post(self,request,*args,**kwargs):
        datos = request.data
        self.credencial = Credencial(datos['credencial'])
        if int(datos["credencial"]["codigo"])==1:
            return self.pdf_with_tallas()
        else:

            return self.pdf_off_tallas()
    def pdf_off_tallas(self):
        try:
            sql = "SELECT emp_razon FROM t_empresa"
            s,result = CAQ.request(self.credencial,sql,(),'get',0)
            if not s:
                raise Exception('No se pudo recuperar el nombre de la empresa')
            empresa = result[0].strip()
            sql = """SELECT 
                        a.MOV_FECHA,
                        a.gui_direc,
                        a.gui_ruc,
                        'vendedor'=(SELECT USU_NOMBRE FROM t_usuario WHERE usu_codigo=a.USUARIO ),
                        a.gui_exp001,
                        a.rou_submon,
                        a.rou_dscto,
                        a.ROU_BRUTO,
                        a.ROU_IGV,
                        a.ROU_TVENTA,
                        b.AUX_NOMBRE,
                        a.MOV_MONEDA,
                        a.ROU_PIGV
                    FROM cabepedido AS a INNER JOIN t_auxiliar AS b ON a.MOV_CODAUX = b.AUX_CLAVE WHERE MOV_COMPRO=?"""
            s,result = CAQ.request(self.credencial,sql,(self.request.data['numero_pedido'],),'get',0)
            if not s:
                raise Exception('No se pudo recuperar datos del cliente')
            cabecera = CABECERA(
                numero_pedido=self.request.data['numero_pedido'],
                fecha_emision=result[0].strftime('%Y-%m-%d'),
                direccion=result[1].strip(),
                documento=result[2].strip(),
                vendedor=result[3].strip(),
                observacion=result[4].strip(),
                subtotal=float(result[5]),
                descuento=float(result[6]),
                base_imponible=float(result[7]),
                igv=float(result[8]),
                venta_total=float(result[9]),
                cliente=result[10].strip(),
                moneda=result[11].strip(),
                p_igv=float(result[12])

            )
      
            sql = """SELECT 
                        a.ART_CODIGO,
                        a.MOM_CANT,
                        a.MOM_PUNIT,
                        b.ART_NOMBRE,
                        a.mom_valor,
                        a.mom_dscto1,
                        a.ped_observ
                    FROM movipedido AS a 
                    INNER JOIN t_articulo AS b ON a.ART_CODIGO=b.art_CODIGO WHERE MOV_COMPRO=?
                    ORDER BY b.ART_NOMBRE"""
            s,result = CAQ.request(self.credencial,sql,(self.request.data['numero_pedido'],),'get',1)
            if not s:
                raise Exception('Error al consultar a la base de datos')
       
            response = HttpResponse(content_type='application/pdf')
            response["Content-Disposition"] = "attachment;filename='REPORTE.pdf'"
            PDF(response,empresa,cabecera,self.items(result)).generate()
            return response
        except Exception as e:
            logger.error("A error ocurred %s",e)
            traceback.print_exc()
            return Response({"error":f'Ocurrio un error :{str(e)}'})
    def items(self,detalle):
        data = []
        for item in detalle:
            d = {
                'codigo':item[0].strip(),
                'cantidad':float(item[1]),
                'precio':float(item[2]),
                'nombre':f"{item[3].strip()}<br/>{item[-1].strip()}".replace('\n','<br/>'),
                'subtotal':float(item[4]),
                'descuento':float(item[5])
            }
            data.append(d)
        return data


      
    def pdf_with_tallas(self,):
        try:
            partes = self.order()

            response = HttpResponse(content_type='application/pdf')
            response["Content-Disposition"] = "attachment;filename='REPORTE.pdf'"
            doc = SimpleDocTemplate(response, pagesize=A4)

            styles = getSampleStyleSheet()
            custom_style = ParagraphStyle(name='Negrita', parent=styles['Normal'])
            custom_style.fontName = 'Helvetica-Bold'  
            custom_style.alignment = 0 
        
            story = []  
            style_normal = styles["Normal"]
            style_normal.alignment = 2
            style_normal.fontName = "Helvetica-Bold"
            style_normal.wordWrap = False
            style_heading = styles["Heading1"]
            sql = """
                    SELECT 
                        a.MOV_FECHA,
                        b.AUX_NOMBRE,
                        a.gui_direc,
                        a.gui_ruc,
                        'vendedor'=(SELECT USU_NOMBRE FROM t_usuario WHERE usu_codigo=a.USUARIO ),
                        a.gui_exp001,
                        a.rou_dscto,
                        a.ROU_IGV,
                        a.ROU_BRUTO,
                        a.rou_submon,
                        a.ROU_TVENTA,
                        a.MOV_MONEDA,
                        a.ROU_PIGV
                    FROM cabepedido AS a INNER JOIN t_auxiliar AS b ON a.MOV_CODAUX = b.AUX_CLAVE WHERE MOV_COMPRO=?
            """
           
            params = (self.request.data["numero_pedido"],)
            s,res = CAQ.request(self.credencial,sql,params,'get',0)
            if not s:
                raise ValueError(res["error"])
            story.append(Paragraph(f"{self.request.data['credencial']['razon_social']}", style_heading))
            story.append(Spacer(1, 12))
            numero_pedido = Paragraph(f"NUMERO PEDIDO: {self.request.data['numero_pedido']}",custom_style)
            story.append(numero_pedido)
            fecha = Paragraph(f"EMISION: {res[0].strftime('%d/%m/%Y')}",custom_style)
            story.append(fecha)
            cliente = Paragraph(f"CLIENTE: {res[1].strip()}",custom_style)
            story.append(cliente)
            direccion = Paragraph(f"DIRECCION: {res[2].strip()}",custom_style)
            story.append(direccion)
            documento = Paragraph(f"DOCUMENTO: {res[3].strip()}",custom_style)
            story.append(documento)
            vendedor = Paragraph(f"VENDEDOR: {res[4].strip()}",custom_style)
            story.append(vendedor)
            for parte in partes:
                result,tallas_header = self.agruparTallas(partes[parte])
                cabeceras = ["CODIGO", "ARTICULO","CANT."]+[i for i in tallas_header]+['P. UNIT','TOTAL']
                data = [cabeceras,
                        ]
                total = 0
                for item in result.values():

                    numeros = [elemento for elemento in item['cantidad'] if isinstance(elemento, (int, float))]
                    total+=sum(numeros)
                    lista = [item['codigo'],Paragraph(item['nombre']),sum(numeros)]+item['cantidad']+[round(item['precio'],2),sum(item['total'])]
                    data.append(lista)
            
                data.append(['','TOTAL:',total]+['']*(len(tallas_header)+2))
                w,h = A4
                story.append(Spacer(0,20))
                col_widths = [w*0.15,w*.25,w*.06]+[w*0.3/len(tallas_header)]*len(tallas_header)+[w*.1,w*.1]
                table = Table(data,colWidths=col_widths,repeatRows=1)
                table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                                    ]))

                story.append(table)
            obs = Paragraph(f"Observacion: {res[5].strip()}")
        
            story.append(obs)
            moneda = 'S/ ' if 'S' == res[11].strip() else '$'
            data = [
                ['CARGO','MONEDA',"MONTO"],
                ['SUBTOTAL',moneda,round(res[9], 2)],
                ['DESCUENTO',moneda,round(res[6], 2)],
                ['BASE IMPONIBLE',moneda,round(res[8], 2)],
                [f'IGV {res[12]:.0f}%',moneda,round(res[7], 2)],
                ['TOTAL VENTA',moneda,round(res[10], 2)],
                ]

            table= Table(data,repeatRows=1)
            table.hAlign = 'RIGHT'
            table.setStyle(TableStyle([
                                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                        ('ALIGN',(0,0),(-1,-1),'RIGHT'),
                                    ('BACKGROUND', (0, 1), (-1, -1), colors.white)
                                    ]))
            story.append(table)
            story.append(PageBreak())
            doc.build(story)
            return response
        except Exception as e :
            print(str(e))
            return Response({'error':f'No se puede generar el pdf:{str(e)}'})
class PDFStock(GenericAPIView):
    def agrupar(self,datos):
        dates = {}
        for item in datos:
            codigo = item['codigo']
            nombre = item['nombre']
            stock = item['stock']
            if codigo in dates:
                dates[codigo]['stock']+= int(stock)
            else:
                dates[codigo] = {'codigo':codigo,'nombre':nombre,'stock':int(stock)} 
        return dates
    def post(self,request,*args,**kwargs):
        res = {}
        try:
            datos = request.data['datos']
            ubicacion = request.data['ubicacion']
            cred = request.data['cred']
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment;filename="REPORTE.pdf"'
            doc = SimpleDocTemplate(response, pagesize=A4)
            style = getSampleStyleSheet()
            story = []
            titulo = Paragraph(f'{cred["razon_social"]}',style['Title'])
            story.append(titulo)
            ubi = Paragraph(f"<b>UBICACION</b>: {ubicacion}")
            story.append(ubi)
            now = datetime.now()
            fecha = Paragraph(f"<b>Fecha</b>: {now.strftime('%d-%m-%Y')}")
            fecha.hAlign = "RIGHT"
            hora = Paragraph(f"<b>Hora</b>: {now.strftime('%H:%M:%S')}")
            hora.hAlign = "RIGHT"
            story.append(fecha)
            story.append(hora)
            cabeceras = ['CODIGO','NOMBRE','CANTIDAD']
            
            table_data = []
            table_data.append(cabeceras)
            
            for item in list(self.agrupar(datos).values()):
                lista = [Paragraph(item['codigo']),Paragraph(item['nombre']),Paragraph(str(item['stock']))]
                table_data.append(lista)
            w,h = A4

            widths = [w*0.2,w*.6,w*.2]
            table = Table(table_data,repeatRows=1,colWidths=widths)
            table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), (0.7, 0.7, 0.7)),
                    ('TEXTCOLOR', (0, 0), (-1, 0), (1, 1, 1)),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), (1, 1, 1))
                ]))
            story.append(table)
            story.append(PageBreak())
            doc.build(story)
            return response
        except Exception as e:
            print(str(e))
            res['error'] = f'Ocurrio un error: f{str(e)}'
        return Response(res)