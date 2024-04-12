# from weasyprint import HTML,CSS
import base64
import io

from rest_framework.generics import GenericAPIView

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,Spacer,TableStyle
from reportlab.lib.styles import ParagraphStyle,getSampleStyleSheet
from reportlab.platypus.flowables import PageBreak
from django.http import HttpResponse
import os
from django.conf import settings

from apirest.credenciales import Credencial
from apirest.querys import CAQ
from reportlab.pdfgen.canvas import Canvas

class GeneratedPDF(GenericAPIView):

    def post(self, request, *args, **kwargs):
      
        self.datos = request.data
        self.credencial = Credencial(self.datos['credencial'])
        try:
            sql = "SELECT emp_razon,emp_ruc,emp_direc,emp_telef FROM t_empresa"

            s,result = CAQ.request(self.credencial,sql,(),"get",0)
            if not s:
                raise Exception("No se pudo recuperar datos de la empresa")

            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="three_columns_with_image.pdf"'
            c = Canvas(response, pagesize=A4)

            # Definir estilo de texto en negrita
            style = getSampleStyleSheet()["Normal"]
            style.fontName = "Helvetica-Bold"
            style.fontSize = 10

            # Dibujar imagen
            image = os.path.join(settings.BASE_DIR, 'static/img/kasac.jpg')
            c.drawImage(image=image, x=13, y=750, width=100, height=50)

            # Dibujar texto con estilo de fuente en negrita usando Paragraph
            p = Paragraph(text=f" N° COTIZACION {self.datos['numero_cotizacion']}", style=style)
            c.drawText(p)
            # Dibujar texto adicional con drawString()
            c.drawString(x=150, y=810, text=result[0].strip())
            c.drawString(x=150, y=790, text=result[1].strip())
            c.drawString(x=150, y=770, text=result[2].strip())
            c.drawString(x=150, y=750, text=result[3].strip())

            c.save()

            return response
           
        except Exception as e:
            print(str(e))
            return HttpResponse({"error": str(e)})
class PDF:
    def __init__(self,empresa,cabecera,detalle) -> None:
        self.empresa = empresa
        self.cabecera = cabecera
        self.detalle = detalle
    def generate(self):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer,pagesize=A4) 
        style = getSampleStyleSheet()
        custom_style = ParagraphStyle(name='Negrita',parent=style['Normal'])
        custom_style.fontName = 'Helvetica-Bold'
        custom_style.alignment = 0

        style_normal = style['Normal']
        style_normal.alignment = 2
        style_normal.fontName = 'Helvetica-Bold'
        style_normal.wordWrap = False
        style_heading = style['Heading1']
        
        story = []
        story.append(Paragraph(self.empresa,style_heading))
        story.append(Spacer(1,12))
        story.append(Paragraph(f"NUMERO PEDIDO: {self.cabecera.numero_pedido}",custom_style))
        story.append(Paragraph(f"EMISIÓN: {self.cabecera.fecha_emision}",custom_style))
        story.append(Paragraph(f"CLIENTE: {self.cabecera.cliente}",custom_style))
        story.append(Paragraph(f"DOCUMENTO: {self.cabecera.documento}",custom_style))
        story.append(Paragraph(f"DIRECCIÓN: {self.cabecera.direccion}",custom_style))
        story.append(Paragraph(f"VENDEDOR: {self.cabecera.vendedor}",custom_style))
        header = ['CODIGO','ARTICULO','CANTIDAD','P. UNIT','TOTAL']
        data = [header]
        for item in self.detalle:
            items = [item['codigo'],Paragraph(item['nombre']),item['cantidad'],item['precio'],item['subtotal']]
            data.append(items)
        story.append(Spacer(0,20))
        w,h = A4
        col_widths = [w*.15,w*.35,w*.15,w*.15,w*.10,w*.10]
        table = Table(data,colWidths=col_widths,repeatCols=1)
        table.hAlign  = 'CENTER'
        table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                                    ]))
        story.append(table)
        story.append(Paragraph(f"Observación: {self.cabecera.observacion}"))
        moneda = 'S/' if self.cabecera.moneda == 'S' else '$'
        data = [
            ['CARGO','','MONTO'],
            ['SUBTOTAL',moneda,f"{self.cabecera.subtotal:.2f}"],
            ['DESCUENTO',moneda,f"{self.cabecera.descuento:.2f}"],
            ['BASE IMPONIBLE',moneda,f"{self.cabecera.base_imponible:.2f}"],
            ['IGV',moneda,f"{self.cabecera.igv:.2f}"],
            ['VENTA TOTAL',moneda,f"{self.cabecera.venta_total:.2f}"],
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
        pdf = buffer.getvalue()
        return base64.b64encode(pdf).decode('utf-8')
    def ticket(self,datos,tarjetas):
        try:
            buffer = io.BytesIO()
            width, height =A4
            doc = SimpleDocTemplate(buffer,pagesize=(width,height)) 
            negrita_left = ParagraphStyle(name='Negrita',alignment=0,fontName='Helvetica-Bold',fontSize=8)
            normal_left = ParagraphStyle(name='Negrita',alignment=0,fontSize=8)
            negrita_right = ParagraphStyle(name='Negrita',alignment=2,fontName='Helvetica-Bold',fontSize=8)
            normal_right = ParagraphStyle(name='Negrita',alignment=2,fontSize=8)
            negrita_center = ParagraphStyle(name='Centeres',alignment=1,fontName='Helvetica-Bold')
           
            story = []
            story.append(Paragraph(self.empresa,style=negrita_center))
            story.append(Spacer(1,12))
            data = [
                [Paragraph("N° CUADRE",style=negrita_left),Paragraph(f"{datos[0]}",style=negrita_right)],
                [Paragraph("FECHA",style=normal_left),Paragraph(f"{datos[1].strftime('%d/%m/%Y')}",style=normal_right)],
                [Paragraph("TIENDA",style=normal_left),Paragraph(f"{datos[2]}",style=normal_right)],
                [Paragraph("TIPO DE CAMBIO",style=normal_left),Paragraph(f"{datos[3]}",style=normal_right)],
                [Paragraph("VENTAS DEL DIA",style=normal_left),Paragraph(f"{datos[4]:.2f}",style=normal_right)],
                [Paragraph("DEVOLUCION DEL DIA",style=normal_left),Paragraph(f"{datos[5]:.2f}",style=normal_right)],
                [Paragraph("TOTAL VENTAS",style=negrita_left),Paragraph(f"{datos[6]:.2f}",style=negrita_right)],
            ]
            
      
            story.append(self.style_table(data))
            story.append(Spacer(1,12))
            story.append(Paragraph('INGRESOS',style=negrita_center))
            data = [
                [Paragraph(f"VENTAS EFECTIVO",style=normal_left),Paragraph(f'{datos[7]:.2f}',style=normal_right)],
                [Paragraph(f"VENTAS AL CREDITO",style=normal_left),Paragraph(f'{datos[8]:.2f}',style=normal_right)],
                [Paragraph(f"VENTAS N. CREDITO",style=normal_left),Paragraph(f'{datos[9]:.2f}',style=normal_right)],
                [Paragraph(f"SENCILLO ANTERIOR",style=normal_left),Paragraph(f'{datos[10]:.2f}',style=normal_right)],
                [Paragraph(f"OTROS",style=normal_left),Paragraph(f'{datos[11]:.2f}',style=normal_right)],
                [Paragraph(f"TOTAL EFECTIVO",style=negrita_left),Paragraph(f'{datos[12]:.2f}',style=negrita_right)],

            ]+[[Paragraph(f"{item[0]}",style=normal_left),Paragraph(f"{item[1]}",style=normal_right)] for item in tarjetas]+[
                [Paragraph(f"TOTAL TARJ. ING",style=negrita_left),Paragraph(f"{datos[13]:.2f}",style=negrita_right)],
                [Paragraph(f"TOTAL INGRESOS",style=negrita_left),Paragraph(f"{datos[14]:.2f}",style=negrita_right)],
            ]            
            story.append(self.style_table(data))
            story.append(Spacer(1,12))

            story.append(Paragraph('EGRESOS',style=negrita_center))
            data = [
                [Paragraph("DEVOLUCION",style=normal_left),Paragraph(f"{datos[15]:.2f}",style=normal_right)],
                [Paragraph("GASTOS C. CHICA",style=normal_left),Paragraph(f"{datos[16]:.2f}",style=normal_right)],
                [Paragraph("GASTOS ADMINIS.",style=normal_left),Paragraph(f"{datos[17]:.2f}",style=normal_right)],
                [Paragraph("GASTOS LOCAL",style=normal_left),Paragraph(f"{datos[18]:.2f}",style=normal_right)],
                [Paragraph("GASTOS PROVEE",style=normal_left),Paragraph(f"{datos[19]:.2f}",style=normal_right)],
                [Paragraph("GASTOS LETRAS",style=normal_left),Paragraph(f"{datos[20]:.2f}",style=normal_right)],
                [Paragraph("DEPOSITOS BANC.",style=normal_left),Paragraph(f"{datos[21]:.2f}",style=normal_right)],
                [Paragraph("SENCILLO MAÑANA",style=normal_left),Paragraph(f"{datos[22]:.2f}",style=normal_right)],
                [Paragraph("TOTAL GASTOS",style=negrita_left),Paragraph(f"{datos[23]:.2f}",style=negrita_right)],
            ]+[[Paragraph(f"{item[0]}",style=normal_left),Paragraph(f"{item[1]}",style=normal_right)] for item in tarjetas]+[
                [Paragraph("TOTAL TARJ. EGR.",style=negrita_left),Paragraph(f"{datos[24]:.2f}",style=negrita_right)],
                [Paragraph("TOTAL EGRESOS",style=negrita_left),Paragraph(f"{datos[25]:.2f}",style=negrita_right)],
            ]
            story.append(self.style_table(data))
            story.append(Paragraph('-'*88,style=negrita_center))
            data = [
                [Paragraph("SALDO (ING-EGR)",style=normal_left),Paragraph(f"{datos[26]:.2f}",style=normal_right)],
                [Paragraph("DISPONIBLE CAJA",style=normal_left),Paragraph(f"{datos[27]:.2f}",style=normal_right)],
                [Paragraph("US$",style=normal_left),Paragraph(f"{datos[28]:.2f}",style=normal_right)],
                [Paragraph("SALDO DISPONIBLE",style=normal_left),Paragraph(f"{datos[29]:.2f}",style=normal_right)],
                [Paragraph("+ EGRESOS",style=normal_left),Paragraph(f"{datos[30]:.2f}",style=normal_right)],
                [Paragraph("TOTAL S/",style=negrita_left),Paragraph(f"{datos[31]:.2f}",style=negrita_right)],
                [Paragraph("SOBRANTE",style=normal_left),Paragraph(f"{datos[32]:.2f}",style=normal_right)],
                [Paragraph("FALTANTE",style=normal_left),Paragraph(f"{datos[33]:.2f}",style=normal_right)],
                [Paragraph("TOTAL A DEPOSITAR",style=negrita_left),Paragraph(f"{datos[7]:.2f}",style=negrita_right)],
                [Paragraph("TOTAL TARJETAS",style=negrita_left),Paragraph(f"{datos[24]:.2f}",style=negrita_right)],
                [Paragraph("TOTAL PRENDAS",style=negrita_left),Paragraph(f"{int(datos[34])}",style=negrita_right)],
                [Paragraph("TOTAL PRENDAS DEVUELTAS",style=negrita_left),Paragraph(f"{int(datos[35])}",style=negrita_right)],
                [Paragraph("NUMER DE FACTURAS",style=normal_left),Paragraph(f"{int(datos[36])}",style=normal_right)],
                [Paragraph("DESDE-HASTA",style=normal_left),Paragraph(f"{datos[37]}",style=normal_right)],
                [Paragraph("NUMER DE BOLETAS",style=normal_left),Paragraph(f"{int(datos[38])}",style=normal_right)],
                [Paragraph("DESDE-HASTA",style=normal_left),Paragraph(f"{datos[39]}",style=normal_right)],
                [Paragraph("NUMER N. CREDITO",style=normal_left),Paragraph(f"{int(datos[40])}",style=normal_right)],
                [Paragraph("DESDE-HASTA",style=normal_left),Paragraph(f"{datos[41]}",style=normal_right)],
                [Paragraph("NUMER TICKET FACTURA",style=normal_left),Paragraph(f"{int(datos[42])}",style=normal_right)],
                [Paragraph("DESDE-HASTA",style=normal_left),Paragraph(f"{datos[43]}",style=normal_right)],
                [Paragraph("NUMER TICKET BOLETA",style=normal_left),Paragraph(f"{int(datos[44])}",style=normal_right)],
                [Paragraph("DESDE-HASTA",style=normal_left),Paragraph(f"{datos[45]}",style=normal_right)],
            ]
            story.append(self.style_table(data))
            story.append(PageBreak())
            doc.build(story)
            pdf = buffer.getvalue()
            return base64.b64encode(pdf).decode("utf-8")
        except Exception as e:
            print(str(e))
            raise Exception(str(e))
    def style_table(self,data):
        w,h = A4
        col_widths = [w*.25,w*.25]
        table = Table(data, colWidths=col_widths,rowHeights=10)
        table.hAlign  = 'CENTER'
        table.setStyle(TableStyle([
                                    ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                                    
                                ]))
        return table