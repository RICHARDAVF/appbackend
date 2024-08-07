from rest_framework import generics
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response 
from apirest.credenciales import Credencial
from apirest.querys import CAQ
from apirest.view.general.views import User
from apirest.views import QuerysDb
from datetime import datetime
class ListOCview(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        host = kwargs['host']
        db = kwargs['db']
        user = kwargs['user']
        password = kwargs['password']
        sql = f"""
        SELECT  
            a.ped_numero,a.ped_fecha,a.ped_igv,a.ped_subtot,a.ped_submon,b.aux_razon,
            a.ped_diasen,a.ped_aprob1,a.ped_aprob2,a.ped_aprob3,a.pag_nombre,a.ped_estado,a.ped_moneda,a.ped_observ,a.pag_nombre
        FROM 
            orp101{str(datetime.now().year)[2:]} AS a 
        INNER JOIN 
            t_auxiliar AS B 
        ON 
            a.ped_codaux=b.aux_clave 
        WHERE 
            SUBSTRING(b.aux_clave,1,1) = 'P'
            AND a.PED_ANULA=0
			AND a.ped_estado=0
            """
        
        conn = QuerysDb.conexion(host,db,user,password)
        cursor = conn.cursor()
        cursor.execute(sql)
        datos = cursor.fetchall()
        conn.commit()
        conn.close()
        data = []
        for index, value in enumerate(datos):
            if int(value[11])==0:
                estado = 'PENDIENTE'
            elif int(value[11])==1:
                estado = "APROBADO"
            else:
                estado = "ANULADO"
           
            d = {'id':index,'pedido_numero':value[0],'fecha':value[1].strftime('%Y-%m-%d'),'igv':value[2],'subtotal':value[3],'total':value[4],\
                 'proveedor':value[5].strip(),'dias_entrega':value[6],'apro1':value[7],'apro2':value[8],'apro3':value[9],\
                'tipo_pago':value[10],'estado':estado,'moneda':value[12],'obs':value[13].strip(),"con_pago":value[14].strip()}
            data.append(d)
        return Response({'message':data})
    def post(self,request,*args,**kwargs):
        host = kwargs['host']
        db = kwargs['db']
        user = kwargs['user']
        password = kwargs['password']
        sql = f"UPDATE orp101{str(datetime.now().year)[2:]} SET "

        try:
            datos = request.data
            if datos['numero_aprobacion']==-1:
                raise ValueError('No se puede aprobar la orden de compra')
            if datos['option']==1:
                sql+='ped_aprob1=1'
            elif datos['option']==2:
                sql+='ped_aprob2=1'
            elif datos['option']==3:
                sql+='ped_aprob3=1'
            if  datos['numero_aprobacion']==3 and (datos["3"] and datos['2'] and datos['1']) :
                sql+=", ped_estado=1"
            elif  datos['numero_aprobacion']==2 and  (datos['1'] and datos["2"])  :
                sql+=", ped_estado=1"
            elif   datos['numero_aprobacion']==1 and datos['1']:
                sql+=', ped_estado=1'
            sql+=' WHERE ped_numero=?'

            respuesta = {}
            conn = QuerysDb.conexion(host,db,user,password)
            cursor = conn.cursor()
            cursor.execute(sql,(request.data['codigo'],))
            conn.commit()
            conn.close()
            respuesta['success'] = "Aprobacion exitosa"
        except Exception as e:
        
            respuesta['error'] = str(e)
        return Response({'message':respuesta})

class DetalleViewOR(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        host = kwargs['host']
        db = kwargs['db']
        user = kwargs['user']
        password = kwargs['password']
        numero = kwargs['numero']
        conn = QuerysDb.conexion(host,db,user,password)
        sql =f"""
            SELECT 
                art_nombre,ped_des1,ped_costou,ped_cant,ped_subt,art_umed
            FROM orp201{str(datetime.now().year)[2:]}
            WHERE 
                ped_numero=?
        """
        cursor = conn.cursor()
        cursor.execute(sql,(numero,))
        data = cursor.fetchall()
        conn.commit()
        conn.close()
        datos = []
        for index,value in enumerate(data):
            d = {'id':index,'nombre':value[0].strip(),'descuento':value[1],'precio':f"{value[2]:.2f}",'cantidad':value[3],'subtotal':value[4],'medida':value[5]}
            datos.append(d)
        return Response({'message':datos})
class ListOrdenCompra(GenericAPIView):
    fecha = datetime.now()
    def post(self,request,*args,**kwargs):

        data = {}
        datos = request.data
        self.credencial = Credencial(datos['credencial'])
        self.user = User(datos['user_codigo'],self.credencial)
      
        try:
            sql = f"""
                SELECT
                    par_rande2,
                    par_ranha2,
                    par_alogi2,
                    par_rande3,
                    par_ranha3,
                    par_alogi3,
                    par_rande4,
                    par_ranha4,
                    par_alogi4,
                    par_rande5,
                    par_ranha5,
                    par_alogi5
                FROM t_parrametro 
                WHERE par_anyo='{self.fecha.year}'
"""
            s,res_ =  CAQ.request(self.credencial,sql,(),'get',0)
            if not s:
                raise ValueError(res['error'])
            filter_ = datos['filter']
            
            sql = f"""
            SELECT  
                TOP 100
                a.ped_numero,
                a.ped_fecha,
                a.ped_igv,
                a.ped_subtot,
                a.ped_submon,
                b.aux_razon,
                a.ped_diasen,
                a.ped_aprob1,
                a.ped_aprob2,
                a.ped_aprob3,
                a.pag_nombre,
                a.ped_estado,
                a.ped_moneda,
                a.ped_observ,
                a.pag_nombre
            FROM 
                orp101{str(self.fecha.year)[2:]} AS a 
            INNER JOIN 
                t_auxiliar AS b
            ON 
                a.ped_codaux=b.aux_clave 
            WHERE 
                SUBSTRING(b.aux_clave,1,1) = 'P'
                AND a.PED_ANULA=0
                AND a.ped_estado=0
                AND (b.aux_razon LIKE '%{filter_}%' OR a.ped_numero LIKE '%{filter_}%')
            ORDER BY a.ped_fecha DESC
        """
            s,res = CAQ.request(self.credencial,sql,(),'get',1)
            estados = {"0":'PENDIENTE','1':'APROBADO','2':'ANULADO'}
            if not s:
                raise ValueError(res['error'])
            data = [
                {
                    'id':index,
                    "numero_pedido":value[0].strip(),
                    'fecha':value[1].strftime('%Y-%m-%d'),
                    'igv':f"{value[2]:.2f}",
                    'subtotal':f"{value[3]:.2f}",
                    'total':f"{value[4]:.2f}",
                    'proveedor':value[5].strip(),
                    'dias_entrega':int(value[6]),
                    'aprobacion1':self.can_aprobate(value[4],res_,value[7])>=1 and self.user.orden_compra_apro1,
                    'aprobacion2':self.can_aprobate(value[4],res_,value[8])>=2 and self.user.orden_compra_apro2,
                    'aprobacion3':self.can_aprobate(value[4],res_,value[9])>=3 and self.user.orden_compra_apro3,
                    "numero_aprobacion":self.number_aprobate(value[4],res_),
                    'tipo_pago':value[10].strip(),
                    'estado':estados[f'{value[11]}'],
                    'moneda':value[12],
                    "obs":value[13].strip(),
                    "cond_pago":value[14].strip()
                }
                for index,value in enumerate(res)
            ]
           
        except Exception as e:
            data['error'] = str(e)
        return Response(data)

    def can_aprobate(self,monto,data,status):
        if status==1:
            return -1
        if self.user.desde<=monto<=self.user.hasta:
           return self.number_aprobate(monto,data)
        return -1
    def number_aprobate(self,monto,data)->bool:
        if data[0]<=monto<=data[1]:
            return data[2]
        elif data[3]<=monto<=data[4]:
            return data[5]
        elif data[6]<=monto<=data[7]:
            return data[8]
        elif data[9]<=monto<=data[10]:
            return data[11]
        return -1