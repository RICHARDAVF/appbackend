from django.http import FileResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus.flowables import PageBreak
from datetime import datetime
from django.http import HttpResponse
import io
from rest_framework.generics import GenericAPIView
from apirest.querys import Querys
from numpy import array
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
class PdfPedidoView(GenericAPIView):
    def order(self):
        
        sql = """SELECT 
                    a.ART_CODIGO,
                    a.MOM_CANT,
                    a.tal_codigo,
                    a.MOM_PUNIT,
                    b.ART_NOMBRE,
                    b.art_partes,
                    a.mom_valor
                FROM movipedido AS a INNER JOIN t_articulo AS b ON a.ART_CODIGO=b.art_CODIGO WHERE MOV_COMPRO=? order by b.ART_NOMBRE"""
        result = Querys(self.kwargs).querys(sql,(self.kwargs['codigo'],),'get',1)
        datos = []
        for item in result:
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
    def get(self,request,*args,**kwargs):
        partes = self.order()
       
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        custom_style = ParagraphStyle(name='Negrita', parent=styles['Normal'])
        custom_style.fontName = 'Helvetica-Bold'  
        custom_style.alignment = 0 
       
        story = []  
        style_normal = styles["Normal"]
        style_heading = styles["Heading1"]
        sql = """
                SELECT*FROM cabepedido WHERE MOV_COMPRO =?
        """
        story.append(Paragraph("DEMO DENINM ART", style_heading))
        story.append(Spacer(1, 12))
        fecha = Paragraph(f'EMISION: {datetime.now().strftime("%d-%m-%Y")}',custom_style)
        fecha.vAlign = 'LEFT'
        story.append(fecha)
        cliente = Paragraph(f"CLIENTE: RICHARD AVILES FERRO",custom_style)
        story.append(cliente)
        direccion = Paragraph(f"DIRECCION: LIMA-LIMA-PERU",custom_style)
        story.append(direccion)
        documento = Paragraph(f"DOCUMENTO: 10273986127838",custom_style)
        story.append(documento)
        vendedor = Paragraph(f"VENDEDOR: ADMINISTRACION",custom_style)
        story.append(vendedor)
        for parte in partes:
            result,tallas_header = self.agruparTallas(partes[parte])
            cabeceras = ["CODIGO", "ARTICULO","CANT."]+[i for i in tallas_header]+['P. UNIT','TOTAL']
            data = [cabeceras,
                    ]
            for item in result.values():

                numeros = [elemento for elemento in item['cantidad'] if isinstance(elemento, (int, float))]

                lista = [item['codigo'],item['nombre'],sum(numeros)]+item['cantidad']+[round(item['precio'],2),sum(item['total'])]
                data.append(lista)
            w,h = A4
            story.append(Spacer(0,20))
            col_widths = [w*0.15,w*.25,w*.06]+[w*0.3/len(tallas_header)]*len(tallas_header)+[w*.1,w*.1]
            table = Table(data,colWidths=col_widths)
            table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                                   ]))

            story.append(table)
        story.append(PageBreak())

   
        doc.build(story)


        buffer.seek(0)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="mi_archivo.pdf"'
        response.write(buffer.read())

        return response
