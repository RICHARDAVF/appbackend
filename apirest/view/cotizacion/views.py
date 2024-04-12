from datetime import datetime
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from apirest.credenciales import Credencial
from apirest.querys import CAQ
class Cotizacion(GenericAPIView):
    def post(self,request,*args,**kwargs):
        self.fecha = datetime.now()
        data = {}
        datos = request.data
        desde = '-'.join(datos['desde'].split('-')[::-1])
        hasta = '-'.join(datos['hasta'].split('-')[::-1])
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
                                        FROM guic{self.fecha.year} z22 WHERE z22.mov_pedido=(
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
                                'fac_bol'=ISNULL((SELECT TOP 1 rtrim(z2.fac_serie)+'-'+rtrim(z2.fac_docum) FROM guic{self.fecha.year} z2     
                                                where z2.mov_pedido=(SELECT TOP 1 y.mov_compro FROM cabepedido y 
                                                                        WHERE y.mov_cotiza=a.mov_compro 
                                                                        AND y.elimini=0) 
                                                                        AND z2.elimini=0                                                                                                                                         AND z2.fac_docum<>''),''),
                                'fac_fecha'=ISNULL((SELECT TOP 1 z.mov_fecha FROM guic{self.fecha.year} z 
                                                    WHERE z.mov_pedido=(SELECT TOP 1 y.mov_compro FROM cabepedido y 
                                                                        WHERE y.mov_cotiza=a.mov_compro and y.elimini=0) 
                                                                        AND z.elimini=0 and z.fac_docum<>''),''),
                                'fac_monto'=ISNULL((SELECT TOP 1 z.rou_tventa FROM guic{self.fecha.year} z 
                                                    WHERE z.mov_pedido=(SELECT TOP 1 y.mov_compro FROM cabepedido y 
                                                    WHERE y.mov_cotiza=a.mov_compro 
                                                        AND y.elimini=0) 
                                                        AND z.elimini=0 and z.fac_docum<>''),0),
                                a.identi,a.elimini,
                                'ot_fac_bol'=ISNULL(STUFF((SELECT char(10)+rtrim(z23.fac_serie)+'-'+rtrim(z23.fac_docum)+' ' FROM guic{self.fecha.year} z23, guid{self.fecha.year} z24 
                                                                                WHERE z23.MOV_COMPRO=z24.mov_compro 
                                                                                    AND z24.mov_ot in(SELECT y3.mov_compro FROM cabetecnico y3 
                                                                                                    WHERE y3.mov_cotiza=a.mov_compro 
                                                                                                    AND y3.elimini=0)                                                              AND z23.elimini=0
                                                                                                    AND z23.fac_docum<>'' 
                                                                                                    GROUP BY z23.fac_serie,z23.fac_docum for xml path('')),1,1,''),''),
                                'ot_f_facbo'=ISNULL((SELECT TOP 1 z233.mov_fecha FROM guic{self.fecha.year} z233, guid{self.fecha.year} z243 
                                                    WHERE z233.MOV_COMPRO=z243.mov_compro 
                                                    AND z243.mov_ot in(SELECT y33.mov_compro FROM cabetecnico y33 
                                                                        WHERE y33.mov_cotiza=a.mov_compro 
                                                                            AND y33.elimini=0) 
                                                                            AND z233.elimini=0 
                                                                            AND z233.fac_docum<>''),''),
                                'ot_m_facbo'=ISNULL((SELECT sum(z2433.mom_valor) FROM guic{self.fecha.year} z2333, guid{self.fecha.year} z2433, cabetecnico y3331 
                                                        WHERE z2333.MOV_COMPRO=z2433.mov_compro 
                                                         AND z2433.mov_ot=y3331.mov_compro 
                                                         AND y3331.mov_cotiza=a.mov_compro 
                                                         AND z2333.elimini=0 
                                                         AND z2333.fac_docum<>''),0),
                                a.rou_igv,a.rou_bruto,
                                'gui_ot'=ISNULL((SELECT TOP 1 rtrim(z5.gui_serie)+'-'+rtrim(z5.gui_docum) FROM guic{self.fecha.year} z5 
                                                WHERE z5.tec_devol in(SELECT y5.mov_compro FROM cabetecnico y5 
                                                                    WHERE y5.mov_cotiza=a.MOV_COMPRO 
                                                                    AND y5.elimini=0) 
                                                                    AND z5.elimini=0 
                                                                    AND z5.gui_docum<>''),''),
                                'oguia_fb'=ISNULL((SELECT TOP 1 rtrim(z222.ser_vargui)+'-'+rtrim(z222.fac_vargui) FROM guic{self.fecha.year} z222 
                                                    WHERE z222.tec_devol in(SELECT yyy.mov_compro FROM cabetecnico yyy 
                                                                        WHERE yyy.mov_cotiza=a.mov_compro 
                                                                        AND yyy.elimini=0) 
                                                                        AND z222.elimini=0 
                                                                        AND z222.gui_docum<>'' 
                                                                        AND z222.fac_vargui<>''),''),
                                'oguia_f_fb'=ISNULL((SELECT TOP 1 z2222.fec_vargui FROM guic{self.fecha.year} z2222 
                                                    WHERE z2222.tec_devol in(SELECT yyyy.mov_compro FROM cabetecnico yyyy 
                                                                            WHERE yyyy.mov_cotiza=a.mov_compro 
                                                                            AND yyyy.elimini=0) AND z2222.elimini=0 
                                                                            AND z2222.gui_docum<>'' 
                                                                            AND z2222.fac_vargui<>''),''),
                                'oguia_m_fb'=ISNULL((SELECT TOP 1 z2222.rou_tventa FROM guic{self.fecha.year} z2222 
                                                    WHERE z2222.tec_devol in(SELECT yyyy.mov_compro FROM cabetecnico yyyy 
                                                                            WHERE yyyy.mov_cotiza=a.mov_compro 
                                                                            AND yyyy.elimini=0) 
                                                                            AND z2222.elimini=0 
                                                                            AND z2222.gui_docum<>'' 
                                                                            AND z2222.fac_vargui<>''),0),
                                'ofb_bol'=ISNULL((SELECT TOP 1 rtrim(z2.fac_serie)+'-'+rtrim(z2.fac_docum) FROM guic{self.fecha.year} z2 
                                                    WHERE z2.tec_devol in(SELECT y.mov_compro FROM cabetecnico y 
                                                                        WHERE y.mov_cotiza=a.mov_compro 
                                                                        AND y.elimini=0) 
                                                                        AND z2.elimini=0 
                                                                        AND z2.fac_docum<>''),''),
                                'ofb_fecha'=ISNULL((SELECT TOP 1 z.mov_fecha FROM guic{self.fecha.year} z 
                                                    WHERE z.tec_devol in(SELECT y.mov_compro FROM cabetecnico y 
                                                                        WHERE y.mov_cotiza=a.mov_compro 
                                                                        AND y.elimini=0) 
                                                                        AND z.elimini=0 
                                                                        AND z.fac_docum<>''),''),
                                'ofb_monto'=ISNULL((SELECT TOP 1 z.rou_tventa FROM guic{self.fecha.year} z 
                                                    WHERE z.tec_devol in(SELECT y.mov_compro FROM cabetecnico y 
                                                                        WHERE y.mov_cotiza=a.mov_compro 
                                                                        AND y.elimini=0) 
                                                                        AND z.elimini=0 
                                                                        AND z.fac_docum<>''),0),
                                'guia_fact'=ISNULL((SELECT TOP 1 rtrim(z222.ser_vargui)+'-'+rtrim(z222.fac_vargui) FROM guic{self.fecha.year} z222 
                                                    WHERE z222.mov_pedido=(SELECT TOP 1 yyy.mov_compro FROM cabepedido yyy 
                                                                            WHERE yyy.mov_cotiza=a.mov_compro 
                                                                            AND yyy.elimini=0) 
                                                                            AND z222.elimini=0 
                                                                            AND z222.gui_docum<>'' 
                                                                            AND z222.fac_vargui<>''),''),
                                'guia_f_fac'=ISNULL((SELECT TOP 1 z2222.fec_vargui FROM guic{self.fecha.year} z2222 
                                                    WHERE z2222.mov_pedido=(SELECT TOP 1 yyyy.mov_compro FROM cabepedido yyyy 
                                                                            WHERE yyyy.mov_cotiza=a.mov_compro 
                                                                            AND yyyy.elimini=0) 
                                                                            AND z2222.elimini=0 
                                                                            AND z2222.gui_docum<>'' 
                                                                            AND z2222.fac_vargui<>''),''),
                                'guia_m_fac'=ISNULL((SELECT TOP 1 z2222.rou_tventa FROM guic{self.fecha.year} z2222 
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
                            WHERE YEAR(a.mov_fecha)='{datetime.now().year}'
                                AND a.mov_fecha>='{desde}'
                                AND a.mov_fecha<='{hasta}'
                                {
                                    f"AND b.aux_clave='{datos['cliente']}'" if datos['cliente']!='' else ''
                                }
                                {
                                    f"AND a.mov_compro='{datos['cotizacion']}'" if datos['cotizacion']!='' else ''
                                }
                                {
                                    f"AND a.gui_ordenc='{datos['orden_compra']}'" if datos['orden_compra']!='' else ''
                                }
                                {
                                    f"AND e.ven_codigo='{datos['vendedor']}'" if datos['vendedor']!='' else ''
                                }
                                {
                                    f"AND d.pag_codigo='{datos['condicion_pago']}'" if datos['condicion_pago']!='' else ''
                                }
                                {
                                    f"AND c.ope_codigo='{datos['motivo']}'" if datos['motivo']!='' else ''
                                }
                                {
                                    f"AND a.ope_codigo='{datos['operacion']}'" if datos['operacion']!='' else ''
                                }
                                {
                                    f"AND i.det_codigo='{datos['modelo']}'" if datos['modelo']!='' else ''
                                }
                                {
                                    f"AND a.cot_placa='{datos['placa']}'" if datos['placa']!='' else ''
                                }
                                {
                                    f"AND a.cot_chasis='{datos['chasis']}'" if datos['chasis']!='' else ''
                                }
                                {
                                    f"AND a.cot_chk01='{datos['servicio']}'" if datos['servicio']!='' else ''
                                }
                                {
                                    f"AND a.cot_anyo='{datos['year']}'" if datos['year']!='' else ''
                                }
                                {
                                    f"AND j.col_codigo='{datos['color']}'" if datos['color']!='' else ''
                                }
                                {
                                    f"AND a.ped_status='{datos['estado']}'" if datos['estado']!='' else ''
                                }                
                    """
            estados = {'0':'BORRADOR','1':'BORRADOR','2':'ACEPTADO','3':'RECHAZADO'} 
            servicios = {'1':'EQUIPAMIENTO','2':'ALMACEN','3':'ADICIONAL','4':'OTROS','0':'NS'}
            s,result = CAQ.request(self.credencial,sql,(),'get',1)
            if not s:
                raise Exception('Error al recuperar las cotizaciones')
          
            data = [
                {
                    "id":index,
                    "estado":estados[f"{int(value[0])}"],
                    "numero_cotizacion":value[1].strip(),
                    "orden_compra":value[2].strip(),
                    "documento":value[3].strip(),
                    "razon_social":value[4].strip(),
                    "fecha_emision":value[5].strftime('%d/%m/%Y'),
                    "moneda":value[6].strip(),
                    "importe":f"{float(value[7]):.2f}",
                    "placa":value[8].strip(),
                    "chasis":value[9].strip(),
                    "year":value[10].strip(),
                    "modelo":value[11].strip(),
                    "color":value[12].strip(),
                    "operacion":value[13].strip(),
                    "vehiculos":int(value[14]),
                    "servicio":servicios[f"{int(value[15])}"],
                    "guia_remision":value[16].strip(),
                    "ot":value[17].strip(),
                    "contacto":value[18].strip(),
                    "vendedor":value[19].strip(),
                    "condicion_pago":value[20].strip(),
                    "motivo":value[21].strip(),
                    "pedido":value[22].strip(),
                    "factura_boleta":self.factura_boleta(value[23].strip(),value[40].strip(),value[28].strip(),value[37].strip(),value[34].strip()),
                    "fecha":self.fecha_(value[24],value[41],value[29],value[38],value[35]),
                    "monto":f"{self.monto(value[25],value[42],value[30],value[39],value[36]):.2f}"

                    
                } for index,value in enumerate(result)
            ]
            data = [data[i:i+100] for i in range(0,len(data),100) ]
           
        except Exception as e:
            data['error'] = str(e)

        return Response(data)
    def factura_boleta(self,fac_bol,guia_fact,ot_fac_bol,ofb_bol,oguia_fb):
        if fac_bol!='':
            return fac_bol
        elif guia_fact!='':
            return guia_fact
        elif ot_fac_bol!='':
            return ot_fac_bol,
        elif ofb_bol!='':
            return ofb_bol
        return oguia_fb
    def fecha_(self,fac_fecha,guia_f_fac,ot_f_facbo,ofb_fecha,oguia_f_fb):
        if fac_fecha.strftime('%Y')!='1900':
            return fac_fecha.strftime('%d/%m/%Y')
        elif guia_f_fac.strftime('%Y')!='1900':
            return guia_f_fac.strftime('%d/%m/%Y')
        elif ot_f_facbo.strftime('%Y')!='1900':
            return ot_f_facbo.strftime('%d/%m/%Y')
        elif ofb_fecha.strftime('%Y')!='1900':
            return ofb_fecha.strftime('%d/%m/%Y')
        return oguia_f_fb.strftime('%d/%m/%Y')
    def monto(self,fac_monto,guia_m_fac,ot_m_facbo,ofb_monto,oguia_m_fb):
        if float(fac_monto)!=0:
            return float(fac_monto)
        elif  float(guia_m_fac)!=0:
            return float(guia_m_fac)
        elif  float(ot_m_facbo)!=0:
            return float(ot_m_facbo)
        elif  float(ofb_monto)!=0:
            return float(ofb_monto)
        return float(oguia_m_fb)

class GuardarCotizacion(GenericAPIView):
    def post(self,request,*args,**kwargs):
        self.datos = request.data
      
        self.usuario = self.datos['usuario']
        self.fecha = datetime.now()
        self.credencial = Credencial(self.datos['credencial'])
        self.numero_cotizacion = ''
        self.codigo_operacion = ''
        data = {}
        try:
            sql = f"""SELECT TOP 1 mov_compro FROM cabecotiza WHERE SUBSTRING(mov_compro,1,3)=? ORDER BY mov_compro DESC"""
            params = (self.usuario['codigo'],)
            s,result = CAQ.request(self.credencial,sql,params,'get',0)
          
            if not s:
                raise Exception('No se pudo recuperar el correlativo anterio')
            if result is None:
                result = ['0-0']
            self.numero_cotizacion = str(self.usuario['codigo'])+'-'+str(int(result[0].split('-')[-1])+1).zfill(7)
    
            sql = f""" SELECT ope_codigo FROM t_parrametro WHERE par_anyo='{self.fecha.year}'"""
            s,result = CAQ.request(self.credencial,sql,(),'get',0)
            if not s:
                raise Exception('Error al recuperar el codigo de operacion')
            self.codigo_operacion = result[0].strip()
            total = sum([float(item['subtotal']) for item in self.datos['detalle']])
            if self.datos['incluye_igv']:
                base_imponible = round(total/1.18,2)
            else:
                base_imponible = total
                total = round(base_imponible*1.18,2)
            igv = round(total-base_imponible,2)
            total_sin_descuento = self.total_sin_descuento()
            descuento = abs(total_sin_descuento-total)
            params = (self.numero_cotizacion,self.fecha.strftime('%Y-%m-%d'),self.datos['codigo'],'F1',self.datos['moneda'],self.usuario['cod'],
                      self.fecha.strftime('%Y-%m-%d'),base_imponible,18,igv,total,1,self.datos['ubicacion'],self.datos['tipo_pago'],self.datos['direccion'],
                      self.usuario['codigo'],total_sin_descuento,descuento,'05',self.datos['ubicacion'],self.datos['ruc'],1,self.datos['modelo_codigo'],self.datos['placa'],
                      self.datos['chasis'],self.datos['year'],self.datos['color_codigo'],self.datos['operacion'],self.datos['orden_compra'],
                      self.datos['vehiculos'],self.datos['servicio'],self.datos['dias_validez'],self.datos['contacto'])

            sql = f"""INSERT INTO cabecotiza(MOV_COMPRO,mov_fecha,MOV_CODAUX,DOC_CODIGO,MOV_MONEDA,USUARIO,FECHAUSU,
            ROU_BRUTO,ROU_PIGV,ROU_IGV,ROU_TVENTA,rou_export,ubi_codigo,pag_codigo,gui_direc,ven_codigo,rou_submon,rou_dscto,
            ope_codigo,ubi_codig2,gui_ruc,gui_inclu,cot_modelo,cot_placa,cot_chasis,cot_anyo,cot_color,cot_flota,gui_ordenc,
            cot_diaofe,cot_chk01,cot_chk07,aux_contac) VALUES({','.join('?' for i in params)})"""
            s,_ = CAQ.request(self.credencial,sql,params,'post')
            if not s:
               
                raise Exception('Error al guardar los datos de cotizacion')
         
            for item in self.datos['detalle']:
           
                total = float(item['cantidad'])*float(item['precio'])*float(self.datos['vehiculos']) if int(item['autos'])==0 else float(item['cantidad'])*float(item['precio'])*float(item['cantidad_vehiculos'])
                params = (53,str(self.fecha.month).zfill(2),self.numero_cotizacion,'F1',self.fecha.strftime('%Y-%m-%d'),
                          item['codigo'],'S','04',item['cantidad'],total,item['precio'],self.usuario['cod'],self.fecha.strftime('%Y-%m-%d'),
                          'S',1,self.datos['vehiculos'],item['autos'],item['descuento']) 
                sql = f"""
            INSERT INTO movicotiza(ALM_CODIGO,MOM_MES,mov_compro,doc_codigo,MOM_FECHA,ART_CODIGO,MOM_TIPMOV,OPE_CODIGO,MOM_CANT,
            mom_valor,MOM_PUNIT,USUARIO,FECHAUSU,art_afecto,gui_inclu,MOM_B_P_R,mom_bruto,mom_dscto1) VALUES ({','.join('?' for i in params)})"""
                s,_ = CAQ.request(self.credencial,sql,params,'post')
                if not s:
                   
                    raise Exception('Error al guardar los articulos de la cotizacion')
            data['msg'] = 'La cotizacion se guardo con exito'
        except Exception as e:
            print(str(e))
            data['error'] = str(e)
        return Response(data)
    def total_sin_descuento(self):
        total = 0
        for item in self.datos['detalle']:
            if int(item['autos'])==0:
                total+= float(item['cantidad'])*float(item['precio'])*int(self.datos['vehiculos'])
            else:
                total+= float(item['cantidad'])*float(item['precio'])*int(item['autos'])
        return round(total,2)

class CotizacionVars(GenericAPIView):
    def post(self,request,*args,**kwargs):
        datos = request.data
        self.credencial = Credencial(datos['credencial'])
        data = {}
        action = datos["action"]
        try:
            if action == 'modelo':
                sql = "SELECT det_codigo,det_nombre FROM t_detalle"
                s,result = CAQ.request(self.credencial,sql,(),"get",1)
               
                if not s:
                    raise Exception("Error al recuperar los modelos de vehiculos")
                data=[
                    {
                        "id":index,
                        "codigo":value[0].strip(),
                        "modelo":value[1].strip()
                    } for index,value in enumerate(result)
                ]
            elif action == "color":
                sql = "SELECT col_codigo,col_nombre FROM t_colores"
                s,result = CAQ.request(self.credencial,sql,(),'get',1)
                if not s:
                    raise Exception("Error al recuperar colores de los vehiculos")
                data = [
                    {
                        "id":index,
                        "codigo":value[0].strip(),
                        "color":value[1].strip()
                    } for index,value in enumerate(result)
                ] 
            else:
                data['error'] = "Opcion valida"
        except Exception as e:
            data['error'] = str(e)
        return Response(data)
class CotizacionFilter(GenericAPIView):
    def post(self,request,*args,**kwargs):
        data = {}
        self.datos = request.data
        self.credencial = Credencial(self.datos['credencial'])
        try:
            conn = CAQ().conexion(self.credencial)
            cursor = conn.cursor()
            sql = f"SELECT aux_razon,aux_clave FROM t_auxiliar"
            cursor.execute(sql,())
            result = cursor.fetchall()
            if result is None:
                raise Exception("NO hay clientes a mostrar")
            data['clientes'] = [
                {
                    "id":index,
                    "value":value[1].strip(),
                    "label":value[0].strip()
                } for index,value in enumerate(result)
            ]
            sql = "SELECT pag_nombre,pag_codigo from t_maepago"
            cursor.execute(sql,())
            result = cursor.fetchall()
            if result is None:
                raise Exception("No se pudo recuperar la lista de pago")
            data['condiciones_pago'] = [
                {
                    "id":index,
                    "label":value[0].strip(),
                    "value":value[1].strip()
                } for index,value in enumerate(result)
                ]
            sql = "SELECT col_codigo,col_nombre FROM t_colores"
            cursor.execute(sql,())
            result = cursor.fetchall()
            if result is None:
                raise Exception("No se pudo recuperar la lista de colores")
            data['colores'] = [
                {
                    "id":index,
                    "label":value[1].strip(),
                    "value":value[0].strip()
                } for index,value in enumerate(result)
                ]
            sql = "SELECT VEN_CODIGO,VEN_NOMBRE FROM t_vendedor"
            cursor.execute(sql,())
            result = cursor.fetchall()
            if result is None:
                raise Exception("No se pudo recuperar la lista de vendedores")
            data['vendedores'] = [
                {
                    "id":index,
                    "value":value[0].strip(),
                    "label":value[1].strip(),
                } for index,value in enumerate(result)
                ]
            sql = "SELECT ope_codigo,ope_nombre FROM t_operacion"
            cursor.execute(sql,())
            result = cursor.fetchall()
            data['motivos'] = [
                {
                    "id":index,
                    "value":value[0].strip(),
                    "label":value[1].strip(),
                } for index,value in enumerate(result)
                ]
            sql = "SELECT det_codigo,det_nombre FROM t_detalle"
            cursor.execute(sql,())
            result = cursor.fetchall()
            data['modelos'] = [
                {
                    "id":index,
                    "label":value[1].strip(),
                    "value":value[0].strip()
                } for index,value in enumerate(result)
                ]
            conn.commit()
            conn.close()
        except Exception as e:
            data['error'] = str(e)
        return Response(data)