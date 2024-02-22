from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from dataclasses import dataclass
from datetime import datetime
from apirest.crendeciales import Config, Credencial
from apirest.querys import CAQ
from apirest.tipo_cambio import TipoCambio
from apirest.view.validacion_stock.views import ValidacionStock


class Cliente:
    ruc : str = None 
    razon_social : str = None
    cuenta_soles : str = None
    cuenta_dolares : str = None
    direccion : str = None
    codigo : str = None
    documento : str = None
    def __init__(self,documento:str,credencial:object):
        self.documento = documento
        self.credencial = credencial
        self.get_cliente()
    def get_cliente(self):
        try:
            sql = f"""SELECT AUX_DOCUM,AUX_RAZON,aux_cuenta,aux_cuentd,aux_direcc,aux_clave FROM t_auxiliar WHERE AUX_DOCUM=?"""
            _,result = CAQ.request(self.credencial,sql,(self.documento,),'get',0)
    
            self.ruc = result[0].strip()
            self.razon_social = result[1].strip()
            self.cuenta_soles = result[2].strip()
            self.cuenta_dolares = result[3].strip()
            self.direccion = result[4].strip()
            self.codigo = result[5].strip()
        except :
            raise
class Parametros:
    ubicacion : str = None
    almacen : str = None
    def __init__(self,credencial):
        self.credencial = credencial
        self.get_parametros()
    def get_parametros(self):
        try:
            sql = f"SELECT ubi_codigo,alm_codigo FROM t_parrametro WHERE par_anyo='{datetime.now().year}'"
            s,result = CAQ.request(self.credencial,sql,(),'get',0)
            if not s:
                raise Exception('Error al validar la ubicacion')
            if result is None:
                raise Exception('No existe ubucaciones para validar')
            self.ubicacion = result[0].strip()
            self.almacen = result[1].strip()
        except:
            raise
class Facturacion(GenericAPIView):
    credencial:object = None
    date : datetime  = datetime.now()
    cliente : object = None
    config : object = None
    parametros : object = None
    codigo_documento : str = None
    serie : str = None
    numero : str = None 
    mov_compro : str = None
    codigo_origen : str = None
    def tipo_cambio(self):
        return float(TipoCambio(self.request.data['credencial'],self.request.data['usuario']))
    def base_imponible(self):
        items:list[dict,str] = self.request.data['detalle']
        monto:float = 0
        for item in items:
            monto+=float(item['subtotal'])

        return round(monto/1.18 ,2)
    def total(self):
        items:list[dict,str] = self.request.data['detalle']
        monto:float = 0
        for item in items:
            monto+=float(item['subtotal'])
        return round(monto,2) 


        
    def post(self,request,*args,**kwargs):
        data = {}
        datos = request.data
       
        user = datos['usuario']
        self.credencial = Credencial(datos['credencial'])
        self.config = Config(self.credencial)
        self.parametros = Parametros(self.credencial)
        self.cliente = Cliente(datos['numero_documento'],self.credencial)
        self.codigo_documento = '03'
        try:
            for item in datos['detalle']:
                if not bool(ValidacionStock(CAQ().conexion(self.credencial),item,datos['almacen'],datos['ubicacion'])):
                    raise Exception(f'El articulo {item["nombre"]} no tiene stock disponible')
                
            sql = f"""SELECT b.doc_serie,b.doc_docum,a.ori_codigo FROM t_usuario AS a
                    INNER JOIN  t_documento AS b ON 
                    {f" a.usu_bole=b.doc_serie" if datos['tipo_documento']==1 else 'a.usu_fact=b.doc_serie'}
                    WHERE 
                        a.USU_CODIGO=?
                        {
                            f" AND b.doc_codigo='03' " if datos['tipo_documento']==1 else ''
                        } 
                        {
                            f" AND b.doc_codigo='01' " if datos['tipo_documento']==2 else ''
                        } 
                    """

            s,result = CAQ.request(self.credencial,sql,(user['cod'],),'get',0)
  
            if not s:
                raise Exception('Error al consultar por tipo de documento')
            if result is None:
                raise Exception('No se encontro un serie de facturacion')
            self.serie,self.numero,self.codigo_origen = result
            self.save_guic()
            self.save_guid()
            self.update_documento()
            self.save_mova()
            documento = 'boleta' if self.request.data['tipo_documento']==1 else 'factura'
            data['success'] = f"La {documento} se genero exitosamente"
        except Exception as e:
            data['error'] = str(e)
        return Response(data)
    def save_guic(self):
        datos = self.request.data
        user = datos['usuario']
        try:
            sql = f""" INSERT INTO corret{self.date.year}(usuario,fechausu) VALUES(?,?)"""
            params = (user['codigo'],datetime.now().strftime('%Y-%m-%d'))
            s,result = CAQ.request(self.credencial,sql,params,'post')
            if not s:
                raise  Exception('Error al generar el correlativo')
            sql = f"SELECT numero FROM corret{self.date.year} WHERE numero=(SELECT MAX(numero) FROM corret{self.date.year} WHERE usuario=?)"
            s,result = CAQ.request(self.credencial,sql,(user['codigo'],),'get',0)
            if not s:
                raise Exception('Error al recuperar el correlativo')
            self.mov_compro = result[0]            
            tipo_cambio = self.tipo_cambio()
            total = self.total()
            base_imponible = self.base_imponible()
            ivg = total-base_imponible
         
            almacen = self.parametros.almacen if datos['almacen']=='' else datos['almacen']
            ubicacion = self.parametros.ubicacion if datos['ubicacion']=='' else datos['ubicacion']
            codigo_tipo_documento = '06' if datos['tipo_documento']==2 else '07'
            descuento = abs(self.suma_subtotal()-total)
            vuelto = self.suma_subtotal()-self.vuelto()
            tarjeta1 = datos['tarjeta1'] if datos['tarjeta1']!='-1' else ''
            tarjeta2 = datos['tarjeta2'] if datos['tarjeta2']!='-1' else ''
            params = (str(self.mov_compro).zfill(11),self.date.strftime('%Y-%m-%d'),self.cliente.codigo,self.codigo_documento,self.config.moneda,tipo_cambio,user['cod'],self.date.strftime('%Y-%m-%d'),
                      base_imponible,'18',ivg,total,self.suma_subtotal(),1,1,1,self.serie,self.numero,ubicacion,datos['tipo_pago'],self.cliente.direccion,
                      '01',codigo_tipo_documento,user['codigo'],almacen,self.date.strftime('%m'),'01',self.cliente.razon_social,self.date.strftime('%Y-%m-%d'),
                      self.cliente.ruc,'04',descuento,1,vuelto,tarjeta1,datos['num1_tarjeta'],datos['monto1'],tarjeta2,datos['num2_tarjeta'],datos['monto2'],float(datos['efectivo']))
            sql = f"""
                    INSERT INTO guic{self.date.year} (
                        MOV_COMPRO,mov_fecha,MOV_CODAUX,DOC_CODIGO,MOV_MONEDA,mov_t_c,usuario,FECHAUSU,
                            ROU_BRUTO,ROU_PIGV,ROU_IGV,ROU_TVENTA,rou_submon,rou_export,gui_tipotr,gui_motivo,fac_serie,fac_docum,
                            ubi_codigo,pag_codigo,gui_direc,fac_coddoc,doc_compro,ven_codigo,alm_codigo,mov_mes,
                            ubi_codasi,mov_gloasi,mov_fecasi,gui_ruc,ope_codigo,rou_dscto,gui_inclu,tie_vuesol,tie_tarj01,tie_num01,tie_mon01,tie_tarj02,tie_num02,tie_mon02,
                            tie_efesol
                    )
                    VALUES ({','.join('?' for i in params)})
                    """
            s,_ = CAQ.request(self.credencial,sql,params,'post')
            if not s:
                raise Exception('Ocurrio un error al grabar en la base de datos')
        except:
            raise
    def convert_date_string(self,date):
        if self.request.data['config']['guid_lote']:
            pass
    
    def save_guid(self):
        items = self.request.data['detalle']
        datos = self.request.data
        user = datos['usuario']
        
        codigo_tipo_documento = '06' if datos['tipo_documento']==2 else '07'
        almacen = self.parametros.almacen if datos['almacen']=='' else datos['almacen']
        ubicacion = self.parametros.ubicacion if datos['ubicacion']=='' else datos['ubicacion']

        try:
            for item in items:
                lote = ''
                params = (almacen,self.date.strftime('%m'),str(self.mov_compro).zfill(11),self.codigo_documento,self.date.strftime('%Y-%m-%d'),item['codigo'],'S','04',
                          ubicacion,ubicacion,item['cantidad'],float(item['subtotal']),self.config.moneda,self.tipo_cambio(),item['precio'],user['cod'],
                          self.date.strftime('%Y-%m-%d'),codigo_tipo_documento,'S','',float(item['descuento']),item['lote'],item['lote'])
     
                sql = f"""
                            INSERT INTO guid{self.date.year} (ALM_CODIGO,MOM_MES,mov_compro,doc_codigo,mom_fecha,art_codigo,mom_tipmov,ope_codigo,
                            ubi_cod,ubi_cod1,mom_cant,mom_valor,mom_moneda,mom_t_c,mom_punit,usuario,fechausu,doc_compro,art_afecto,ped_observ,mom_dscto1,art_codadi,mom_lote)
                            VALUES ({','.join('?' for i in params)})
                        """
                s,_ = CAQ.request(self.credencial,sql,params,'post')
                if not s:
                    raise Exception('Ocurrio un error al grabar la factura')
                params = list(params)
                params.pop(-4)
                params = (*params,f"{self.serie}-{self.numero}",self.cliente.codigo,'03',1,item['lote'])
           
                sql = f""" INSERT INTO movm{self.date.year}(
                            ALM_CODIGO,MOM_MES,mom_d_int,mom_retip2,mom_fecha,art_codigo,mom_tipmov,ope_codigo,
                            ubi_cod,ubi_cod1,mom_cant,mom_valor,mom_moneda,mom_t_c,mom_punit,usuario,fechausu,art_afecto,ped_observ,mom_dscto1,mom_redoc2,mom_codaux,
                            doc_cod1,gui_inclu,art_codadi,mom_lote)
                            VALUES({','.join('?' for i in params)})
                        """
                s,_ = CAQ.request(self.credencial,sql,params,'post')
                if not s:
                    raise Exception('Ocurrio un error al grabar la factura')
        except :
            raise
    def save_mova(self):
        datos = self.request.data
        user = datos['usuario']
        try:
            mov_compro = ''
            sql = f"SELECT MAX(mov_compro) FROM mova{self.date.year} WHERE mov_mes=? AND ori_codigo=? "
            s,res = CAQ.request(self.credencial,sql,(self.date.strftime('%m'),user['codigo_origen']),'get',0)
    
            if not s:
                raise Exception('Error al recuperar  serie y numero')
            if res[0] is None:
                mov_compro = 1
            else:
                mov_compro = int(res[0])+1
            params = (self.date.strftime('%Y-%m-%d'),self.codigo_origen,self.cliente.razon_social,datos['ubicacion'],datos['almacen'],'1',
                      self.date.strftime('%m'),mov_compro,self.cliente.cuenta_soles,self.cliente.codigo,user['codigo'],self.date.strftime('%Y-%m-%d'),
                      self.codigo_documento,self.serie,self.numero,self.config.moneda,self.total(),0,0,0,self.tipo_cambio(),self.cliente.razon_social,
                      self.date.strftime('%Y-%m-%d'),user['cod'],)
            sql = f"""INSERT mova{self.date.year}(mov_fecha,ori_codigo,mov_glosa,ubi_codigo,alm_codigo,mov_tipoas,mov_mes,mov_compro,pla_cuenta,
            aux_clave,ven_codigo,mov_femisi,doc_codigo,mov_serie,mov_docum,mov_moned,mov_d,mov_h,mov_d_d,mov_h_d,mov_t_c,mov_glosa1,mov_fvenc,usuario) 
             VALUES({','.join('?' for i in params)})"""

            s,_ = CAQ.request(self.credencial,sql,params,'post')
            igv = abs(self.total()-self.base_imponible())
            if not s:
                raise Exception('Ocurrio un error al generar el primer asiento')
            sql1 = "SELECT cta_igv,cta_difmen,cta_difmas FROM t_parrametro where par_anyo=?"
            s,result = CAQ.request(self.credencial,sql1,(self.date.year,),'get',0)
            if not s:
                raise Exception('Error al recuperar cuenta de ajustes')
            cuenta_igv = result[0].strip()
            cuenta_n = result[1].strip()
            cuenta_p = result[2].strip()
            params = (self.date.strftime('%Y-%m-%d'),self.codigo_origen,self.cliente.razon_social,datos['ubicacion'],datos['almacen'],'1',self.date.strftime('%m'),
                      mov_compro,cuenta_igv,'',user['codigo'],self.date.strftime('%Y-%m-%d'),self.codigo_documento,'','',
                      self.config.moneda,0,round(igv,2),0,0,self.tipo_cambio(),self.cliente.razon_social,self.date.strftime('%Y-%m-%d'),user['cod'])
            s,_ = CAQ.request(self.credencial,sql,params,'post')
       
            if not s:
                raise Exception('Error al generar el asiento 2')
            conn = CAQ().conexion(self.credencial)
            cursor = conn.cursor()
            for item in datos['detalle']:
                params = (self.date.strftime('%Y-%m-%d'),self.codigo_origen,self.cliente.razon_social,datos['ubicacion'],datos['almacen'],'1',self.date.strftime('%m'),
                          mov_compro,item['cuenta'],'',user['codigo'],self.date.strftime('%Y-%m-%d'),self.codigo_documento,'','',
                          self.config.moneda,0,round(float(item['subtotal'])/1.18,2),0,0,self.tipo_cambio(),self.cliente.razon_social,self.date.strftime('%Y-%m-%d'),user['cod'])
                cursor.execute(sql,params)
            state,value = self.verificar_ajustes()
            
            if not state:

                if value<0:
                    c = (-value,0)
                    cuenta = cuenta_n
                else:
                    c = (0,value)
                    cuenta = cuenta_p
                params =  (self.date.strftime('%Y-%m-%d'),self.codigo_origen,self.cliente.razon_social,datos['ubicacion'],datos['almacen'],'1',self.date.strftime('%m'),
                          mov_compro,cuenta,'',user['codigo'],self.date.strftime('%Y-%m-%d'),self.codigo_documento,'','',
                          self.config.moneda,*c,0,0,self.tipo_cambio(),self.cliente.razon_social,self.date.strftime('%Y-%m-%d'),user['cod'])
                cursor.execute(sql,params)
            cursor.commit()
            cursor.close()
            self.update_guic(mov_compro)
        except:
            raise
    def update_guic(self,mov_compro):
        try:
            sql = f"""UPDATE guic{self.date.year} SET mov_comasi=? WHERE fac_serie=? AND fac_docum=?"""
            s,_ = CAQ.request(self.credencial,sql,(mov_compro,self.serie,self.numero),'post')
            if not s:
                raise Exception('Ocurrio un error al actulizar las tablas')
        except :
            raise
    def verificar_ajustes(self):
        total = self.total()
        base = self.base_imponible()
  
        igv = round(abs(total-base),2)

        monto = 0
        for item in self.request.data['detalle']:
            monto+=round(float(item['subtotal'])/1.18,2)
       
        return (total==round(monto+igv,2),round(total-monto-igv,2))
    def update_documento(self):
        try:
            sql = "UPDATE t_documento SET doc_docum=? WHERE doc_serie=?"
            s,_ = CAQ.request(self.credencial,sql,(int(self.numero)+1,self.serie),'post')
            if not s:
                raise Exception('No se puedo actulizar los documentos')
        except:
            raise
    def suma_subtotal(self):
        monto = 0
        for i in self.request.data['detalle']:
            monto+=float(i['cantidad'])*float(i['precio'])
        return monto
    def vuelto(self):
        datos = self.request.data
        try:
            return (float(datos['monto1'])+float(datos['monto2'])+float(datos['efectivo']))
        except:
            raise
