from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from datetime import datetime
from apirest.credenciales import Credencial,CAQ
from apirest.querys import Querys
import logging
from apirest.view.generate_id import gen_id
from apirest.view.apis.views import TipoCambio
logger = logging.getLogger("django")
class GuardarPedido(GenericAPIView):
    credencial = None
    message = 'El pedido se guardo con exito'
    bk_message = 'NUEVO(APPV1)'
    anio = datetime.now().year
    def vale_monto_porcent(self,codigo,value,monto_total):
        if len(codigo)==0:
            return 0
        value_porcent = round(value*100/monto_total,2)
        return value_porcent
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
            s,gui_inclu = CAQ.request(self.credencial,sql,(),'get',0)
            if not s:
                raise ValueError(gui_inclu['error'])
         
            total1 = float(datos['total'])
            monto_vale_porcent = self.vale_monto_porcent(datos['vale_codigo'],datos['vale_monto'],total1)
            total=0
            base_impo=0
            descuento = self.calculate_descuento(total1,monto_vale_porcent,datos['detalle'])

            if int(gui_inclu[0])==1:
                total = total1-descuento
                base_impo = round(float(total)/1.18,2)
            else:
                base_impo= total1
                total = round(float(base_impo)*1.18,2)
            igv=round(total-base_impo,2)
            sql = " SELECT TOP 1 MOV_COMPRO FROM cabepedido WHERE SUBSTRING(mov_compro,1,3)=? ORDER BY MOV_COMPRO DESC"
            params = (datos['vendedor']['codigo'],)
            s,result = CAQ.request(self.credencial,sql,params,'get',0)

            if not s:
                raise ValueError(result['error'])
            if result is None:
                result = ['1']
            cor = str(datos['vendedor']['codigo'])+'-'+str(int(result[0].split('-')[-1])+1).zfill(7)
            if datos['codigo_pedido']!='x':
                cor = datos['codigo_pedido']
            sql = f"SELECT ope_codigo FROM t_parrametro WHERE par_anyo={datetime.now().year}"
           
            # ope_codigo = Querys(kwargs).querys(sql,(),'get',0) 
            s,ope_codigo = CAQ.request(self.credencial,sql,(),'get',0) 
            if not s:
                raise ValueError(ope_codigo['error'])
            fecha = datetime.now().strftime('%Y-%m-%d')
            codigo_vendedor = self.validar_vendedor()
           
            params = (cor,fecha,datos['cabeceras']['codigo'],datos['moneda'], datos['vendedor']['cod'],datetime.now().strftime('%Y-%m-%d %H:%M:%S'),total,1,datos['ubicacion'],datos['tipo_pago'],datos['cabeceras']['direccion'],datos['precio'],codigo_vendedor,str(ope_codigo[0]).strip(),datos['almacen'],datos['cabeceras']['ruc'],datos['obs'],18,igv,base_impo,
                    gui_inclu[0],datos['tipo_venta'],'F1',0,0,0,0,0,0,datos['agencia'],datos['sucursal'],datos['nombre'],datos['direccion'],total1,descuento,
                    datos['tipo_envio'],datos['vale_codigo'],monto_vale_porcent)
            sql = """INSERT INTO cabepedido (MOV_COMPRO,MOV_FECHA,MOV_CODAUX,MOV_MONEDA,USUARIO,FECHAUSU,ROU_TVENTA,
            rou_export,ubi_codigo,pag_codigo,gui_direc,lis_codigo,ven_codigo,ope_codigo,ubi_codig2,gui_ruc,
            gui_exp001,ROU_PIGV,ROU_IGV,ROU_BRUTO,gui_inclu,ped_tipven,doc_codigo,
            gui_aprot1,gui_aprot2,gui_aprot3,gui_aprov1,gui_aprov2,gui_aproc1,tra_codig2,gui_tienda,
            gui_tiedir,ped_tiedir,rou_submon,rou_dscto,ped_tipenv,ped_vale,ped_dscto) VALUES"""+'('+ ','.join('?' for i in params)+')'
        

            s,res = CAQ.request(self.credencial,sql,params,'post')
          
            if 'error' in res:
                data['error'] = 'Ocurrio un error en la grabacion'
                return Response(data)
        
            # res = self.auditoria_cabepedido(params,self.bk_message)
            # if 'error' in res:
            #     data['error'] = 'Ocurrio un error al grabar el pedido'
            #     return Response(data)
            sql1 = """INSERT movipedido (ALM_CODIGO,MOM_MES,mov_compro,MOM_FECHA,ART_CODIGO,tal_codigo,MOM_TIPMOV,
                ope_codigo,MOM_CANT,mom_valor,MOM_PUNIT,USUARIO,FECHAUSU,art_afecto,mom_dscto1,gui_inclu,
                mom_conpre,mom_peso,MOM_PUNIT2,doc_codigo,mom_linea,mom_conpro,mom_conpr2,mom_conreg,
                mom_confle,mom_cofleg,mom_concom,mom_concoa,mom_bruto,mom_lote,art_codadi,ped_observ) VALUES
                """
            cont = 1
            for item in datos['detalle']:
                mom_conpre = 'K' if item['lista_precio'] =='02' else ('U' if item['lista_precio']=='01' else '')
                mom_bruto = float(item['peso'])*int(item['cantidad']) if mom_conpre!= '' else 0
                talla = item['talla'] if item['talla'] !='x' else ''
                promo1 = 1 if item["tipo"] == 'P1' else 0
                promo2 = 1 if item["tipo"] == 'P2' else 0
                regalo = 1 if item['tipo'] == 'R' else 0
                flete = 1 if item["tipo"] == 'F' else 0
                pos = 1 if item['tipo']=='P' else 0
                flete_gratis = 0
                if item['tipo']=='F':
                    flete_gratis = item['flete_gratis'] 
                params = ('53',str(fecha).split('-')[1],cor,fecha,item['codigo'],talla,'S',str(ope_codigo[0]).strip(),float(item['cantidad']),float(item['total']),float(item['precio']),\
                        datos['vendedor']['cod'],fecha,'S',float(item['descuento']),gui_inclu[0],mom_conpre,float(item['peso']),float(item['precio_parcial']),'F1',cont,promo1,promo2,regalo,flete,flete_gratis,0,pos,\
                            mom_bruto,item['fecha'],item['lote'],item['obs']) 

                sql = sql1+'('+ ','.join('?' for i in range(len(params)))+')'
            
                s,res = CAQ.request(self.credencial,sql,params,'post')
                if not s:
                    raise ValueError(res['error'])
                if 'adicional' in item and len(item['adicional']['combo'])>0:
                    dates = item['adicional']['combo']
                    sql =  f"""
                    INSERT INTO movipedido_combo(mov_compro,mom_fecha,art_codigo,art_codig2,mom_cant,usuario,mom_cant2,art_fijo,mom_linea)
                    VALUES(?,?,?,?,?,?,?,?,?)"""
                    for value in dates:
                        if int(value['cant'])<=0:
                            continue
                        params_ = (cor,fecha,value['codigo'],item['codigo'],value['cantidad'],datos['vendedor']['cod'],value['cant'],value['tipo'],cont)
                        s,res = CAQ.request(self.credencial,sql,params_,'post')
            
                        if not s:
                            raise ValueError(res['error'])
                        
                # res = self.auditoria_movipedido(params,self.bk_message)
                
                # if 'error' in res:
                #     data['error'] = 'Ocurrio un error el grabar el pedido'
                #     return Response(data)
                cont+=1
            self.update_vale_usado(datos['vale_codigo'])
            self.aprobacion_automatica(cor)
            data['success'] = self.message
            
        except Exception as e:
       
            logger.error('An error occurred: %s', e)
            data['error'] = str(e)
        return Response(data)
    def calculate_descuento(self,total1,descuento,data):
        valor = 0
        if self.request.data['credencial']['codigo']=='12':
            valor = total1*descuento/100
        else:
            valor = abs(round(total1-self.sumaSDesc(data),2))
        return valor
    def update_vale_usado(self,codigo):
        if len(codigo)==0:
            return -1
        sql = "UPDATE t_descuento_vale SET prm_usado=1 WHERE vig_numero=?"
        CAQ.request(self.credencial,sql,(codigo,),'post')
    def data_update(self,):
        datos = self.request.data
        sql = "DELETE FROM cabepedido WHERE MOV_COMPRO=?"
        CAQ.request(self.credencial,sql,(datos['codigo_pedido'],),'post')
        sql = "DELETE FROM movipedido WHERE mov_compro=?"
        CAQ.request(self.credencial,sql,(datos['codigo_pedido'],),'post')
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
                
      
                stock_disponible = float(stock_real)-float(item['cantidad'])-float(pedidos_aprobados)-float(pedidos_pendientes)
 
                if stock_disponible<0:
                    data['error'] = f'El articulo {item["nombre"]} {item["talla"]} no tiene stock \nStock disponible : {stock_disponible:.2f}'
                    return False,data
            return True,''
        except Exception as e:
            logger.error("A error ocurred %s",str(e))
            data['error'] = f"Ocurrio un error {str(e)} "
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
            s,res = CAQ.request(self.credencial,sql,params,'get',0)
            if not s:
                raise ValueError(res['error'])
            data = res
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
            s,res = CAQ.request(self.credencial,sql,params,'get',0)
            if not s:
                raise ValueError(res['error'])
            data = res   
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
            s,res = CAQ.request(self.credencial,sql,params,'get',0)
            if not s:
                raise ValueError(res['error'])
            data = res
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
        parametros.pop(-1)#ELMINIAR obser
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
                        b.aux_telef,b.aux_email,b.ofi_codigo,a.ped_vale
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
                    'email':result[19].strip(),
                    'familia':result[20].strip()
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
                'vale_codigo':result[21].strip(),
                'vale_monto':self.vale_valor(result[21].strip())[0],
                'vale_monto_ref':self.vale_valor(result[21].strip())[1]
            }
            sql = """ SELECT a.ART_CODIGO, a.MOM_CANT, a.mom_valor, a.MOM_PUNIT, a.mom_dscto1, b.art_nombre,
                        a.tal_codigo,a.mom_peso,a.mom_conpre,a.MOM_PUNIT2,b.ven_codigo,a.art_codadi,a.mom_lote,
                        a.mom_confle,a.mom_conreg,a.mom_conpro,a.mom_conpr2,a.mom_concoa,a.ped_observ,a.mom_cofleg
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
                    "fecha":value[12].strip(),
                    "tipo":self.get_tipo(value[13],value[14],value[15],value[16],value[17]),
                    "obs":value[18].strip(),
                    'flete_gratis':value[19],
                    "adicional":{
                        "cantidad":1,
                        "combo":self.get_items_combo(datos['codigo'],value[0])
                    }
                } for index, value in enumerate(result)
            ]

        except Exception as e:
            print(str(e))
            logger.error('An error occurred: %s', e)
            data['error'] = 'Sucedio un error al recuperar los datos'
        return Response(data)
    def vale_valor(self,codigo):
       
        valor = [0,0]
        if len(codigo)==0:
            return [0,0]
        sql = "SELECT prm_dscto,prm_monto FROM t_descuento_vale WHERE vig_numero=?"
        _,res = CAQ.request(self.credencial,sql,(codigo,),'get',0)
        valor = [res[0],res[1]]
        return valor
    def get_tipo(self,flete,regalo,promo1,promo2,pos):
      
        if int(flete)==1:
            t = "F"
        elif int(regalo)==1:
            t= "R"
        elif int(promo1)==1:
            t = 'P1'
        elif int(promo2)==1:
            t = 'P2'
        elif int(pos)==1:
            t = 'P'
        else:
            t = "SP"
        return t
    def get_items_combo(self,numero_pedido,codigo_articulo):
        data = []
        try:
            sql = f"""
            SELECT 
                a.art_codigo,
                b.art_nombre,
                a.art_fijo,
                a.mom_cant
            FROM movipedido_combo AS a
            LEFT JOIN t_articulo AS b ON a.art_codigo=b.art_codigo
            WHERE 
                mov_compro=?
                AND art_codig2=?
                """
            params = (numero_pedido,codigo_articulo)
            s,res = CAQ.request(self.credencial,sql,params,'get',1)
            if not s:
                raise
            if res is None:
                raise
            data = [
                {
                    'id':gen_id(),
                    "codigo":value[0].strip(),
                    "nombre":value[1].strip(),
                    "tipo":value[2].strip(),
                    "cantidad":f"{value[3]:.0f}",
                    "cant":f"{value[3]:.0f}",
                } for value in res
            ]
        except:
            data = []
        return data
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
    def post(self,request,*args,**kwargs):
        data = {}
   
        self.tabla = 'maelista_familia'
        datos = request.data

        try:
            self.credencial = Credencial(datos['credencial'])
            self.numero = '' if datos['lista_precio']=='01' else int(datos['lista_precio'])
            self.codigo = datos['codigo']
            self.moneda = datos['moneda']
            self.familia = datos['familia']


            for i in range(3):
                if i== 0 and self.familia!='':
                    s,res = self.precio_familiar()
                    if res is not None:
                        break
                elif i==1:
                    s,res=self.precio_clientes()
                    if res is not None:
                        break
                elif i==2:
                    s,res =self.precio_general()
                   
                    if not s:
                        raise ValueError(res['error'])
            if not s:
                raise ValueError(res['error'])

            if res is None:
                data['error'] = 'El articulo no tiene precio' 
            else:
                data = {
                    "precio":round(res[0],2),
                    "moneda":res[1].strip(),
                    'des_min':res[2],
                    "des_max":res[3],
                    'peso':round(res[4],2)
                }
           
        except Exception as e:
            logger.error("A error ocurred %s",e)
            data['error'] = f"Ocurrio un error: {str(e)}"
        return Response(data)
    def precio_familiar(self):
        params = (self.familia,self.moneda,self.codigo)
        sql = f"""
                SELECT
                    a.lis_pmino{self.numero},
                    a.lis_moneda,
                    'des_min'=0,
					'des_max'=0,
                    b.art_peso
                FROM maelista_familia AS a
                LEFT JOIN t_articulo AS b ON a.art_codigo = b.ART_CODIGO
                WHERE
                    CAST(GETDATE() AS date)
                        BETWEEN CAST(a.lis_fini AS date) AND CAST(a.lis_ffin AS date)
                    AND a.ofi_codigo=?
                    AND a.lis_moneda=?
                    AND a.art_codigo=?
            """
        return CAQ.request(self.credencial,sql,params,'get',0)
        
    def precio_clientes(self):
        params = (self.moneda,self.codigo)
        sql = f"""
                SELECT
                    a.lis_pmino{self.numero},
                    a.lis_moneda,
					'des_min'=0,
					'des_max'=0,
                    b.art_peso
                FROM maelista_cliente AS a
                LEFT JOIN t_articulo AS b ON a.art_codigo = b.ART_CODIGO
                WHERE
                    CAST(GETDATE() AS date)
                        BETWEEN CAST(a.lis_fini AS date) AND CAST(a.lis_ffin AS date)      
                    AND a.lis_moneda=?
                    AND a.art_codigo=?
        """

        return CAQ.request(self.credencial,sql,params,'get',0)

    def precio_general(self):
        sql = f"""
                SELECT 
                    a.lis_pmino{self.numero},
                    a.lis_moneda,
                    a.lis_mindes,
                    a.lis_maxdes,
                    b.art_peso
                FROM maelista AS a 
                LEFT JOIN t_articulo AS b ON a.art_codigo = b.ART_CODIGO
                WHERE 
                    CAST(GETDATE() AS date) 
                    BETWEEN CAST(a.lis_fini AS date) AND CAST(a.lis_ffin AS date) 
                    --AND a.lis_tipo IN (1,0) 
                    AND a.lis_moneda=?
                    AND a.art_codigo=?
                    """
  

        params = (self.moneda,self.codigo)

        return CAQ.request(self.credencial,sql,params,'get',0)
        