from django.http import HttpResponse
from rest_framework.response import Response 
from rest_framework import generics
from apirest.credenciales import Credencial
from apirest.querys import CAQ
from apirest.views import QuerysDb
from datetime import datetime
from reportlab.pdfgen.canvas import Canvas
from ..pdf.views import PDFHistorialCliente
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_RIGHT,TA_CENTER,TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak,Table,TableStyle,Spacer

class CuentasView(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        host = kwargs['host']
        bd = kwargs['db']
        user = kwargs['user']
        passsword = kwargs['password']
        filtro = kwargs['filter']
      
        sql1 = f"SELECT tc_venta FROM t_tcambio WHERE tc_fecha='{datetime.now().strftime('%Y-%m-%d')}'"
        
        sql = f"""
        
            SELECT
                a.aux_clave,
                b.aux_razon,
                'fact_s' = SUM(CASE WHEN a.mov_moned = 'S' AND a.DOC_CODIGO <> '50' THEN a.mov_d - a.MOV_H ELSE 0 END),
                'fact_d' = SUM(CASE WHEN a.mov_moned = 'D' AND a.DOC_CODIGO <> '50' THEN a.mov_d_d - a.MOV_H_d ELSE 0 END),
                'letra_s' = SUM(CASE WHEN a.mov_moned = 'S' AND a.DOC_CODIGO = '50' THEN a.mov_d - a.MOV_H ELSE 0 END),
                'letra_d' = SUM(CASE WHEN a.mov_moned = 'D' AND a.DOC_CODIGO = '50' THEN a.mov_d_d - a.MOV_H_d ELSE 0 END),
                'total_s' = SUM(CASE WHEN a.mov_moned = 'S' THEN a.mov_d - a.MOV_H ELSE 0 END),
                'total_d' = SUM(CASE WHEN a.mov_moned = 'D' THEN a.mov_d_d - a.MOV_H_d ELSE 0 END),
                b.aux_limite,
                a.ven_codigo
                
               
            FROM
                MOVA{datetime.now().year} AS a
                INNER JOIN t_auxiliar b ON a.aux_clave = b.aux_clave
            WHERE
                a.mov_fecha <= GETDATE()
                AND a.mov_elimin = 0
                AND SUBSTRING(a.pla_cuenta, 1, 2) >= '12'
                AND SUBSTRING(a.pla_cuenta, 1, 2) <= '13'
                
            
            GROUP BY
                a.aux_clave,
                b.aux_razon,
                b.aux_limite,
                a.ven_codigo
              
            {
                '''HAVING
                SUM(CASE WHEN a.mov_moned = 'S' AND a.DOC_CODIGO <> '50' THEN a.mov_d - a.MOV_H ELSE 0 END) <> 0
                OR SUM(CASE WHEN a.mov_moned = 'D' AND a.DOC_CODIGO <> '50' THEN a.mov_d_d - a.MOV_H_d ELSE 0 END) <> 0
                OR SUM(CASE WHEN a.mov_moned = 'S' AND a.DOC_CODIGO = '50' THEN a.mov_d - a.MOV_H ELSE 0 END) <> 0
                OR SUM(CASE WHEN a.mov_moned = 'D' AND a.DOC_CODIGO = '50' THEN a.mov_d_d - a.MOV_H_d ELSE 0 END) <> 0
                OR SUM(CASE WHEN a.mov_moned = 'S' THEN a.mov_d - a.MOV_H ELSE 0 END) <> 0
                OR SUM(CASE WHEN a.mov_moned = 'D' THEN a.mov_d_d - a.MOV_H_d ELSE 0 END) <> 0'''
                if filtro==0 else ''}
            
            ORDER BY
                b.aux_razon;

            """
      
        data = {}
        try:
            conn = QuerysDb.conexion(host,bd,user,passsword)
            result = self.querys(conn,sql,(),'get')
   
            tipo_cambio = self.querys(conn,sql1,(),'get')[0][0]
            data = [
                {
                    'id':index,
                    'codigo':value[0].strip(),
                    'razon_social':value[1].strip(),
                    'monto_soles':f"{value[2]:,.2f}",
                    'monto_dolares':f"{value[3]:,.2f}",
                    'letra_soles':f"{value[4]:,.2f}",
                    'letra_dolares':f"{value[5]:,.2f}",
                    'total_soles':f"{value[6]:,.2f}",
                    'total_dolares':f"{value[7]:,.2f}", #Formateo de la
                    'filtro':filtro,
                    "linea_credito":float(value[8]),
                    "saldo_dolares":f"{self.saldo(value[6],value[7],value[8],tipo_cambio):,.2f}",
                    "saldo_soles":f"{self.saldo(value[6],value[7],value[8],tipo_cambio)*tipo_cambio:,.2f}",
                    "usuario":value[9].strip()
                    
                }    for index,value in enumerate(result)]
        
            conn.commit()
            conn.close()
        except Exception as e:
      
            data['error'] = 'Ocurrio un error al recuperar las cuentas'
        return Response(data)
    def saldo(self,soles,dolares,linea,tipo_cambio):
        return round(linea-(soles/tipo_cambio+dolares),2)
    def querys(self,conn,sql,params,request):
        cursor = conn.cursor()
        cursor.execute(sql,params)
        if request=='get':
            data = cursor.fetchall()
        elif request == "post":
            data = 'succes'
               
        return data
class ReadCuentasView(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        host = kwargs['host']
        bd = kwargs['db']
        user = kwargs['user']
        passsword = kwargs['password']
        codigo = kwargs['codigo']
        filtro = kwargs['filter']
        self.fecha = datetime.now()
    
        sql = f"""
            SELECT
                b.ven_codigo,
                a.DOC_NOMBRE,
				a.mvc_serie,
				a.mvc_docum,
				a.MOV_MONED,
				a.mvc_debe,
				a.mvc_haber,
                'mvc_debes' = a.mvc_debe - a.mvc_haber,
                b.mov_femisi,
                b.MOV_FVENC,
                a.ban_nombre
        
            FROM (
                SELECT
                    'DOC_NOMBRE' = COALESCE(b.DOC_NOMBRE, a.DOC_CODIGO),
                    'mvc_serie' = COALESCE(a.mov_serie, ''),
                    'mvc_docum' = a.mov_docum,
                    a.mov_moned,
                    'mvc_debe' = SUM(CASE WHEN a.mov_moned = 'S' THEN a.mov_d ELSE a.mov_d_d END),
                    'mvc_haber' = SUM(CASE WHEN a.mov_moned = 'S' THEN a.mov_h ELSE a.mov_h_d END),
                    'ban_nombre' = ISNULL((SELECT TOP 1 ban_nombre FROM mova{self.fecha.year} AS n WHERE n.mov_docum = a.mov_docum AND n.ori_codigo<>'00' ORDER BY n.mov_fecha DESC ),'')
                FROM
                    MOVA{self.fecha.year} a
                    LEFT JOIN t_documento b ON a.DOC_CODIGO = b.DOC_CODIGO AND a.MOV_SERIE = b.doc_serie
                WHERE
                    a.aux_clave = ?
                    AND SUBSTRING(a.pla_cuenta, 1, 2) >= '12'
                    AND SUBSTRING(a.pla_cuenta, 1, 2) <= '13'
                    AND a.mov_fecha <= GETDATE()
                    AND a.mov_elimin = 0
                    AND (a.mov_moned = 'D' AND a.mov_d_d + a.mov_h_d <> 0 OR a.mov_moned <> 'D')
                GROUP BY
                    COALESCE(b.DOC_NOMBRE, a.DOC_CODIGO),
                    COALESCE(a.mov_serie, ''),
                    a.mov_docum,
                    a.mov_moned,
                    a.aux_clave,
                    a.DOC_CODIGO
            ) a
            INNER JOIN MOVA{self.fecha.year} b ON a.mvc_docum = b.mov_docum AND a.mvc_serie = b.MOV_SERIE
            LEFT JOIN t_origen c ON b.ORI_CODIGO = c.ori_codigo
            WHERE
                (c.ori_ventas = 1
                OR b.ORI_CODIGO IN (
                    SELECT ori_codigo
                    FROM t_parrametro
                    WHERE par_anyo = YEAR(GETDATE())
                )
                OR (b.ORI_CODIGO = '00' AND b.MOV_MES = '00'))
                {'AND a.mvc_debe <> a.mvc_haber' if filtro==0 else ''}
           
                AND SUBSTRING(b.pla_cuenta, 1, 2) >= '12'
                AND SUBSTRING(b.pla_cuenta, 1, 2) <= '13'
            ORDER BY
                a.mvc_docum ASC;
            """
        
        try:
            conn = QuerysDb.conexion(host,bd,user,passsword)
        
            result = self.querys(conn,sql,(codigo,),'get')
            data = []
            for index,value in enumerate(result):
                d = {
                    'id':index,
                    'codigo_vendedor':value[0],
                    'documento':value[1],
                    'serie':value[2].strip(),
                    'numero':value[3].strip(),
                    'moneda':value[4].strip(),
                    'monto_debe':f"{value[5]:,.2f}",
                    'monto_haber':f"{value[6]:,.2f}",
                    'monto_debes':f"{value[7]:,.2f}",
                    'emision':value[8].strftime('%Y-%m-%d'),
                    'vencimiento':value[9].strftime('%Y-%m-%d'),
                    'estado':value[10].strip(),
                   
                    }
                data.append(d)

        except Exception as e:
            data = str(e)
        return Response({'message':data})

    def querys(self,conn,sql,params,request):
        cursor = conn.cursor()
        cursor.execute(sql,params)
        if request=='get':
            data = cursor.fetchall()
        elif request=='post':
            data = 'success'
        conn.commit()
        conn.close()
        return data
    def post(self,request,*args,**kwargs):
        self.fecha = datetime.now()
        self.credencial = Credencial(request.data["credencial"])
    
        try:
            datos = request.data
            filtro = datos["filtro"]
            codigo = datos["codigo"]
            params = (codigo,)

            sql = f"""
                SELECT
                    b.ven_codigo,
                    a.DOC_NOMBRE,
                    a.mvc_serie,
                    a.mvc_docum,
                    a.MOV_MONED,
                    a.mvc_debe,
                    a.mvc_haber,
                    'mvc_debes' = a.mvc_debe - a.mvc_haber,
                    b.mov_femisi,
                    b.MOV_FVENC,
                    a.ban_nombre,
                    b.doc_codigo
            
                FROM (
                    SELECT
                        'DOC_NOMBRE' = COALESCE(b.DOC_NOMBRE, a.DOC_CODIGO),
                        'mvc_serie' = COALESCE(a.mov_serie, ''),
                        'mvc_docum' = a.mov_docum,
                        a.mov_moned,
                        'mvc_debe' = SUM(CASE WHEN a.mov_moned = 'S' THEN a.mov_d ELSE a.mov_d_d END),
                        'mvc_haber' = SUM(CASE WHEN a.mov_moned = 'S' THEN a.mov_h ELSE a.mov_h_d END),
                        'ban_nombre' = ISNULL((SELECT TOP 1 ban_nombre FROM mova{self.fecha.year} AS n WHERE n.mov_docum = a.mov_docum AND n.ban_nombre<>''  ORDER BY identi DESC ),'')
                    FROM
                        MOVA{self.fecha.year} a
                        LEFT JOIN t_documento b ON a.DOC_CODIGO = b.DOC_CODIGO AND a.MOV_SERIE = b.doc_serie
                    WHERE
                        a.aux_clave = ?
                        AND SUBSTRING(a.pla_cuenta, 1, 2) >= '12'
                        AND SUBSTRING(a.pla_cuenta, 1, 2) <= '13'
                        AND a.mov_fecha <= GETDATE()
                        AND a.mov_elimin = 0
                        AND (a.mov_moned = 'D' AND a.mov_d_d + a.mov_h_d <> 0 OR a.mov_moned <> 'D')
                    GROUP BY
                        COALESCE(b.DOC_NOMBRE, a.DOC_CODIGO),
                        COALESCE(a.mov_serie, ''),
                        a.mov_docum,
                        a.mov_moned,
                        a.aux_clave,
                        a.DOC_CODIGO
                ) a
                INNER JOIN MOVA{self.fecha.year} b ON a.mvc_docum = b.mov_docum AND a.mvc_serie = b.MOV_SERIE
                LEFT JOIN t_origen c ON b.ORI_CODIGO = c.ori_codigo
                WHERE
                    (c.ori_ventas = 1
                    OR b.ORI_CODIGO IN (
                        SELECT ori_codigo
                        FROM t_parrametro
                        WHERE par_anyo = YEAR(GETDATE())
                    )
                    OR (b.ORI_CODIGO = '00' AND b.MOV_MES = '00'))
                    {'AND a.mvc_debe <> a.mvc_haber' if filtro==0 else ''}
            
                    AND SUBSTRING(b.pla_cuenta, 1, 2) >= '12'
                    AND SUBSTRING(b.pla_cuenta, 1, 2) <= '13'
                ORDER BY
                    a.ban_nombre ASC;
                """
            s,result = CAQ.request(self.credencial,sql,params,"get",1)

            if not s:
                raise Exception("Ocurrio un error al ercuperar datos para el REPORTE")
            tipo_documentos = {
                "01":"FACT",
                "03":"NCR",
                "08":"NDE",
                "50":"LET"
            }
            data = [[tipo_documentos[value[-1]],value[2].strip(),value[3].strip(),value[8].strftime("%Y-%m-%d"),value[9].strftime("%Y-%m-%d"),value[4].strip(),value[5],value[6],value[7],value[10].strip()] for value in result]
            def custom_cabecera(canvas:Canvas,nombre):
                canvas.saveState()
                style = getSampleStyleSheet()
                razon_social = ParagraphStyle(name="aline",alignment=TA_LEFT,parent=style["Normal"])
                razon_social = Paragraph(self.datos['credencial']["razon_social"],style=razon_social)
                razon_social.wrap(nombre.width,nombre.topMargin)
                razon_social.drawOn(canvas,nombre.leftMargin,750)
                canvas.restoreState()
            response = HttpResponse(content_type = "application/pdf")
            response["Content-Disposition"] = "attachment;filename='REPORTE.pdf'" 

            file = PDFHistorialCliente(response,title="Cuentas por Cobrar",header=["TIpo","Numª","Serie","F. Emsion","F. Venc.","Mon.","Debe","Haber","Saldo","Banco"],data=data,custom_cabecera=custom_cabecera)
            file.generate()
            return response
        except Exception as e:
            return Response({"error":str(e)}) 

class ReadDocumentoView(generics.GenericAPIView):
    anio = datetime.now().year
    def get(self,request,*args,**kwargs):
        data = {}
        try:
            year = kwargs['year'].split('-')[0]
            conn = QuerysDb.conexion(kwargs['host'],kwargs['db'],kwargs['user'],kwargs['password'])
            sql = f"""
                SELECT
                    b.art_codigo,
                    c.ART_NOMBRE,
                    b.MOM_PUNIT,
                    b.MOM_CANT,
                    b.MOM_BRUTO,
                    b.mom_valor,
                    b.mom_dscto1,
                    b.mom_dscto2,
                    'UME_NOMBRE' = ISNULL(d.UME_NOMBRE, ''),
                    a.MOV_MONEDA,
                    b.art_codadi,
                    a.ROU_IGV,
                    a.rou_bruto,
                    a.rou_submon
                FROM
                    GUIC{year} a
                    INNER JOIN GUID{year} b ON a.MOV_COMPRO = b.MOV_COMPRO
                    INNER JOIN t_articulo c ON b.ART_CODIGO = c.ART_CODIGO
                    LEFT JOIN t_umedida d ON b.med_codigo = d.UME_CODIGO
                WHERE
                    a.fac_docum = ?
                ORDER BY
                    c.ART_NOMBRE
                """
            result = self.querys(conn,sql,(kwargs['codigo'],),'get')
            if len(result)==0:
                data['error']='No se encontraron datos'
                return Response(data)
            
       
            data['articulos'] = [
                {
                    'id':index,'codigo':value[0].strip(),'nombre':value[1].strip(),'precio':f"{value[2]:,.2f}",
                                'cantidad':value[3],'monto':f"{value[5]:,.2f}",'moneda':value[9].strip(),
                                'igv':value[11],'total':f"{value[12]:,.2f}",'base_imponible':f"{value[13]:,.2f}"
                } for index,value in enumerate(result)
                ]
            result = self.cabecera(year)
            data['cabecera'] = {
                'base_imponible':f"{result[0]:,.2f}",
                'igv':f"{result[1]:,.2f}",
                'total':f"{result[2]:,.2f}",
                'moneda':result[3].strip()
            }
        except Exception as e:
            data['error'] = 'Ocurrio un error al recuperar los datos'
            print(str(e))
        return Response(data)
    def cabecera(self,year):
        conn = QuerysDb.conexion(self.kwargs['host'],self.kwargs['db'],self.kwargs['user'],self.kwargs['password'])
        sql = f"""SELECT
                ROU_BRUTO,
                ROU_IGV,
                ROU_TVENTA,
                MOV_MONEDA
                FROM guic{year}    WHERE  fac_docum=?"""
        return self.querys(conn,sql,(self.kwargs['codigo'],),'get')[0]
    def querys(seld,conn,sql,params,request):
        cursor= conn.cursor()
        cursor.execute(sql,params)
        if request =='get':
            data = cursor.fetchall()
        elif request=='post':
            data = 'SUCCESS'
        return data