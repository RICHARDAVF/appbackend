from rest_framework import generics
from rest_framework.response import Response 
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
            a.ped_diasen,a.ped_aprob1,a.ped_aprob2,a.ped_aprob3,a.pag_nombre,a.ped_estado 
        FROM 
            orp101{str(datetime.now().year)[2:]} AS a 
        INNER JOIN 
            t_auxiliar AS B 
        ON 
            a.ped_codaux=b.aux_clave 
        WHERE 
            SUBSTRING(b.aux_clave,1,1) = 'P'"""
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
                'tipo_pago':value[10],'estado':estado}
            data.append(d)
        return Response({'message':data})
    def post(self,request,*args,**kwargs):
        host = kwargs['host']
        db = kwargs['db']
        user = kwargs['user']
        password = kwargs['password']
        sql = f"UPDATE orp101{str(datetime.now().year)[2:]} SET "
        usuario = request.data['user']
        if usuario['apro_oc1']==1:
            sql+='ped_aprob1=1'
        if usuario['apro_oc2']==1:
            sql+=',ped_aprob2=1'
        if usuario['apro_oc3']==1:
            sql+=',ped_aprob3=1'
        sql+=' WHERE ped_numero=?'
        respuesta = {}
        try:
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
                art_nombre,ped_des1,ped_costou,ped_cant,ped_subt 
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
            d = {'id':index,'nombre':value[0].strip(),'descuento':value[1],'precio':value[2],'cantidad':value[3],'subtotal':value[4]}
            datos.append(d)
        return Response({'message':datos})
