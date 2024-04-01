from datetime import datetime
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from apirest.credenciales import Credencial
from apirest.querys import CAQ
class Cotizacion(GenericAPIView):
    def post(self,request,*args,**kwargs):
        data = {}
        datos = request.data

        self.credencial = Credencial(datos['credencial'])
        try:
            sql = f"""
                       SELECT  DISTINCT 
                                a.ped_status,
                                a.mov_compro,a.gui_ordenc,a.gui_ruc,'aux_razon'=ISNULL(b.aux_razon,''),
                                a.mov_fecha,a.mov_moneda,a.rou_tventa,a.cot_placa,a.cot_chasis,a.cot_anyo,
                                'det_nombre'=ISNULL(i.det_nombre,''),'col_nombre'=ISNULL(j.col_nombre,''),
                                a.cot_flota,a.cot_diaofe,a.cot_chk01,

                                'guia'=ISNULL(
                                        (SELECT TOP 1 rtrim(z22.gui_serie)+'-'+rtrim(z22.gui_docum) 
                                        FROM guic2024 z22 WHERE z22.mov_pedido=(
                                                            SELECT TOP 1 yy.mov_compro FROM cabepedido yy 
                                                            WHERE yy.mov_cotiza=a.mov_compro 
                                                                AND yy.elimini=0) 
                                                                AND z22.elimini=0 
                                                                AND z22.gui_docum<>''),''),
                                'ot'=ISNULL(STUFF((SELECT CHAR(10)+rtrim(ltrim(zz.mov_compro))+' ' FROM cabetecnico zz 
                                                    WHERE zz.mov_cotiza=a.MOV_COMPRO 
                                                     AND zz.elimini=0 for xml path('')),1,1,''),''),
                                a.aux_contac,'ven_nombre'=ISNULL(e.ven_nombre,''),
                                'pag_nombre'=ISNULL(d.pag_nombre,''),
                                'ope_nombre'=ISNULL(c.ope_nombre,''),
                                'pedido'=ISNULL((SELECT TOP 1 z.mov_compro FROM cabepedido z WHERE z.mov_cotiza=a.mov_compro 
                                                                                                AND z.elimini=0),''),
                                'fac_bol'=ISNULL((SELECT TOP 1 rtrim(z2.fac_serie)+'-'+rtrim(z2.fac_docum) FROM guic2024 z2     
                                                where z2.mov_pedido=(SELECT TOP 1 y.mov_compro FROM cabepedido y 
                                                                        WHERE y.mov_cotiza=a.mov_compro 
                                                                        AND y.elimini=0) 
                                                                        AND z2.elimini=0                                                                                                                                         AND z2.fac_docum<>''),''),
                                'fac_fecha'=ISNULL((SELECT TOP 1 z.mov_fecha FROM guic2024 z 
                                                    WHERE z.mov_pedido=(SELECT TOP 1 y.mov_compro FROM cabepedido y 
                                                                        WHERE y.mov_cotiza=a.mov_compro and y.elimini=0) 
                                                                        AND z.elimini=0 and z.fac_docum<>''),''),
                                'fac_monto'=ISNULL((SELECT TOP 1 z.rou_tventa FROM guic2024 z 
                                                    WHERE z.mov_pedido=(SELECT TOP 1 y.mov_compro FROM cabepedido y 
                                                    WHERE y.mov_cotiza=a.mov_compro 
                                                        AND y.elimini=0) 
                                                        AND z.elimini=0 and z.fac_docum<>''),0),
                                a.identi,a.elimini,
                                'ot_fac_bol'=ISNULL(STUFF((SELECT char(10)+rtrim(z23.fac_serie)+'-'+rtrim(z23.fac_docum)+' ' FROM guic2024 z23, guid2024 z24 
                                                                                WHERE z23.MOV_COMPRO=z24.mov_compro 
                                                                                    AND z24.mov_ot=(SELECT TOP 1 y3.mov_compro FROM cabetecnico y3 
                                                                                                    WHERE y3.mov_cotiza=a.mov_compro 
                                                                                                    AND y3.elimini=0) 
                                                                                                    AND z23.elimini=0
                                                                                                    AND z23.fac_docum<>'' 
                                                                                                    GROUP BY z23.fac_serie,z23.fac_docum for xml path('')),1,1,''),''),
                                'ot_f_facbo'=ISNULL((SELECT TOP 1 z233.mov_fecha FROM guic2024 z233, guid2024 z243 
                                                    WHERE z233.MOV_COMPRO=z243.mov_compro 
                                                    AND z243.mov_ot=(SELECT TOP 1 y33.mov_compro FROM cabetecnico y33 
                                                                        WHERE y33.mov_cotiza=a.mov_compro 
                                                                            AND y33.elimini=0) 
                                                                            AND z233.elimini=0 
                                                                            AND z233.fac_docum<>''),''),
                                'ot_m_facbo'=ISNULL((SELECT sum(z2433.mom_valor) FROM guic2024 z2333, guid2024 z2433, cabetecnico y3331 
                                                        WHERE z2333.MOV_COMPRO=z2433.mov_compro 
                                                         AND z2433.mov_ot=y3331.mov_compro 
                                                         AND y3331.mov_cotiza=a.mov_compro 
                                                         AND z2333.elimini=0 
                                                         AND z2333.fac_docum<>''),0),
                                a.rou_igv,a.rou_bruto,
                                'gui_ot'=ISNULL((SELECT TOP 1 rtrim(z5.gui_serie)+'-'+rtrim(z5.gui_docum) FROM guic2024 z5 
                                                WHERE z5.tec_devol=(SELECT TOP 1 y5.mov_compro FROM cabetecnico y5 
                                                                    WHERE y5.mov_cotiza=a.MOV_COMPRO 
                                                                    AND y5.elimini=0) 
                                                                    AND z5.elimini=0 
                                                                    AND z5.gui_docum<>''),''),
                                'oguia_fb'=ISNULL((SELECT TOP 1 rtrim(z222.ser_vargui)+'-'+rtrim(z222.fac_vargui) FROM guic2024 z222 
                                                    WHERE z222.tec_devol=(SELECT TOP 1 yyy.mov_compro FROM cabetecnico yyy 
                                                                        WHERE yyy.mov_cotiza=a.mov_compro 
                                                                        AND yyy.elimini=0) 
                                                                        AND z222.elimini=0 
                                                                        AND z222.gui_docum<>'' 
                                                                        AND z222.fac_vargui<>''),''),
                                'oguia_f_fb'=ISNULL((SELECT TOP 1 z2222.fec_vargui FROM guic2024 z2222 
                                                    WHERE z2222.tec_devol=(SELECT TOP 1 yyyy.mov_compro FROM cabetecnico yyyy 
                                                                            WHERE yyyy.mov_cotiza=a.mov_compro 
                                                                            AND yyyy.elimini=0) AND z2222.elimini=0 
                                                                            AND z2222.gui_docum<>'' 
                                                                            AND z2222.fac_vargui<>''),''),
                                'oguia_m_fb'=ISNULL((SELECT TOP 1 z2222.rou_tventa FROM guic2024 z2222 
                                                    WHERE z2222.tec_devol=(SELECT TOP 1 yyyy.mov_compro FROM cabetecnico yyyy 
                                                                            WHERE yyyy.mov_cotiza=a.mov_compro 
                                                                            AND yyyy.elimini=0) 
                                                                            AND z2222.elimini=0 
                                                                            AND z2222.gui_docum<>'' 
                                                                            AND z2222.fac_vargui<>''),0),
                                'ofb_bol'=ISNULL((SELECT TOP 1 rtrim(z2.fac_serie)+'-'+rtrim(z2.fac_docum) FROM guic2024 z2 
                                                    WHERE z2.tec_devol=(SELECT TOP 1 y.mov_compro FROM cabetecnico y 
                                                                        WHERE y.mov_cotiza=a.mov_compro 
                                                                        AND y.elimini=0) 
                                                                        AND z2.elimini=0 
                                                                        AND z2.fac_docum<>''),''),
                                'ofb_fecha'=ISNULL((SELECT TOP 1 z.mov_fecha FROM guic2024 z 
                                                    WHERE z.tec_devol=(SELECT TOP 1 y.mov_compro FROM cabetecnico y 
                                                                        WHERE y.mov_cotiza=a.mov_compro 
                                                                        AND y.elimini=0) 
                                                                        AND z.elimini=0 
                                                                        AND z.fac_docum<>''),''),
                                'ofb_monto'=ISNULL((SELECT TOP 1 z.rou_tventa FROM guic2024 z 
                                                    WHERE z.tec_devol=(SELECT TOP 1 y.mov_compro FROM cabetecnico y 
                                                                        WHERE y.mov_cotiza=a.mov_compro 
                                                                        AND y.elimini=0) 
                                                                        AND z.elimini=0 
                                                                        AND z.fac_docum<>''),0),
                                'guia_fact'=ISNULL((SELECT TOP 1 rtrim(z222.ser_vargui)+'-'+rtrim(z222.fac_vargui) FROM guic2024 z222 
                                                    WHERE z222.mov_pedido=(SELECT TOP 1 yyy.mov_compro FROM cabepedido yyy 
                                                                            WHERE yyy.mov_cotiza=a.mov_compro 
                                                                            AND yyy.elimini=0) 
                                                                            AND z222.elimini=0 
                                                                            AND z222.gui_docum<>'' 
                                                                            AND z222.fac_vargui<>''),''),
                                'guia_f_fac'=ISNULL((SELECT TOP 1 z2222.fec_vargui FROM guic2024 z2222 
                                                    WHERE z2222.mov_pedido=(SELECT TOP 1 yyyy.mov_compro FROM cabepedido yyyy 
                                                                            WHERE yyyy.mov_cotiza=a.mov_compro 
                                                                            AND yyyy.elimini=0) 
                                                                            AND z2222.elimini=0 
                                                                            AND z2222.gui_docum<>'' 
                                                                            AND z2222.fac_vargui<>''),''),
                                'guia_m_fac'=ISNULL((SELECT TOP 1 z2222.rou_tventa FROM guic2024 z2222 
                                                    WHERE z2222.mov_pedido=(SELECT TOP 1 yyyy.mov_compro FROM cabepedido yyyy 
                                                                            WHERE yyyy.mov_cotiza=a.mov_compro 
                                                                            AND yyyy.elimini=0) 
                                                                            AND z2222.elimini=0 
                                                                            AND z2222.gui_docum<>'' 
                                                                            AND z2222.fac_vargui<>''),0) 
                                                                            
                            FROM cabecotiza a LEFT JOIN t_auxiliar b on a.mov_codaux=b.aux_clave 
                            LEFT JOIN t_maepago d on a.pag_codigo=d.pag_codigo 
                            LEFT JOIN t_vendedor e on a.ven_codigo=e.ven_codigo 
                            LEFT JOIN t_operacion c on a.ope_codigo=c.ope_codigo 
                            LEFT JOIN mk_oficina g on b.ofi_codigo=g.ofi_codigo 
                            LEFT JOIN t_sucursal h on a.gui_tienda=h.tie_codigo 
                            LEFT JOIN t_detalle i on a.cot_modelo=i.det_codigo 
                            LEFT JOIN t_colores j on a.cot_color=j.col_codigo 
                            LEFT JOIN movicotiza pp on a.MOV_COMPRO=pp.mov_compro 
                            LEFT JOIN t_articulo qq on pp.ART_CODIGO=qq.ART_CODIGO 
                            WHERE YEAR(a.mov_fecha)='2024' 
                                AND a.mov_fecha>='2024-01-01' 
                                AND a.mov_fecha<='2024-03-23' 
                    """
            estados = {'0':'BORRADOR','1':'BORRADOR','2':'ACEPADO','3':'RECHAZADO'} 
            servicios = {'1':'EQUIPAMIENTO','2':'ALMACEN','3':'ADICIONAL','4':'OTROS'}
            s,result = CAQ.request(self.credencial,sql,(),'get',1)
            if not s:
                raise Exception('Error al recuperar las cotizaciones')
         
            data = [
                {
                    "id":index,
                    "estado":estados[f"{int(value[0])}"],
                    "numero_cotizacion":value[1].strip(),
                    "order_compra":value[2].strip(),
                    "documento":value[3].strip(),
                    "razon_social":value[4].strip(),
                    # "fecha_emision":value[3].strftime('%d/%m/%Y'),
                    # "moneda":value[4].strip(),
                    
                } for index,value in enumerate(result)
            ]
            data = [data[i:i+100] for i in range(0,len(data),100) ]
        except Exception as e:
            data['error'] = str(e)

        return Response(data)
class GuardarCotizacion(GenericAPIView):
    def post(self,request,*args,**kwargs):
        self.datos = request.data
        print(self.datos)
        self.fecha = datetime.now()
        self.credencial = Credencial(self.datos['credencial'])
        self.numero_cotizacion = ''
        self.codigo_operacion = ''
        data = {}
        try:
            sql = f"""SELECT TOP 1 mov_compro FROM cabepedido WHERE SUBSTRING(mov_compro,1,3)=? ORDER BY mov_compro DESC"""
            params = (self.datos['vendedor']['codigo'],)
            s,result = CAQ.request(self.credencial,sql,params,'get',0)
            if not s:
                raise Exception('No se pudo recuperar el correlativo anterio')
            if result is None:
                result = ['1']
            self.numero_cotizacion = str(self.datos['vendedor']['codigo'])+'-'+str(int(result[0].split('-')[-1])+1).zfill(7)
            sql = f""" SELECT ope_codigo FROM t_parrametro WHERE par_anyo='{self.fecha.year}'"""
            s,result = CAQ.request(self.credencial,sql,(),'get',0)
            if not s:
                raise Exception('Error al recuperar el codigo de operacion')
            self.codigo_operacion = result[0].strip()
            params = (self.numero_cotizacion,)
            sql = f"""INSERT INTO cabecotiza() VALUES({','.join('?' for i in params)})"""
        except Exception as e:
            data['error'] = str(e)
        return Response(data)