# from weasyprint import HTML,CSS
import base64
import io
from django.template.loader import get_template
from rest_framework.generics import GenericAPIView
from apirest.querys import Querys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,Spacer,TableStyle
from reportlab.lib.styles import ParagraphStyle,getSampleStyleSheet
from reportlab.platypus.flowables import PageBreak
def pdf_generate(request):
    html_template = get_template('mi_template_pdf.html')
    sql = "select art_codigo from t_articulo_imagen"
    images = Querys({'host':'192.168.1.40','db':'siia_demo_denim_art','user':'sa','password':'Noi2011'}).querys(sql,(),'get',1)
    data = [{'img':f"{img[0].strip()}A.JPG"} for img in images]
    context = {}
    context['images'] = data
    render_html = html_template.render(context)
    # pdf_file = HTML(string=render_html,base_url=request.build_absolute_uri()).write_pdf()
    # response = HttpResponse(pdf_file,content_type='application/pdf')
    # response['Content_Disposition'] = 'filename="home.pdf"'
    # return response
class GeneratedPDF(GenericAPIView):
    def get(self,request,*args,**kwargs):
        lista_ubicaciones = request.GET.getlist('arreglo[]',[])
        almacen = request.GET.get('almacen')
        linea = request.GET.get('linea')
        genero = request.GET.get('genero')
        modelo = request.GET.get('modelo')
        color = request.GET.get('color')
        temporada = request.GET.get('temporada')
        talla = request.GET.get('talla')
        html_template = get_template('mi_template_pdf.html')
        sql = "select top 100 art_codigo from t_articulo_imagen"
        images = Querys(kwargs).querys(sql,(),'get',1)
        data = [{'img':f"{img[0].strip()}A.JPG"} for img in images]
        context = {}
        context['images'] = data
        render_html = html_template.render(context)
        # pdf_file = HTML(string=render_html,base_url=request.build_absolute_uri()).write_pdf()
        # response = HttpResponse(pdf_file,content_type='application/pdf')
        # response['Content_Disposition'] = 'filename="home.pdf"'
        # return response
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
        story.append(Paragraph(f"NUMERo PEDIDO: {self.cabecera.numero_pedido}",custom_style))
        story.append(Paragraph(f"EMISIÓN: {self.cabecera.fecha_emision}",custom_style))
        story.append(Paragraph(f"DIRECCIÓN: {self.cabecera.direccion}",custom_style))
        story.append(Paragraph(f"DOCUMENTO: {self.cabecera.documento}",custom_style))
        story.append(Paragraph(f"{self.cabecera.vendedor}",custom_style))
        header = ['CODIGO','ARTICULO','CANTIDAD','P. UNIT','TOTAL']
        data = [header]
        for item in self.detalle:
            items = [item['codigo'],item['nombre'],item['cantidad'],item['precio'],item['subtotal']]
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