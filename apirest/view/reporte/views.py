from reportlab.pdfgen import canvas
from django.conf import settings
from apirest.credenciales import Credencial
from apirest.querys import CAQ
from apirest.view.pdf.views import CustomPDF
from apirest.views import QuerysDb
import os
from reportlab.lib.pagesizes import A4
import base64
from rest_framework.response import Response
from rest_framework import generics
import io
from datetime import datetime
from PIL import Image
from itertools import groupby
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak,Table,TableStyle,Spacer
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.platypus import Image as img
from django.http import HttpResponse
from django.http import FileResponse
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.enums import TA_RIGHT,TA_CENTER,TA_LEFT
def decode_and_save_image(base64_img, filename):
    try:
        image_data = base64.b64decode(base64_img)
        img = Image.open(io.BytesIO(image_data))
        new_size = (300, 400)  
        img = img.resize(new_size)
        file_path = os.path.join(f"{settings.BASE_DIR}/static/img", filename + ".JPG")
        img.save(file_path, "JPEG", quality=40) 
    except Exception as e:
        # img = Image.open(os.path.join(f"{settings.BASE_DIR}/static/img",  "defaul.jpg"))
        # new_size = (300, 400)   
        # img = img.resize(new_size)
        # file_path = os.path.join(f"{settings.BASE_DIR}/static/img", filename + ".JPG")
        # img.save(file_path, "JPEG", quality=40) 
        pass

def query(sql,params,args):
    conn = QuerysDb.conexion(*args)
    cursor = conn.cursor()
    cursor.execute(sql,params)
    data = cursor.fetchall()
    conn.commit()
    conn.close()
    return data
def draw_image(p, file_path, x, y,ancho,alto):
    p.drawImage(file_path, x, y, width=ancho, height=alto)
def group_key(item):
    return item['genero'], item['linea']
def agrupar(datos):
    datos_agrupados = {}
    for item in datos:
        codigo = item['codigo']
        nombre = item['nombre']
        talla = 'S'if item['talla']=='SS' else ('M' if item['talla']=='MM' else('L' if item['talla']=='LL' else item['talla'] ))
        stock = item['stock']
        if nombre in datos_agrupados:
            datos_agrupados[nombre]['talla'].append(talla)
            datos_agrupados[nombre]['stock'].append(stock)
        else:
            datos_agrupados[nombre] = {'codigo': codigo, 'nombre': nombre, 'talla': [talla], 'stock': [stock]}
    return datos_agrupados
class PDFView(generics.GenericAPIView):
    def post(self,request,*args,**kwargs):
        res = {}
        cred = request.data['cred']
        
        try:
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'inline; filename="example.pdf"'

            p = canvas.Canvas(response, pagesize=A4)
            creden = tuple(request.data['creden'].values())
            sql = "SELECT art_codigo,art_image2,art_image3 FROM t_articulo_imagen"
            date = query(sql,(),creden)
            for item in date:
                try:
                    if not os.path.isfile(os.path.join(f"{settings.BASE_DIR}/static/img",f"{item[0]}A.JPG")): 
                        decode_and_save_image(item[1],f"{item[0]}A")
                    if not os.path.isfile(os.path.join(f"{settings.BASE_DIR}/static/img",f"{item[0]}B.JPG")): 
                        decode_and_save_image(item[2],f"{item[0]}B")
                except:
                    pass
            coordenadas = [
            [[30,580],[160,580]],[[320,580],[460,580]],
            [[30,355],[160,355]],[[320,355],[460,355]],
            [[30,155],[160,155]],[[320,155],[460,155]]
            ]
            coord_text = [
                [30,560],[320,560],
                [30,340],[320,340],
                [30,90],[320,90]
            ]
            coord_talla = [
                [30,550],[320,550],
                [30,330],[320,330],
                [30,80],[320,80]
            ]
            coord_stock = [
                [30,540],[320,540],
                [30,320],[320,320],
                [30,70],[320,70]
            ]
            data = request.data
            generos = {i['value']:i['label'] for i in data['genero']}
            lineas = {i['value']:i['label'] for i in data['linea']}
            data_sorted = sorted(data['datos'], key=lambda x: (x['genero'], x['linea']))
            grouped_data = {}
            for key, group in groupby(data_sorted, group_key):
                genero, linea = key
                grouped_data.setdefault(genero, {})
                grouped_data[genero].setdefault(linea, []).extend(list(group))
            file_path = os.path.join(settings.BASE_DIR, 'static', 'img\logo.png')
            draw_image(p,file_path,20,790,300,50)
            p.drawString(400,810,f'Fecha: {datetime.now().strftime("%d-%m-%Y")}')
            p.drawString(400,800,f'Hora : {datetime.now().strftime("%H:%M:%S")}')
            p.drawString(50,770,f"UBICACION: {request.data['ubicacion']}")
            for gender in grouped_data:
                p.drawString(50,760,"GENERO: "+str(generos[str(gender)]))
                for line in grouped_data[gender]:
                    p.drawString(50,750,"LINEA: "+str(lineas[line]))
                    agrupados = grouped_data[gender][line]
                    final_result = list(agrupar(agrupados).values())
                    
                    itm=0
                    for item in final_result:
                        p.setFont("Helvetica", 8)
                
                        try:
                            file_path = os.path.join(settings.BASE_DIR, 'static', 'img', f"{item['codigo']}A.JPG")
                            draw_image(p,file_path,*coordenadas[itm][0],100,150)
                        except:
                            
                            file_path = os.path.join(settings.BASE_DIR, 'static', 'img\default.jpg')
                            draw_image(p,file_path,*coordenadas[itm][0],100,150)
                        try:
                            file_path = os.path.join(settings.BASE_DIR, 'static', 'img', f"{item['codigo']}B.JPG")
                            draw_image(p,file_path,*coordenadas[itm][1],100,150)
                        except:
                            file_path = os.path.join(settings.BASE_DIR, 'static', 'img\default.jpg')
                            draw_image(p,file_path,*coordenadas[itm][1],100,150)
                        p.drawString(*coord_text[itm],item['nombre'].strip())
                        const =0
                        for tal,stock in zip(item['talla'],item['stock']):
                            p.drawString(coord_talla[itm][0]+const,coord_talla[itm][1],tal)
                            p.drawString(coord_stock[itm][0]+const,coord_stock[itm][1],str(stock))
                            const+=15
                        if itm == 5:#0,1,2,3,4,5,
                            p.showPage()
                        itm+=1
                        if itm==6:
                            itm = 0
                        p.rect(20,10,560,730)
                        p.line(290,10,290,740)
                        p.line(20,520,580,520)
                        p.line(20,310,580,310)
                    if itm!=0:
                        p.showPage()
            p.save()
            user = request.data['user']
            ruta = os.path.join(settings.BASE_DIR,'media',f'archivo{cred["ruc"]}-{user["cod"]}-{user["codigo"]}.pdf')
            with open(ruta,'wb') as file:
                file.write(response.content)
            res['success'] = "success"
        except Exception as e:
            res['error'] = f"Ocurrio un error : {str(e)}"
        return Response(res)
        
class DownloadPDF(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        cod = kwargs['cod']
        codigo = kwargs['codigo']
        ruc = kwargs['ruc']
        pdf = os.path.join(settings.BASE_DIR,'media',f'archivo{ruc}-{cod}-{codigo}.pdf')
        return FileResponse(open(pdf,'rb'),as_attachment=True)
class PDFview1(generics.GenericAPIView):
    def post(self,request,*args,**kwargs):
        res = {}
        try:
            data = request.data
            cred = request.data['cred']
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            partes = {}  
            for item in data['datos']:
                parte = item['parte']
                if parte in partes:
                    partes[parte].append(item)
                else:
                    partes[parte] = [item]
            story = []
            first_page_image_path =os.path.join(settings.BASE_DIR, 'static', 'img\logo.png')
            first_page_image = img(first_page_image_path, width=300, height=60) 
            first_page_image.hAlign = 'CENTER'  
            story.append(first_page_image)
            ubi = Paragraph(request.data['ubicacion'])
            ubi.hAlign = "CENTER"
            story.append(ubi)
            now = datetime.now()
            fecha = Paragraph(f"Fecha: {now.strftime('%d-%m-%Y')}")
            fecha.hAlign = "RIGHT"
            hora = Paragraph(f"Hora: {now.strftime('%H:%M:%S')}")
            hora.hAlign = "RIGHT"
            talla_orden = {'S': 1, 'M': 2, 'L': 3, 'XL': 4}
            story.append(fecha)
            story.append(hora)
            for parte in partes:
                styles = getSampleStyleSheet()
                normal_style = styles["Normal"]
                table_data = []
                datos = list(agrupar(partes[parte]).values())
                tallas = sorted(list(set([str(talla).replace('SS','S').replace('LL','L').replace('MM','M') for i in datos for talla in i['talla']])))
                if "XL" in tallas or 'S' in tallas or 'M' in tallas or 'L' in tallas:
                    tallas = sorted(tallas, key=lambda x: talla_orden.get(x, 99))
                cabeceras = [Paragraph("Codigo", normal_style),
                        Paragraph("Nombre", normal_style),
                        Paragraph("Stock", normal_style),
                        ]
                for tal in tallas:
                    cabeceras.insert(-1,tal)
                table_data.append(cabeceras)
                total = 0
                for item in datos:
                    itm = tuple(item.values())
                    tal = [i.replace("MM","M").replace("SS",'S').replace("LL",'L') for i in  item['talla']]
                    index = [tallas.index(i) for i in tal]
                    stk = item['stock']
                    lineas = [
                        Paragraph(itm[0], normal_style),
                        Paragraph(itm[1], normal_style),
                        
                    ]+[Paragraph('', normal_style) for i in tallas]
                
                    for i,j in zip(index,stk):
                        lineas[i+2] = Paragraph(str(j),normal_style)
                    t = sum([int(i) for i in stk])
                    lineas.append(Paragraph(str(t),normal_style))
                    table_data.append(lineas)
                    total+=t
                sum_stock = ['']*len(cabeceras)
                sum_stock[-1] = Paragraph(str(total),normal_style)
                sum_stock[1] = Paragraph('TOTAL',normal_style)
                table_data.append(sum_stock)
                w,h = A4
                col_width = [w*0.11,w*0.32]+[w*0.5/len(tallas) for i in tallas]+[w*0.07]
                table = Table(table_data,colWidths=col_width,repeatRows=1)    
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), (0.7, 0.7, 0.7)),
                    ('TEXTCOLOR', (0, 0), (-1, 0), (1, 1, 1)),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), (1, 1, 1))
                ]))
                story.append(table)
                story.append(Spacer(1,12))
        
            story.append(PageBreak())
            doc.build(story)
            user = request.data['user']
            ruta = os.path.join(settings.BASE_DIR,'media',f'archivo{cred["ruc"]}-{user["cod"]}-{user["codigo"]}.pdf')
            with open(ruta, 'wb') as file:
                file.write(buffer.getvalue())
            res['success'] = "success"
        except Exception as e:
            res['error'] = f"Ocurrio un error: {str(e)}"
        return Response(res)

class PDFGENERATEView(generics.GenericAPIView):
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
            user = request.data['user']
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
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
            buffer.seek(0)
            ruta = os.path.join(settings.BASE_DIR,'media',f'archivo{cred["ruc"]}-{user["cod"]}-{user["codigo"]}.pdf')
            with open(ruta, 'wb') as file:
                file.write(buffer.getvalue())
            res['success'] = "success"
        except Exception as e:
            res['error'] = f'Ocurrio un error: f{str(e)}'
            
        return Response(res)
class  LetraUbicacion(generics.GenericAPIView):
    def post(self,request,*args,**kwargs):
        self.datos = request.data
        self.credencial = Credencial(self.datos['credencial'])
        self.fecha = datetime.now()
        sql = f"""SELECT 
                    b.AUX_RAZON,
                    a.MOV_DOCUM,
                    a.mov_femisi,
                    a.MOV_FVENC,
                    a.MOV_MONED,
                    a.MOV_H_D,
                    a.fac_docref
                FROM mova{self.fecha.year} AS a
                LEFT JOIN t_auxiliar AS b ON a.AUX_CLAVE=b.AUX_CLAVE
                WHERE 
                    a.ven_codigo=?
                    AND (a.ban_codigo=? OR a.ban_codigo=?)
                    AND a.MOV_ELIMIN=0
                    {
                    f" AND a.aux_clave = '{self.datos["cliente"]}' " if self.datos['cliente']!='' else ""
                    }

                """
        params = (self.datos['vendedor'],self.datos['banco1'],self.datos['banco2'])
        s,res = CAQ.request(self.credencial,sql,params,"get",1)

        data = [[item[0].strip(),item[1].strip(),item[2].strftime('%d/%m/%Y'),item[3].strftime('%d/%m/%Y'),item[4].strip(),f"{float(item[5]):,.2f}",item[6].strip()] for item in res]
        def pie_pagina(canvas:Canvas,nombre):
          
            canvas.saveState()
            style = getSampleStyleSheet()

            razon_social = ParagraphStyle(name="aline",alignment=TA_LEFT,parent=style["Normal"])
            razon_social = Paragraph(self.datos['credencial']["razon_social"],style=razon_social)
            razon_social.wrap(nombre.width,nombre.topMargin)
            razon_social.drawOn(canvas,nombre.leftMargin,750)

            user = ParagraphStyle(name="aline",alignment=TA_LEFT,parent=style["Normal"])
            user = Paragraph(f"USUARIO:{self.datos['user']}",style=user)
            user.wrap(nombre.width,nombre.topMargin)
            user.drawOn(canvas,nombre.leftMargin,735)

            fecha = ParagraphStyle(name="aline",alignment=TA_RIGHT,parent=style["Normal"])
            fecha = Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y')}",style=fecha)
            fecha.wrap(nombre.width,nombre.topMargin)
            fecha.drawOn(canvas,nombre.leftMargin,750)

            hora = ParagraphStyle(name="aline",alignment=TA_RIGHT,parent=style["Normal"])
            hora = Paragraph(f"Hora: {datetime.now().strftime('%H:%M:%S')}",style=hora)
            hora.wrap(nombre.width,nombre.topMargin)
            hora.drawOn(canvas,nombre.leftMargin,735)

            hora = ParagraphStyle(name="aline",alignment=TA_CENTER,parent=style["Normal"])
            hora = Paragraph(f"UBICACION DE LETRAS(CLIENTES) ",style=hora)
            hora.wrap(nombre.width,nombre.topMargin)
            hora.drawOn(canvas,60,735)
            canvas.restoreState()
        header = ["Cliente","Letra","E/Emision","F/Vencim.","Moneda","Monto","Referencia"]
        response = HttpResponse(content_type="application/pdf")
        response['Content-Disposition'] = 'attachment;filename="REPORTE.pdf"'
        file = CustomPDF(response,"richard",header,data,custom_header=pie_pagina)
        file.generate()
        return response
        # except Exception as e:
        #     return Response({"error":str(e)})