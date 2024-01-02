from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus.flowables import PageBreak
import base64
import io
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from apirest.querys import Querys
from datetime import datetime
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
        dates = Querys(kwargs).querys(sql,(kwargs['codigo'],),'get',0)
        
        story.append(Paragraph("DEMO DENINM ART", style_heading))
        story.append(Spacer(1, 12))
        numero_pedido = Paragraph(f"NUMERO PEDIDO: {self.kwargs['codigo']}",custom_style)
        story.append(numero_pedido)
        fecha = Paragraph(f"EMISION: {dates[0].strftime('%d/%m/%Y')}",custom_style)
        story.append(fecha)
        cliente = Paragraph(f"CLIENTE: {dates[1].strip()}",custom_style)
        story.append(cliente)
        direccion = Paragraph(f"DIRECCION: {dates[2].strip()}",custom_style)
        story.append(direccion)
        documento = Paragraph(f"DOCUMENTO: {dates[3].strip()}",custom_style)
        story.append(documento)
        vendedor = Paragraph(f"VENDEDOR: {dates[4].strip()}",custom_style)
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
        obs = Paragraph(f"Observacion: {dates[5].strip()}")
    
        story.append(obs)
        moneda = 'S/ ' if 'S' == dates[11].strip() else '$'
        data = [
            ['CARGO','MONEDA',"MONTO"],
            ['SUBTOTAL',moneda,round(dates[9], 2)],
            ['DESCUENTO',moneda,round(dates[6], 2)],
            ['BASE IMPONIBLE',moneda,round(dates[8], 2)],
            [f'IGV {dates[12]:.0f}%',moneda,round(dates[7], 2)],
            ['TOTAL VENTA',moneda,round(dates[10], 2)],

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
        return Response({"pdf":base64.b64encode(pdf).decode('utf-8')})
class PedidoWithQr(GenericAPIView):
    def get(self,request,*args,**kwargs):
        data = {}
        try:
            sql = "SELECT*FROM t_articulo WHERE ART_CODIGO=?"
            params = ()
            result = Querys(kwargs).querys(sql,params,'get',1)
            data = {}
        except Exception as e:
            data['error'] = f"Ocurrio un error: {str(e)}"
        return Response()
class PrecioProduct(GenericAPIView):
    def get(self,request,*args,**kwargs):
        data = {}
        p = '' if kwargs['precio'] =='01' else int(kwargs['precio'])
        moneda = kwargs['moneda']
        codigo = kwargs['codigo']
        try:
            sql = f"""
                SELECT a.lis_pmino{p},a.lis_moneda,a.lis_mindes,a.lis_maxdes,b.art_peso
            FROM maelista AS a LEFT JOIN t_articulo AS b ON a.art_codigo = b.ART_CODIGO
            WHERE cast(GETDATE() AS date) 
            BETWEEN cast(a.lis_fini AS date) AND cast(a.lis_ffin AS date) 
            AND a.lis_tipo IN (1,0) 
            AND a.lis_moneda=?
            AND a.art_codigo=?
            """
            params = (moneda,codigo)
            result = Querys(kwargs).querys(sql,params,'get',0)
            if result is None:
                data['error'] = 'El articulo no tiene precio'
                return Response(data)
            data = {
                'precio':round(result[0],2),
                'moneda':result[1].strip(),
                'des_min':result[2],
                'des_max':result[3],
                'peso':round(result[4],2)
            }
        except Exception as e:
            data['error'] = f'Ocurrio un error: {str(e)}'
        return Response(data)
class NotaPedido(GenericAPIView):
    def get(self,resquest,*args,**kwargs):
        data = {}
        try:
            sql = f"""
                SELECT par_moneda FROM t_parrametro WHERE par_anyo = {datetime.now().year}
                """
            result = Querys(kwargs).querys(sql,(),'get',0)
            data = {
                'moneda':result[0].strip()
            }
        except Exception as e:
            data['error'] = f"Ocurrio un error : {str(e)}"
        return Response(data)
class GuardarPedido(GenericAPIView):
    def post(self,request,*args,**kwargs):
        data = {}
        try:
            datos = request.data
            status,message = self.validar_stock()
            if not status:
                data['error'] = message['error']
                return Response(data)
            if datos['codigo_pedido']!='x':
                return self.data_update()
            sql = "SELECT emp_inclu from t_empresa"
            gui_inclu = Querys(kwargs).querys(sql,(),'get',0)
            total1 = float(datos['total'])
            total=0
            base_impo=0
            if int(gui_inclu[0])==1:
                total = total1
                base_impo = round(float(total)/1.18,2)
            else:
                base_impo= total1
                total = round(float(base_impo)*1.18,2)
            igv=round(total-base_impo,2)
            
        
            sql = " SELECT TOP 1 MOV_COMPRO FROM cabepedido WHERE SUBSTRING(mov_compro,1,3)=? ORDER BY MOV_COMPRO DESC"
            params = (datos['vendedor']['codigo'],)
            result = Querys(kwargs).querys(sql,params,'get',0)
            cor = str(datos['vendedor']['codigo'])+'-'+str(int(result[0].split('-')[-1])+1).zfill(7)
        
            sql = f"SELECT ope_codigo FROM t_parrametro WHERE par_anyo={datetime.now().year}"
           
            ope_codigo = Querys(kwargs).querys(sql,(),'get',0)        
            fecha = datetime.now().strftime('%Y-%m-%d')
            
            params = (cor,fecha,datos['cabeceras']['codigo'],'S', datos['vendedor']['cod'],datetime.now().strftime('%Y-%m-%d %H:%M:%S'),\
                    total,1,datos['local'],datos['tipo'],datos['cabeceras']['direccion'],datos['precio'],datos['vendedor']['codigo'],\
                    str(ope_codigo[0]).strip(),datos['almacen'],datos['cabeceras']['ruc'],datos['obs'],18,igv,base_impo,\
                    gui_inclu[0],'','',datos['tipo_venta'],'F1',0,0,0,0,0,0,datos['agencia'],'',datos['sucursal'],'',datos['nombre'],datos['direccion'],round(self.sumaSDesc(datos['detalle']),2),\
                    abs(round(total1-self.sumaSDesc(datos['detalle']),2)),datos['tipo_envio'])
            sql = """INSERT INTO cabepedido (MOV_COMPRO,MOV_FECHA,MOV_CODAUX,MOV_MONEDA,USUARIO,FECHAUSU,ROU_TVENTA,
            rou_export,ubi_codigo,pag_codigo,gui_direc,lis_codigo,ven_codigo,ope_codigo,ubi_codig2,gui_ruc,
            gui_exp001,ROU_PIGV,ROU_IGV,ROU_BRUTO,gui_inclu,mov_cotiza,aux_nuevo,ped_tipven,doc_codigo,
            gui_aprot1,gui_aprot2,gui_aprot3,gui_aprov1,gui_aprov2,gui_aproc1,tra_codig2,agr_codigo,gui_tienda,
            edp_codigo,gui_tiedir,ped_tiedir,rou_submon,rou_dscto,ped_tipenv) VALUES"""+'('+ ','.join('?' for i in params)+')'
        

            res = Querys(kwargs).querys(sql,params,'post')
           
            if 'error' in res:
                data['error'] = 'Ocurrio un error en la grabacion'
                return Response(data)
            sql1 = """INSERT movipedido (ALM_CODIGO,MOM_MES,mov_compro,MOM_FECHA,ART_CODIGO,col_codigo,tal_codigo,MOM_TIPMOV,
                ope_codigo,MOM_CANT,mom_valor,MOM_PUNIT,USUARIO,FECHAUSU,art_afecto,mom_dscto1,gui_inclu,
                mom_conpre,mom_peso,MOM_PUNIT2,doc_codigo,ped_priori,mom_linea,ped_observ,mom_conpro,mom_conreg,
                mom_confle,mom_cofleg,mom_concom,mom_concoa,mom_conpr2,art_codadi,mom_lote,mom_bruto) VALUES
                """
        
            for item in datos['detalle']:
                mom_conpre = 'K' if item['lista_precio'] =='02' else ('U' if item['lista_precio']=='01' else '')
                mom_bruto = float(item['peso'])*int(item['cantidad']) if mom_conpre!= '' else 0
                talla = item['talla'] if item['talla'] !='x' else ''
                
                params = ('53',str(fecha).split('-')[1],cor,fecha,item['codigo'],'',talla,'S',str(ope_codigo[0]).strip(),float(item['cantidad']),float(item['total']),float(item['precio']),\
                        datos['vendedor']['cod'],fecha,'S',float(item['descuento']),gui_inclu[0],mom_conpre,float(item['peso']),float(item['precio_parcial']),'F1','',0,'',0,0,0,0,0,0,0,'','',mom_bruto) 

                sql = sql1+'('+ ','.join('?' for i in range(len(params)))+')'
            
                res = Querys(kwargs).querys(sql,params,'post')
              
                if 'error' in res:
                    data['error'] = 'Ocurrio un error en la grabacion'
                    return Response(data)
                data['success'] = 'El pedido se guardo con exito'
        except Exception as e:
            print(str(e),'agregando nuevo pedido')
            data['error'] = 'Ocurrio un error a grabar el pedido'
        return Response(data)
    def data_update(self,):
        data = {}
        try:
            datos = self.request.data
            sql = "DELETE FROM cabepedido WHERE MOV_COMPRO=?"
            Querys(self.kwargs).querys(sql,(datos['codigo_pedido'],),'post')
            sql = "DELETE FROM movipedido WHERE mov_compro=?"
            Querys(self.kwargs).querys(sql,(datos['codigo_pedido'],),'post')
            total=0
            base_impo=0
            if int(datos['gui_inclu'])==1:
                total = float(datos['total'])
                base_impo = round(float(total)/1.18,2)
            else:
                base_impo= float(datos['total'])
                total = round(float(base_impo)*1.18,2)
            igv=round(float(total)-float(base_impo),2)
            sql = f"SELECT ope_codigo FROM t_parrametro WHERE par_anyo={datetime.now().year}"
            ope_codigo = Querys(self.kwargs).querys(sql,(),'get',0) 
            params = (datos['codigo_pedido'],datetime.now().strftime('%Y-%m-%d'),datos['cabeceras']['codigo'],'S',\
                    datos['codigo_usuario'],datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),\
                        total,1,datos['local'],datos['tipo'],datos['cabeceras']['direccion'],datos['precio'],datos['codigo_usuario'],\
                        str(ope_codigo[0]).strip(),datos['almacen'],datos['cabeceras']['ruc'],datos['obs'],18,igv,base_impo,\
                        datos['gui_inclu'],datos['tipo_venta'],'F1',0,0,0,0,0,0,datos['agencia'],datos['sucursal'],datos['direccion'],datos['nombre'],round(self.sumaSDesc(datos['detalle']),2),\
                        round(abs(float(datos['total'])-self.sumaSDesc(datos['detalle'])),2),datos['tipo_envio'])
            sql = """INSERT INTO cabepedido 
                (MOV_COMPRO,MOV_FECHA,MOV_CODAUX,MOV_MONEDA,USUARIO,FECHAUSU,ROU_TVENTA,
                rou_export,ubi_codigo,pag_codigo,gui_direc,lis_codigo,ven_codigo,ope_codigo,ubi_codig2,gui_ruc,
                gui_exp001,ROU_PIGV,ROU_IGV,ROU_BRUTO,gui_inclu,ped_tipven,doc_codigo,
                gui_aprot1,gui_aprot2,gui_aprot3,gui_aprov1,gui_aprov2,gui_aproc1,tra_codig2,gui_tienda,gui_tiedir,
                ped_tiedir,rou_submon,rou_dscto,ped_tipenv) VALUES"""+'('+ ','.join('?' for i in params)+')'
            
            Querys(self.kwargs).querys(sql,params,'post')
            sql1 = """INSERT INTO movipedido (ALM_CODIGO,MOM_MES,mov_compro,MOM_FECHA,ART_CODIGO,col_codigo,tal_codigo,MOM_TIPMOV,
                ope_codigo,MOM_CANT,mom_valor,MOM_PUNIT,USUARIO,FECHAUSU,art_afecto,mom_dscto1,gui_inclu,
                mom_conpre,mom_peso,MOM_PUNIT2,doc_codigo,ped_priori,mom_linea,ped_observ,mom_conpro,mom_conreg,
                mom_confle,mom_cofleg,mom_concom,mom_concoa,mom_conpr2,art_codadi,mom_lote,mom_bruto) VALUES
                """
        
            for item in datos['detalle']:
                mom_conpre = 'K' if item['lista_precio'] =='02' else ('U' if item['lista_precio']=='01' else '')
                mom_bruto = float(item['peso'])*int(item['cantidad']) if mom_conpre!= '' else 0
                talla = item['talla'] if item['talla'] !='x' else ''
                params = ('53',datetime.now().month,datos['codigo_pedido'],datetime.now().strftime('%Y-%m-%d'),item['codigo'],'',talla,'S','04',float(item['cantidad']),float(item['total']),float(item['precio']),\
                            datos['codigo_usuario'],datetime.now().strftime('%Y-%m-%d'),'S',float(item['descuento']),datos['gui_inclu'],mom_conpre,item['peso'],float(item['precio_parcial']),'F1','',0,'',0,0,0,0,0,0,0,'','',mom_bruto) 
                sql = sql1+'('+ ','.join('?' for i in range(len(params)))+')'
            
                Querys(self.kwargs).querys(sql,params,'post') 
            data['success'] = f'El pedido {datos["codigo_pedido"]} fue editado exitosamente'    
        except Exception as e:
            print(str(e),'edicion de pedido')
            data['error'] = 'Ocurrio un error en la edicion del pedido'
        return Response(data)
    def sumaSDesc(self,datos):
        total = 0
        
        for item in datos:
            total+=float(item['cantidad'])*float(item['precio'])
        
        return total
    def validar_stock(self):
        data = {}
        try:
            datos = self.request.data
            
            articulos = datos['detalle']
            numero_pedido = datos['codigo_pedido']
            for item in articulos:
                
                stock_real = self.stock_real(item['talla'],item['codigo'],datos['almacen'],datos['local'])[0]
               
                pedidos_pendientes = self.pedidos_pendientes(item['codigo'],item['talla'],datos['local'],datos['almacen'],numero_pedido)[0]
             
                pedidos_aprobados = self.pedidos_aprobados(item['talla'],item['codigo'],datos['local'],datos['almacen'])[0]
                
                stock_disponible = int(stock_real)-int(item['cantidad'])-int(pedidos_aprobados)-int(pedidos_pendientes)
       
                if stock_disponible<0:
                    data['error'] = f'El articulo {item["nombre"]} {item["talla"]} no tiene stock \nStock disponible : {stock_disponible}'
                    return False,data
            return True,''
        except Exception as e:
            print(str(e),'validacion de estok')
            data['error'] = "ocurrio un error "
            return False,data

    def stock_real(self,talla,codigo,almacen,ubicacion):
        data = {}
        try:
            sql = f"""
                SELECT 'mom_cant' = ISNULL(
                    SUM(
                        CASE
                            WHEN mom_tipmov = 'E' THEN mom_cant
                            WHEN mom_tipmov = 'S' THEN mom_cant * -1
                        END
                    ), 0
                ) 
                FROM movm{datetime.now().year} 
                WHERE elimini = 0 
                    AND art_codigo = ?
                    AND ALM_CODIGO = ?
                    AND UBI_COD1 = ? 
                    {'AND tal_codigo=?'if talla!='x' else ''}
                """
            if talla=='x':
                params = (codigo,almacen,ubicacion)
            else:
                params = (codigo,almacen,ubicacion,talla)
            data = Querys(self.kwargs).querys(sql,params,'get',0)
        except Exception as e:
            print(str(e))
            data['error'] = 'error'
        return data
    def pedidos_pendientes(self,codigo,talla,ubicacion,almacen,numero_pedido):
        anio = datetime.now().year
        data = {}
        try:
            sql = f"""
                    SELECT 'mom_cant' = ISNULL(SUM(zzz.mom_cant), 0)
                    FROM (
                        SELECT 'mom_cant' = ISNULL(SUM(a.MOM_CANT), 0) + (
                            SELECT ISNULL(SUM(
                                    CASE
                                        WHEN z.mov_pedido = '' THEN 0
                                        WHEN z.mom_tipmov = 'E' THEN z.mom_cant
                                        ELSE -z.mom_cant
                                    END
                                ), 0)
                            FROM movm{anio} z
                            LEFT JOIN cabepedido zz ON z.mov_pedido = zz.mov_compro
                            WHERE b.mov_compro = z.mov_pedido
                                AND a.art_codigo = z.art_codigo
                                AND a.tal_codigo = z.tal_codigo
                                AND b.ubi_codig2 = z.alm_codigo
                                AND b.ubi_codigo = z.ubi_cod1
                                AND z.elimini = 0
                                AND zz.elimini = 0
                                AND zz.ped_cierre = 0
                                { 'AND b.mov_compro <> ?' if numero_pedido!='x' else ''}

                        )
                        FROM movipedido a
                        INNER JOIN cabepedido b ON a.mov_compro = b.MOV_COMPRO
                        WHERE a.art_codigo = ?
                            AND b.ubi_codig2 = ?
                            AND b.ubi_codigo = ?
                            { 'AND tal_codigo = ?' if talla!='x' else ''}
                            { 'AND b.mov_compro <> ?' if numero_pedido!='x' else ''}
                            AND a.elimini = 0
                            AND b.ped_status IN (0, 1)
                            AND ped_statu2 IN (0, 1)
                            AND b.ped_cierre = 0
                        GROUP BY b.mov_compro, a.art_codigo, a.tal_codigo, b.ubi_codig2, b.ubi_codigo
                    ) AS zzz;

                    """
            if talla!='x' and numero_pedido!='x':
                params = (numero_pedido,codigo,almacen,ubicacion,talla,numero_pedido)
            elif talla!='x' and numero_pedido=='x':
                params = (codigo,almacen,ubicacion,talla)
            elif talla=='x' and numero_pedido!='x':
                params = (numero_pedido,codigo,almacen,ubicacion,numero_pedido)
            elif talla == 'x' and numero_pedido =='x':
                params = (codigo,almacen,ubicacion)
            data = Querys(self.kwargs).querys(sql,params,'get',0)   
        except Exception as e:
            data['error'] = 'error'
        return data
    def pedidos_aprobados(self,talla,codigo,ubicacion,almacen):
        data = {}
        anio = datetime.now().year
        try:
            sql = f"""
                SELECT 'mom_cant' = ISNULL(
                    SUM(zzz.mom_cant), 0
                )
                FROM (
                    SELECT 'mom_cant' = ISNULL(
                            SUM(a.MOM_CANT), 0
                        ) + (
                            SELECT ISNULL(
                                SUM(
                                    CASE
                                        WHEN z.mov_pedido = '' THEN 0
                                        WHEN z.mom_tipmov = 'E' THEN z.mom_cant
                                        ELSE -z.mom_cant
                                    END
                                ), 0
                            )
                            FROM movm{anio} z
                            LEFT JOIN cabepedido zz ON z.mov_pedido = zz.mov_compro
                            WHERE b.mov_compro = z.mov_pedido
                                AND a.art_codigo = z.art_codigo
                                AND a.tal_codigo = z.tal_codigo
                                AND b.ubi_codig2 = z.alm_codigo
                                AND b.ubi_codigo = z.ubi_cod1
                                AND z.elimini = 0
                                AND zz.elimini = 0
                                AND zz.ped_cierre = 0
                        )
                    FROM movipedido a
                    INNER JOIN cabepedido b ON a.mov_compro = b.MOV_COMPRO
                    WHERE a.art_codigo = ?
                        AND b.ubi_codig2 = ?
                        AND b.ubi_codigo = ?
                        {'AND tal_codigo = ?' if talla!='x' else ''}
                        AND a.elimini = 0
                        AND b.ped_status = 2
                        AND ped_statu2 = 2
                        AND b.ped_cierre = 0
                    GROUP BY b.mov_compro, a.art_codigo, a.tal_codigo, b.ubi_codig2, b.ubi_codigo
                ) AS zzz;

                """
            if talla!='x':
                params = (codigo,ubicacion,almacen,talla)
            else:
                params = (codigo,ubicacion,almacen)
            data = Querys(self.kwargs).querys(sql,params,'get',0)
        except Exception as e:
            print(str(e))
            data['error'] = 'error'
        return data
        
class EditPedido(GenericAPIView):
    def get(self,request,*args,**kwargs):
        data = {}
        try:
            sql = """SELECT 
                        a.MOV_CODAUX, a.gui_ruc, a.gui_direc, b.AUX_NOMBRE,
                        a.ubi_codig2,a.ubi_codigo,a.lis_codigo,a.MOV_MONEDA,
                        a.gui_exp001,a.gui_inclu,
                        a.ped_tipven,a.tra_codig2,a.gui_tienda,a.gui_tiedir,a.ped_tiedir,
                       a.pag_codigo,a.ped_tipenv,'agencia'=(SELECT tra_nombre FROM t_transporte WHERE TRA_CODIGO=a.tra_codig2 )
                        FROM cabepedido AS a
                        INNER JOIN t_auxiliar AS b ON a.MOV_CODAUX = b.AUX_CLAVE
                        WHERE a.MOV_COMPRO = ? """
            result = Querys(kwargs).querys(sql,(kwargs['codigo'],),'get',0)
            data['cabecera'] = {
                'cliente':{
                    'codigo':result[0].strip(),
                    'ruc':result[1].strip(),
                    'direccion':result[2].strip(),
                    'razon_social':result[3].strip()
                },
                'notapedido':{
                    'almacen':result[4].strip(),
                    'ubicacion':result[5].strip(),
                    'lista_precio':result[6].strip(),
                    'moneda':result[7].strip(),
                },
                'final':{
                    'obs':result[8].strip(),
                    'gui_inclu':int(result[9]),
                    'tipo_venta':int(result[10]),
                    'agencia_codigo':result[11].strip(),
                    'agencia_nombre':result[17].strip(),
                    'entrega_codigo':result[12].strip(),
                    'entrega_nombre':result[13].strip(),
                    'entrega_direccion':result[14].strip(),
                    'tipo_pago':result[15].strip(),
                    'tipo_envio':int(result[16]),

                }
            }
        except Exception as e:
            print(str(e))
            data['error'] = 'Sucedio un error al recuperar los datos'
        return Response(data)
