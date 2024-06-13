from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus.flowables import PageBreak
import base64
import io
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from apirest.credenciales import Credencial
from apirest.querys import CAQ, Querys
from datetime import datetime
from apirest.view.apis.views import TipoCambio
from dataclasses import dataclass
from apirest.view.pdf.views import PDF
import logging

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
class PdfPedidoView(GenericAPIView):
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
    def post(self,request,*args,**kwargs):
        data = {}
        datos = request.data
        self.credencial = Credencial(datos['credencial'])
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
            s,result = CAQ.request(self.credencial,sql,(datos['numero_pedido'],),'get',0)
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
                        a.mom_dscto1
                    FROM movipedido AS a 
                    INNER JOIN t_articulo AS b ON a.ART_CODIGO=b.art_CODIGO WHERE MOV_COMPRO=?
                    ORDER BY b.ART_NOMBRE"""
            s,result = CAQ.request(self.credencial,sql,(datos['numero_pedido'],),'get',1)
            if not s:
                raise Exception('Error al consultar a la base de datos')
            data['pdf'] = PDF(empresa,cabecera,self.items(result)).generate()
        except Exception as e:
            data['error'] = str(e)
        return Response(data)
    def items(self,detalle):
        data = []
        for item in detalle:
            d = {
                'codigo':item[0].strip(),
                'cantidad':float(item[1]),
                'precio':float(item[2]),
                'nombre':item[3].strip(),
                'subtotal':float(item[4]),
                'descuento':float(item[5])
            }
            data.append(d)
        return data


      
    def get(self,request,*args,**kwargs):
        try:
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
            
            story.append(Paragraph(f"{kwargs['empresa']}", style_heading))
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
        except Exception as e :
            print(str(e))
            return Response({'error':'No se puede generar el pdf'})
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
class Moneda(GenericAPIView):
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
    credencial = None
    message = 'El pedido se guardo con exito'
    bk_message = 'NUEVO(APPV1)'
    anio = datetime.now().year
    def post(self,request,*args,**kwargs):
        data = {}
        datos = request.data
        self.credencial = Credencial(datos['credencial'])
        try:
            if datos['config']['separacion_pedido']:
                status,message = self.validar_stock()
                if not status:
                    data['error'] = message['error']
                    return Response(data)
            if datos['credencial']['codigo']=='3':
                s,msg = self.validar_linea_credito()
                if not s:
                    data['error'] = msg
                    return Response(data)
            if datos['codigo_pedido']!='x':
                self.data_update()
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
            if result is None:
                result = ['1']
            cor = str(datos['vendedor']['codigo'])+'-'+str(int(result[0].split('-')[-1])+1).zfill(7)
            if datos['codigo_pedido']!='x':
                cor = datos['codigo_pedido']
            sql = f"SELECT ope_codigo FROM t_parrametro WHERE par_anyo={datetime.now().year}"
           
            ope_codigo = Querys(kwargs).querys(sql,(),'get',0)        
            fecha = datetime.now().strftime('%Y-%m-%d')
            codigo_vendedor = self.validar_vendedor()
            
            params = (cor,fecha,datos['cabeceras']['codigo'],datos['moneda'], datos['vendedor']['cod'],datetime.now().strftime('%Y-%m-%d %H:%M:%S'),\
                    total,1,datos['ubicacion'],datos['tipo_pago'],datos['cabeceras']['direccion'],datos['precio'],codigo_vendedor,\
                    str(ope_codigo[0]).strip(),datos['almacen'],datos['cabeceras']['ruc'],datos['obs'],18,igv,base_impo,\
                    gui_inclu[0],datos['tipo_venta'],'F1',0,0,0,0,0,0,datos['agencia'],datos['sucursal'],datos['nombre'],datos['direccion'],round(self.sumaSDesc(datos['detalle']),2),\
                    abs(round(total1-self.sumaSDesc(datos['detalle']),2)),datos['tipo_envio'])
            sql = """INSERT INTO cabepedido (MOV_COMPRO,MOV_FECHA,MOV_CODAUX,MOV_MONEDA,USUARIO,FECHAUSU,ROU_TVENTA,
            rou_export,ubi_codigo,pag_codigo,gui_direc,lis_codigo,ven_codigo,ope_codigo,ubi_codig2,gui_ruc,
            gui_exp001,ROU_PIGV,ROU_IGV,ROU_BRUTO,gui_inclu,ped_tipven,doc_codigo,
            gui_aprot1,gui_aprot2,gui_aprot3,gui_aprov1,gui_aprov2,gui_aproc1,tra_codig2,gui_tienda,
            gui_tiedir,ped_tiedir,rou_submon,rou_dscto,ped_tipenv) VALUES"""+'('+ ','.join('?' for i in params)+')'
        

            res = Querys(kwargs).querys(sql,params,'post')
          
            if 'error' in res:
                data['error'] = 'Ocurrio un error en la grabacion'
                return Response(data)
        
            res = self.auditoria_cabepedido(params,self.bk_message)
            if 'error' in res:
                data['error'] = 'Ocurrio un error al grabar el pedido'
                return Response(data)
            sql1 = """INSERT movipedido (ALM_CODIGO,MOM_MES,mov_compro,MOM_FECHA,ART_CODIGO,tal_codigo,MOM_TIPMOV,
                ope_codigo,MOM_CANT,mom_valor,MOM_PUNIT,USUARIO,FECHAUSU,art_afecto,mom_dscto1,gui_inclu,
                mom_conpre,mom_peso,MOM_PUNIT2,doc_codigo,mom_linea,mom_conpro,mom_conreg,
                mom_confle,mom_cofleg,mom_concom,mom_concoa,mom_conpr2,mom_bruto,mom_lote,art_codadi) VALUES
                """

            for item in datos['detalle']:
                mom_conpre = 'K' if item['lista_precio'] =='02' else ('U' if item['lista_precio']=='01' else '')
                mom_bruto = float(item['peso'])*int(item['cantidad']) if mom_conpre!= '' else 0
                talla = item['talla'] if item['talla'] !='x' else ''
                
                params = ('53',str(fecha).split('-')[1],cor,fecha,item['codigo'],talla,'S',str(ope_codigo[0]).strip(),float(item['cantidad']),float(item['total']),float(item['precio']),\
                        datos['vendedor']['cod'],fecha,'S',float(item['descuento']),gui_inclu[0],mom_conpre,float(item['peso']),float(item['precio_parcial']),'F1',0,0,0,0,0,0,0,0,mom_bruto,item['fecha'],item['lote']) 

                sql = sql1+'('+ ','.join('?' for i in range(len(params)))+')'
            
                res = Querys(kwargs).querys(sql,params,'post')
                if 'error' in res:
                    data['error'] = 'Ocurrio un error en la grabacion'
                    return Response(data)
                res = self.auditoria_movipedido(params,self.bk_message)
                
                if 'error' in res:
                    data['error'] = 'Ocurrio un error el grabar el pedido'
                    return Response(data)
            self.aprobacion_automatica(cor)
            data['success'] = self.message
            
        except Exception as e:
            logger.error('An error occurred: %s', e)
            data['error'] = str(e)
        return Response(data)
    def data_update(self,):
        datos = self.request.data
        sql = "DELETE FROM cabepedido WHERE MOV_COMPRO=?"
        Querys(self.kwargs).querys(sql,(datos['codigo_pedido'],),'post')
        sql = "DELETE FROM movipedido WHERE mov_compro=?"
        Querys(self.kwargs).querys(sql,(datos['codigo_pedido'],),'post')
        self.message = f"El pedido {datos['codigo_pedido']} fue editado exitosamente"
        self.bk_message = 'EDITADO(APPV1)'

    def sumaSDesc(self,datos):
        total = 0
        for item in datos:
            total+=float(item['cantidad'])*float(item['precio'])
        return total
    def aprobacion_automatica(self,numero_pedido):
        if self.request.data['credencial']['codigo'] != '6':
            return
        try:
            datos = self.request.data
            user = datos['vendedor']
            sql = "SELECT usu_apraut FROM t_usuario where usu_codigo=? and ven_codigo=?"
            s,result = CAQ.request(self.credencial,sql,(user['cod'],user['codigo']),'get',0)
            if not s:
                raise Exception("Error al consultar si es vendedor tiene aprobacion automatica")
            if int(result[0]) == 0:
                return
            sql = "UPDATE cabepedido SET ped_status=?,ped_fecapr=?,ped_usuapr=?,ped_statu2=?,ped_usuap2=? WHERE mov_compro=?"
            params = (2,datetime.now(),user['cod'],2,user['cod'],numero_pedido)
            s,_ = CAQ.request(self.credencial,sql,params,'post')
            if not s:
                raise Exception('No se pudo realizar la aprobacion automatica')
        except Exception as e:
            raise Exception(str(e))
    def validar_stock(self):
        data = {}
        try:
            datos = self.request.data
            
            articulos = datos['detalle']
            numero_pedido = datos['codigo_pedido']
            for item in articulos:
                
                stock_real = self.stock_real(item['talla'],item['codigo'],datos['almacen'],datos['ubicacion'],item['lote'],item['fecha'])[0]
               
                pedidos_pendientes = self.pedidos_pendientes(item['codigo'],item['talla'],datos['ubicacion'],datos['almacen'],numero_pedido,item['lote'],item['fecha'])[0]
                pedidos_aprobados = self.pedidos_aprobados(item['talla'],item['codigo'],datos['ubicacion'],datos['almacen'],item['fecha'],item['lote'])[0]
                
                stock_disponible = int(stock_real)-int(item['cantidad'])-int(pedidos_aprobados)-int(pedidos_pendientes)
       
                if stock_disponible<0:
                    data['error'] = f'El articulo {item["nombre"]} {item["talla"]} no tiene stock \nStock disponible : {stock_disponible:.2f}'
                    return False,data
            return True,''
        except Exception as e:
            print(str(e),'validacion de estok')
            data['error'] = "ocurrio un error "
            return False,data
    def stock_real(self,talla,codigo,almacen,ubicacion,lote,fecha):
        data = {}
        fecha = '-'.join(i for i in reversed(fecha.split('/')))
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
                        {
                            f"AND tal_codigo='{talla}' " if talla!='' else ''
                        }

                        {
                            f"AND art_codadi='{lote}' " if lote!='' else ''
                        }
                        {
                            f"AND mom_lote='{fecha}' " if fecha!='' else ''
                        }
                    """
            params = (codigo,almacen,ubicacion)
            data = Querys(self.kwargs).querys(sql,params,'get',0)
        except Exception as e:
           
            data['error'] = 'error'
        return data
    def pedidos_pendientes(self,codigo,talla,ubicacion,almacen,pedido,lote,fecha):
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
                        )
                        FROM movipedido a
                        INNER JOIN cabepedido b ON a.mov_compro = b.MOV_COMPRO
                        WHERE a.art_codigo = ?
                            AND b.ubi_codig2 = ?
                            AND b.ubi_codigo = ?
                            {
                                f"AND b.mov_compro<>'{pedido}' " if pedido!='x' else ''
                            }
                            {
                                f"AND tal_codigo ='{talla}' " if talla!='x' else ''
                            }
                            {
                                f"AND a.mom_lote='{fecha}' " if fecha!='' else ''
                            }
                            {
                                f"AND a.art_codadi='{lote}' " if lote!='' else ''
                            }
                            AND a.elimini = 0
                            AND b.ped_status IN (0, 1)
                            AND ped_statu2 IN (0, 1)
                            AND b.ped_cierre = 0
                        GROUP BY b.mov_compro, a.art_codigo, a.tal_codigo, b.ubi_codig2, b.ubi_codigo
                    ) AS zzz;
                    """
            params = (codigo,almacen,ubicacion)
            data = Querys(self.kwargs).querys(sql,params,'get',0)   
        except Exception as e:
            data['error'] = 'error'
        return data
    def pedidos_aprobados(self,talla,codigo,ubicacion,almacen,fecha,lote):
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
                            {
                                f"AND a.tal_codigo ='{talla}' " if talla!='' else ''
                                
                            }
                            {
                                f"AND a.mom_lote='{fecha}' " if fecha!='' else ''
                                
                            }
                            {
                                f"AND a.art_codadi ='{lote}' " if lote!='' else ''
                                
                            }
                            AND a.elimini = 0
                            AND b.ped_status = 2
                            AND ped_statu2 = 2
                            AND b.ped_cierre = 0
                        GROUP BY b.mov_compro, a.art_codigo, a.tal_codigo, b.ubi_codig2, b.ubi_codigo
                    ) AS zzz;
                """
            params = (codigo,almacen,ubicacion)
            data = Querys(self.kwargs).querys(sql,params,'get',0)
        except Exception as e:
            print(str(e))
            data['error'] = 'error'
        return data
    def validar_vendedor(self):
        codigo_vendedor = ''
        if self.request.data['empresa'] =='3':
            for item in self.request.data['detalle']:
                codigo_vendedor = item['vendedor']
        if codigo_vendedor=='':
            codigo_vendedor = self.request.data['vendedor']['codigo'].strip()
    
            if codigo_vendedor=='':
                raise Exception('El usuario no tiene codigo de vendedor')
        return codigo_vendedor  
    def auditoria_cabepedido(self,params:tuple,state:str):
        parametros = list(params)
        usuario = self.request.data['vendedor']['cod']
        
        fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        parametros.pop(21)
        parametros = (*parametros,usuario,fecha,state)
        sql = f""" INSERT INTO bkcabepedido(MOV_COMPRO,MOV_FECHA,MOV_CODAUX,MOV_MONEDA,USUARIO,FECHAUSU,ROU_TVENTA,
            rou_export,ubi_codigo,pag_codigo,gui_direc,lis_codigo,ven_codigo,ope_codigo,ubi_codig2,gui_ruc,
            gui_exp001,ROU_PIGV,ROU_IGV,ROU_BRUTO,gui_inclu,doc_codigo,
            gui_aprot1,gui_aprot2,gui_aprot3,gui_aprov1,gui_aprov2,gui_aproc1,tra_codig2,gui_tienda,
            gui_tiedir,ped_tiedir,rou_submon,rou_dscto,ped_tipenv,bk_usuario,bk_fecha,bk_observ)
                VALUES({','.join('?' for i in parametros)})"""
        return Querys(self.kwargs).querys(sql,parametros,'post')
    def auditoria_movipedido(self,params,state):
        parametros = list(params)
        parametros.pop(16)#ELMINAR mon_compre
        parametros.pop(16)#ELIMINAR mom_peso
        parametros.pop(16)#ELMINIAR mom_punit2
        usuario = self.request.data['vendedor']['cod']
      
        fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        parametros = (*parametros,usuario,fecha,state)
        sql = f"""
                INSERT INTO bkmovipedido (
                ALM_CODIGO,MOM_MES,mov_compro,MOM_FECHA,ART_CODIGO,tal_codigo,MOM_TIPMOV,
                ope_codigo,MOM_CANT,mom_valor,MOM_PUNIT,USUARIO,FECHAUSU,art_afecto,mom_dscto1,gui_inclu,
                doc_codigo,mom_linea,mom_conpro,mom_conreg,
                mom_confle,mom_cofleg,mom_concom,mom_concoa,mom_conpr2,mom_bruto,mom_lote,art_codadi,bk_usuario,bk_fecha,bk_observ
                ) VALUES({','.join('?' for i in parametros)})
                """
        return Querys(self.kwargs).querys(sql,parametros,'post')
    def validar_linea_credito(self):
        """
        Este metodo solo esta habilitado para algunos clientes
        """
        try:
            datos = self.request.data
            
            sql = "SELECT pag_nvallc FROM t_maepago WHERE pag_codigo=?"
            s,result = CAQ.request(self.credencial,sql,(datos['tipo_pago'],),'get',0)
            
            if int(result[0])==1:
                return True,''
            sql  = """SELECT 
                        aux_limite 
                    FROM t_auxiliar 
                    WHERE 
                        AUX_CLAVE=?"""
            _,result = CAQ.request(self.credencial,sql,(datos['cabeceras']['codigo'],),'get',0)
            linea_credito = float(result[0])
           
            if int(linea_credito)==0:
                return False,'El cliente no tiene linea de credito'
            sql = f"""
                    SELECT 
                        'saldo'=(
                            CASE 
                                WHEN mov_moned='S' THEN SUM(mov_d) 
                                WHEN mov_moned='D' THEN SUM(mov_d_d) 
                                ELSE 0 END
                                )-(
                            CASE 
                            WHEN mov_moned='S' THEN SUM(mov_h) 
                            WHEN mov_moned='D' THEN SUM(mov_h_d) 
                            ELSE 0 END
                            ) 
                    FROM mova{self.anio}
                    WHERE aux_clave=? 
                        AND SUBSTRING(pla_cuenta,1,2)>='12'
                        AND SUBSTRING(pla_cuenta,1,2)<='13' 
                        AND mov_elimin=0 
                    GROUP BY mov_moned"""
            s,result=CAQ.request(self.credencial,sql,(datos['cabeceras']['codigo'],),'get',0)
            
            if not s :
                return False,'Ocurrio un error al consultar por la deuda del cliente'
            if result is None:
                saldo = 0
            else:
                saldo = float(result[0])
            
            total = self.monto_total(datos['detalle'])
         
            if datos['moneda']=='S':
                total = self.conversion(total)
            t = linea_credito-saldo-total
            
            return t>0,f'El pedido ha superado en $ {abs(t):.2f} y el total del pedido es de: $ {total:.2f}'
        except Exception as e:
            print(str(e))
            return False,'Ocurrio un error al validar la linea de credito'
            
    def monto_total(self,datos):
        return sum( float(item['total']) for item in datos)
    def conversion(self,total):
        return self.tipo_cambio()*total
    def tipo_cambio(self):
        sql = f"SELECT tc_venta FROM t_tcambio where TC_FECHA={datetime.now().strftime('%Y-%m-%d')}"
        s,result = CAQ.request(self.credencial,sql,(),'get',0)
        if result is None:
            tipo_cambio = TipoCambio.tipo_cambio()
        else:
            tipo_cambio = result[0]
        return tipo_cambio


class EditPedido(GenericAPIView):
    credencial = None
    def post(self,request,*args,**kwargs):
        data = {}
        datos  = request.data
        self.credencial = Credencial(datos['credencial'])
        try:
            sql = """SELECT 
                        a.MOV_CODAUX, a.gui_ruc, a.gui_direc, b.AUX_NOMBRE,
                        a.ubi_codig2,a.ubi_codigo,a.lis_codigo,a.MOV_MONEDA,
                        a.gui_exp001,a.gui_inclu,
                        a.ped_tipven,a.tra_codig2,a.gui_tienda,a.gui_tiedir,a.ped_tiedir,
                        a.pag_codigo,a.ped_tipenv,'agencia'=ISNULL((SELECT tra_nombre FROM t_transporte WHERE TRA_CODIGO=a.tra_codig2 ),''),
                        b.aux_telef,b.aux_email 
                        FROM cabepedido AS a
                        INNER JOIN t_auxiliar AS b ON a.MOV_CODAUX = b.AUX_CLAVE
                        WHERE a.MOV_COMPRO = ? """
            s,result = CAQ.request(self.credencial,sql,(datos['codigo']),'get',0)
            if not s:
                data['error'] = result['error']
                return Response(data)
            data['cabecera'] = {
                'cliente':{
                    'codigo':result[0].strip(),
                    'ruc':result[1].strip(),
                    'direccion':result[2].strip(),
                    'nombre':result[3].strip(),
                    'telefono':result[18].strip(),
                    'email':result[19].strip()
                },
                
                'almacen':result[4].strip(),
                'ubicacion':result[5].strip(),
                'lista_precio':result[6].strip(),
                'moneda':result[7].strip(),
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
            sql = """ SELECT a.ART_CODIGO, a.MOM_CANT, a.mom_valor, a.MOM_PUNIT, a.mom_dscto1, b.art_nombre,
                        a.tal_codigo,a.mom_peso,a.mom_conpre,a.MOM_PUNIT2,b.ven_codigo,a.art_codadi,a.mom_lote
                        FROM movipedido AS a 
                        INNER JOIN t_articulo AS b ON a.ART_CODIGO = b.art_codigo 
                        WHERE a.mov_compro = ?"""
            s,result = CAQ.request(self.credencial,sql,(datos['codigo'],),'get',1)
            if not s:
                data['error'] = result['error']
                return Response(data)
            data['articulos'] = [
                {
                    "id":index,
                    "codigo":value[0].strip(),
                    "cantidad":value[1],
                    "total":value[2],
                    "precio":value[3],
                    "descuento":value[4],
                    "nombre":value[5].strip(),
                    "talla":value[6].strip(),
                    "peso":value[7],
                    "lista_precio":'',
                    "precio_parcial":value[9],
                    "vendedor":value[10].strip(),
                    "lote":value[11].strip(),
                    "fecha":value[12].strip()
                } for index, value in enumerate(result)
            ]
        except Exception as e:
            print(str(e))
            data['error'] = 'Sucedio un error al recuperar los datos'
        return Response(data)
class ListPedidos(GenericAPIView):
    anio = datetime.now().year
    credencial = None
    def post(self,request,*args,**kwargs):
        data = {}
        try:
            datos = request.datos
            self.credencial = Credencial(datos['credencial'])
            all_items = datos['all_items']
            sql =f"""
                SELECT a.MOV_COMPRO, a.MOV_FECHA,
                ped_status = CASE 
                    WHEN a.elimini = 1 THEN 'ANULADO' 
                    WHEN (a.ped_status = 3 OR a.ped_statu2 = 3) THEN 'RECHAZADO' 
                    WHEN (a.ped_status IN (1, 0) OR a.ped_statu2 IN (1, 0)) THEN 'PENDIENTE' 
                    WHEN (a.ped_status = 2 AND a.ped_statu2 = 2) THEN 'APROBADO' 
                END,
                b.aux_razon, a.ROU_BRUTO, a.ROU_IGV, a.ROU_TVENTA,a.ven_codigo,a.MOV_MONEDA,
                COALESCE((SELECT TRA_NOMBRE FROM t_transporte WHERE TRA_CODIGO = a.tra_codig2), '') AS agencia,
                (SELECT TOP 1 mom_dscto1 FROM movipedido WHERE mov_compro = a.MOV_COMPRO) AS descuento,
                a.gui_exp001
                FROM cabepedido AS a 
                INNER JOIN t_auxiliar AS b ON a.MOV_CODAUX = b.aux_clave 
            {"WHERE a.ped_cierre=0 AND a.elimini=0" if all_items==0 else ''}
                ORDER BY MOV_FECHA DESC, MOV_COMPRO DESC

                """
            params = ()
            s,result = CAQ.request(self.credencial,sql,params,'GET','POST')
            if not s:
                data['error'] = result['error']
                return Response(data)
            data = []
            for index,value in enumerate(result):
                data.append({'id':index,"codigo_pedido":value[0],"fecha":value[1].strftime('%Y-%m-%d'),'status':value[2],"cliente":value[3].strip(),\
                                "subtotal":value[4],"igv":value[5],"total":value[6],'codigo':value[7].strip(),'moneda':value[8].strip(),'agencia':value[9].strip(),
                                'descuento':value[10],'obs':value[11].strip()})
        except Exception as e:
            data['error'] = 'Ocurrio un error el recuperar los pedidos'
        return Response(data)