
import base64
import io
from reportlab.lib.pagesizes import A4,letter
from reportlab.lib.pagesizes import A4,letter,landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate,Image,Paragraph,Frame,Table,Spacer,TableStyle
from reportlab.lib.styles import ParagraphStyle,getSampleStyleSheet
from reportlab.platypus.flowables import PageBreak

from reportlab.pdfgen.canvas import Canvas

from reportlab.lib.enums import TA_RIGHT,TA_CENTER,TA_LEFT
from reportlab.lib.units import inch,mm
from django.conf import settings
import os
from apirest.number_to_text import NumberToText
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
    

class CustomPDF:
    def __init__(self,filename,title:str,header:list,data:list,custom_header,t_soles:float=0,t_dolares:float=0) -> None:
        super(CustomPDF,self).__init__()
        self.filename = filename
        self.title = title
        self.style = getSampleStyleSheet()
        self.header = header
        self.data =  data
        self.t_soles = t_soles
        self.t_dolares = t_dolares
        self.custom_header = custom_header
    def generate(self):
        try:
            self.data.insert(0,self.header)
            col_widths = [220,50,60,60,50,60,80]

            table = Table(self.data,repeatRows=1,colWidths=col_widths)


            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ("FONTSIZE",(0,0),(-1,-1),10),
                ('SPLITBYROWSPAN', (0, 0), (-1, -1), 1)
            ]))
            total_soles = Paragraph(f"<b>TOTAL S/ {self.t_soles:,.2f}</b>",style=ParagraphStyle(name='RightAligned', alignment=2))
            total_dolares = Paragraph(f"<b>TOTAL US$$ {self.t_dolares:,.2f}</b>",style=ParagraphStyle(name='RightAligned', alignment=2))

            content = [Spacer(1,.16*inch),table,total_soles,total_dolares]
            file = SimpleDocTemplate(self.filename,pagesize=letter,title="REPORTE",author="RICHARD AVILES FERRO")
            file.build(content,onFirstPage=self.custom_header,onLaterPages=self.custom_header,canvasmaker=Numeracion)
        except Exception as e:
            raise Exception(str(e))

class PDFCOTIZACION:
    def __init__(self,data,blob):
        self.data = data
        self.blob = blob
    def generate(self):

        doc = SimpleDocTemplate(self.blob,pagesize=letter,leftMargin=0, rightMargin=0, topMargin=0, bottomMargin=0)
        history = []
        try:
            image = os.path.join(settings.BASE_DIR,'static/img/logo_kasac.jpeg')
            img = Image(image,width=100,height=60)
        
            dates = f"""
                    <b>{self.data['empresa']['razon_social']}</b> <br/>
                    <b>RUC:{self.data['empresa']['ruc']}</b><br/>
                    <b>{self.data['empresa']['direccion']}</b> <br/>
                    <b>TELEFONO:{self.data['empresa']['telefono']}</b>
    """
            num_cotizacion = f"""
                <b>N° COTIZACION : {self.data['numero_cotizacion']}</b>
    """
            header_data = [img,Paragraph(dates),Paragraph(num_cotizacion)]
            table = Table([header_data],colWidths=[162,300,150])
            history.append(table)
            line1 = [[Paragraph(f"<b>EMISIÓN: </b> {self.data['emision']}"),Paragraph(f"<b>CONTACTO: </b> {self.data['contacto']}"),Paragraph(f"<b>MOTIVO: </b> {self.data['motivo']}")]]
            table = Table(line1)
            history.append(table)
            line2 = [[Paragraph(f"<b>CLIENTE: </b> {self.data['cliente']}"),Paragraph(f"<b>CONDICIÓN DE PAGO: </b> {self.data['condicion_pago']}")]]
            table = Table(line2)
            history.append(table)
            line3 = [[Paragraph(f"<b>RUC: </b> {self.data['documento']}"),Paragraph(f"<b>O. COMPRA: </b> {self.data['orden_compra']}"),Paragraph(f"<b>OPERACION:</b> {self.data['operacion']}")]]
            table = Table(line3)
            history.append(table)
            line4 = [[Paragraph(f"<b>PLACA : </b> {self.data['placa']}"),Paragraph(f"<b>CHASIS: </b> {self.data['chasis']}"),Paragraph(f"<b>AÑO: </b> {self.data['anyo']}"),Paragraph(f"<b>COLOR: </b> {self.data['color']}")]]
            table = Table(line4)
            history.append(table)
            history.append(Paragraph(f"<b>TIPO DE SERVICIO: </b>{self.data['servicio']}"))
            text = "MEDIANTE EL PRESENTE LE AGRADECEMOS SU INTERÉS Y PRESENCIA EN NUESTROS PORDUCTOS, A CONTINUACIÓN NOS COMPLACE HACERLES LLEGAR NNUESTRA PROPUESTA ECONOMICA SEGUN LAS ESPECIFICACIONES RECAUDADAS"
            history.append(Spacer(1,12))
            history.append(Paragraph(text))
            history.append(Spacer(1,12))
            items = [
        ["CODIGO", "C/V", "CANT.", "ARTICULO","U/M","P. UNI","DSCTO (%)","TOTAL"],
    ]
            total_v = 0
            for item in self.data['items']:
                cantidad_vehiculos =  item[3] if item[3]!=0  else item[4]
                total_v+=cantidad_vehiculos
                items.append([Paragraph(item[0].strip()),Paragraph(f"{cantidad_vehiculos}"),Paragraph(f"{item[2]:.2f}"),Paragraph(item[1].strip()),Paragraph(f"{item[8].strip()}"),Paragraph(f"{item[5]:.2f}"),Paragraph(f"{item[6]:.2f}"),Paragraph(f"{item[7]:.2f}")])
            items.append(['',Paragraph('<b>TOTAL</b>'),Paragraph(f"<b>{total_v}</b>"),'',"",""])
            table = Table(items,colWidths=[70,50,50,200,60,60,50],style=TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ]))
            history.append(table)
            text = NumberToText(self.data['venta_total'])
            history.append(Paragraph(text))
            date = [["BASE IMPONIBLE",self.data['moneda'],f"{self.data['base_imponible']:,.2f}"],
                    [f"IGV({int(self.data['igv_porcent'])}%",self.data['moneda'],f"{self.data['igv']:,.2f}"],
                    [f"TOTAL VENTA",self.data['moneda'],f"{self.data['venta_total']:,.2f}"],
                    ]
            table = Table(date)
            table.hAlign = 'RIGHT'
            table.setStyle(TableStyle([    
                                        ('ALIGN',(0,0),(-1,-1),'RIGHT'),
                                        ('BACKGROUND', (0, 1), (-1, -1), colors.white)
                                        ]))
            history.append(table)
            text = "TERMINOS Y CONDICIONES DE VENTA."
            history.append(Paragraph(text))
            text = "- LOS PRECIOS INCLUYEN IGV."
            history.append(Paragraph(text))
            text = f"- VALIDES DE LA COIZACION POR {self.data['dias_validez']} DIAS"
            history.append(Paragraph(text))
            text = "- ENTREGA INMEDIATA SEGUN CONFIRMACION DE LA ORDEN DE COMPRA."
            history.append(Paragraph(text))
            text = "PARA CUALQUIER CONSULTA SIRVASE AL TELEFONO DE LA REFERENCIA"
            history.append(Paragraph(text))
            data = [
                [Paragraph("ENTIDAD FINANCIERA"),Paragraph("CUENTA"),Paragraph("MONEDA"),Paragraph("NUMERO DE CUENTA"),Paragraph("CÓDIGO CUENTA INTERBANCARIA")],
                ["BANCO DE CRÉDITO DEL PERÚ","CUENTA CORRIENTE","SOLES",self.data['empresa']['cuenta_soles'],"00219400211411600695"],
                ["BANCO DE CRÉDITO DEL PERÚ","CUENTA CORRIENTE","DOLARES",self.data['empresa']['cuenta_dolares'],"00219100157902717659"],
                ["BANCO DE LA NACIÓN","CUENTA DE DETRACCIÓN","SOLES","00076021171","-"],
            ]
            history.append(Spacer(1,12))
            table = Table(data)
            table.setStyle(TableStyle([    
                                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                        ('ALIGN',(0,0),(-1,-1),'LEFT'),
                                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                                        ("GRID",(0,0),(-1,-1),1,colors.black)
                                        ]))
            history.append(table)
            history.append(Spacer(1,12))

            text = "ATENTAMENTE"
            history.append(Paragraph(text))
            text = '.'*50
            history.append(Spacer(1,12))
            style_ = ParagraphStyle(name='text-center',alignment=TA_CENTER)
            history.append(Paragraph(text=text,style=style_))
            text = self.data['empresa']['razon_social']
            history.append(Paragraph(text=text,style=style_))
        except Exception as e:
            print(str(e))
        doc.build(history)
class PDFHistorialCliente:
    def __init__(self,filename:str,title:str,header:list,data:list[list[str]],custom_cabecera,saldo):
        super(PDFHistorialCliente,self).__init__()
        self.filename = filename
        self.title = title
        self.header = header
        self.data = data
        self.custom_cabecera = custom_cabecera
        self.saldo = saldo
    def generate(self):
        self.data.insert(0,self.header)
        style = TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ("FONTSIZE",(0,0),(-1,-1),10),
                    ('SPLITBYROWSPAN', (0, 0), (-1, -1), 1)
        ])
        table = Table(data=self.data,repeatRows=1,style=style)
        data = [
            [Paragraph(text=f"""Linea de Credito"""),Paragraph(text=f"""<para alignment="right">{self.saldo["linea_credito"]:,.2f}</para>""")],["Saldo Soles S/",Paragraph(text=f"""<para alignment="right" >{self.saldo['soles']}</para>""")],["Saldo Dolares US$",Paragraph(text=f"""<para alignment="right">{self.saldo['dolares']}</para>""")]]
        table1 = Table(data=data,hAlign=TA_RIGHT,colWidths=[100,100])

        
        file = SimpleDocTemplate(self.filename,pagesize=landscape(letter),title="REPORTE",author="RICHARD AVILES FERRO")
        file.build([table,Spacer(1,10,True),table1],canvasmaker=Numeracion,onFirstPage=self.custom_cabecera,onLaterPages=self.custom_cabecera)
        # se hizo cambios 
        
class Numeracion(Canvas):
    def __init__(self,*args,**kwargs):
        Canvas.__init__(self,*args,**kwargs)
        self.paginas = []
    def showPage(self):
        self.paginas.append(dict(self.__dict__))
        self._startPage()
    def save(self):
        paginas = len(self.paginas)
        for state in self.paginas:
            self.__dict__.update(state)
            self.numeracion(paginas)
            Canvas.showPage(self)
        Canvas.save(self)
    def numeracion(self,numeros_pagina):
        self.drawRightString(204*mm,15*mm+(.2*inch),f"Pagina {self._pageNumber} de {numeros_pagina}")



class PDFPedido:
    def __init__(self,filename,cabecera,detalle,empresa) -> None:
        self.filename = filename
        self.cabecera = cabecera
        self.detalle = detalle
        self.empresa = empresa
    def generate(self):
       
        doc = SimpleDocTemplate(self.filename,pagesize=A4) 
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
        header = ['CODIGO','ARTICULO','CANT.','P. UNIT','TOTAL']
        data = [header]
        for item in self.detalle:
            items = [item['codigo'],Paragraph(item['nombre']),item['cantidad'],item['precio'],item['subtotal']]
            data.append(items)

        story.append(Spacer(0,20))
        w,h = A4
        col_widths = [w*.15,w*.55,w*.10,w*.10,w*.10,]
        table = Table(data,colWidths=col_widths,repeatCols=1)
        table.hAlign  = 'CENTER'
        table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                        ('ALIGN', (0, 0), (0, -1), 'LEFT'),#codigo
                                        ('ALIGN', (1, 0), (1, -1), 'LEFT'),#nombre
                                        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),#cantidad
                                        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),#precio
                                        ('ALIGN', (4, 0), (4, -1), 'RIGHT'),#subototal
                                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
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
    def ticket(self,datos,tarjetas):
        try:

            width, height =A4
            doc = SimpleDocTemplate(self.filename,pagesize=(width,height)) 
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