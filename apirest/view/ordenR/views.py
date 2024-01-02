from rest_framework import generics
from rest_framework.response import Response
from datetime import datetime
from apirest.views import QuerysDb
class OrdenView(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        sql = "SELECT*FROM orden"
        host = kwargs['host']
        db = kwargs['db']
        user = kwargs['user']
        password = kwargs['password']
        anio = datetime.now().year
        sql = f"""
                SELECT 
                    a.art_codigo,
                    a.art_nombre,
                    a.ume_abrev,
                    'stock' = ISNULL(
                        (
                            SELECT 
                                SUM(CASE 
                                    WHEN mom_tipmov = 'E' THEN mom_cant 
                                    WHEN mom_tipmov = 'S' THEN mom_cant * -1 
                                END) 
                            FROM 
                                movm{anio}
                            WHERE 
                                alm_codigo = '02' 
                                AND elimini = 0 
                                AND mom_cant <> 0 
                                AND art_codigo = a.art_codigo 
                            GROUP BY 
                                art_codigo 
                            HAVING 
                                SUM(CASE 
                                    WHEN mom_tipmov = 'E' THEN mom_cant 
                                    WHEN mom_tipmov = 'S' THEN mom_cant * -1 
                                END) <> 0
                        ),
                        0
                    ) 
                FROM 
                    t_articulo a 
                 
                ORDER BY 
                    a.art_nombre
                """
        conn = QuerysDb.conexion(host,db,user,password)
        data = self.querys(conn,sql,(),'get')
        datos = []
        for index,value in enumerate(data):
            d = {'id':index,'codigo':value[0].strip(),'nombre':value[1].strip(),'unidad':value[2].strip(),'stock':value[3]}
            datos.append(d)
        return Response({'message':datos})
    def querys(self,conn,sql,params,request):
        cursor = conn.cursor()
        cursor.execute(sql,params)
        if request == 'get':
            data = cursor.fetchall()
        elif  request == 'post':
            data = "SUCCESS"
        conn.commit()
        conn.close()
        return data
class OrdenFormView(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        host = kwargs['host']
        db = kwargs['db']
        user = kwargs['user']
        password = kwargs['password']
        datos = {}
        conn = QuerysDb.conexion(host,db,user,password)
        sql = "SELECT pre_codigo,pre_nombre,pre_correo FROM t_areadepa"
        area = self.querys(conn,sql,(),'get')
        areas =[]
        for value in area:
            d = {'codigo':value[0],'nombre':value[1].strip(),'correlacion':str(int(value[2].strip())+1).zfill(6) if len(value[2])!=0 else "000001"}
            areas.append(d)
        datos['areas']=areas

        conn = QuerysDb.conexion(host,db,user,password)
        sql = "SELECT aux_razon,aux_clave FROM t_auxiliar WHERE SUBSTRING(aux_clave,1,1) = 'P'"
        proveedor = self.querys(conn,sql,(),'get')
        proveedores =[]
        for value in proveedor:
            d = {'codigo':value[1].strip(),'razon_social':value[0].strip()}
            proveedores.append(d)
        datos['proveedores'] = proveedores
        sql = "SELECT ubi_nombre,ubi_codigo  FROM t_ubicacion"
        conn = QuerysDb.conexion(host,db,user,password)
        lugares = self.querys(conn,sql,(),'get')
        lugares_entrega =[]
        for value in lugares:
            d = {'nombre':value[0].strip(),'codigo':value[1].strip()}
            lugares_entrega.append(d)
        datos['lugares_entrega'] = lugares_entrega
        sql = """SELECT PAG_CODIGO,PAG_NOMBRE,pag_nvallc FROM t_maepago WHERE pag_activo='1' AND PAG_NOMBRE<>'' ORDER BY PAG_CODIGO"""
        conn = QuerysDb.conexion(host,db,user,password)
        tipo_pago = self.querys(conn,sql,(),'get')
        tipo_paymets = []
        for value in tipo_pago:
            a = {'codigo':str(value[0]).strip(),'nombre':str(value[1]).strip()}
            tipo_paymets.append(a)
        datos['tipo_pago'] = tipo_paymets
        return Response({'message':datos})
    def post(self,request,*args,**kwargs):
        response = {}
        host = kwargs['host']
        db = kwargs['db']
        user = kwargs['user']
        password = kwargs['password']
        pedido_numero = "R000001"
        year  = datetime.now().strftime('%Y-%m-%d').split('-')[0][2:]
        
        try:
            count = 0
            while count<2:
                conn = QuerysDb.conexion(host,db,user,password)
                table_name = f"sol101{year}"
                sql = f"SELECT TOP 1 ped_numero FROM {table_name} ORDER BY ped_numero DESC"
                data = self.querys(conn,sql,(),'get')
                if len(data)!=0:
                    pedido_numero = self.procesData(data[0][0])
                    break
                year = int(year)-1
                count+=1
            else:
                pedido_numero = "R000001"
            conn = QuerysDb.conexion(host,db,user,password)
        
            cabeceras = request.data['cabeceras']
            usuario =request.data['user']
            params = (pedido_numero,cabeceras['emision'].replace('/','-'),cabeceras['area'],cabeceras['obs1'],cabeceras['obs2'],datetime.now(),usuario['codigo'],cabeceras['serie'],\
                    cabeceras['entrega'].replace('/','-'),str(datetime.now().month).zfill(2),cabeceras['sol'],'',cabeceras['prioridad'],cabeceras['mercado'],cabeceras['tipo'],'',cabeceras['lugar_entrega'],cabeceras['proveedor'],cabeceras['tipo_pago'])
            sql = f"""
                INSERT INTO sol101{str(datetime.now().year)[2:]}(
                    ped_numero, ped_fecha, ped_area, ped_solici, ped_observ, fechausu,usuario, 
                    pre_corre, ped_fechae, ped_mes,ped_solic2, ped_fecapr,ped_priori, ped_mercad,
                    PED_TIPO, pag_nombre, ped_lentre, ped_codaux,pag_codigo) VALUES ({','.join("?" for i in range(len(params)))})
                    """
            self.querys(conn,sql,params,'post')     
            orden = request.data['orden']
            conn = QuerysDb.conexion(host,db,user,password)
            for item in orden:
                conn = QuerysDb.conexion(host,db,user,password)
                params= (pedido_numero,item['codigo'],item['cantidad'],0,item['nombre'],datetime.now().strftime('%Y-%m-%d'),datetime.now().strftime('%Y-%m-%d'),
                        usuario['codigo'],item['unidad'],item['descripcion'],item['cantidad'],item['op'],item['tipo'])
                sql = f"""
                    INSERT INTO sol201{str(datetime.now().year)[2:]} (
                        ped_numero, art_codigo, ped_cant, ped_reg, art_nombre, ped_fecha,
                        fechausu, usuario, art_umed, art_nombr2, ped_cants, ost_compro,ped_tipest)
                    VALUES ({','.join("?" for i in range(len(params)))})
                """
                self.querys(conn,sql,params,'post')
            conn = QuerysDb.conexion(host,db,user,password)
            
            self.querys(conn,f'UPDATE t_areadepa SET pre_correo=? WHERE pre_codigo=?',(cabeceras['serie'],cabeceras['area']),'post')
            response['success'] = 'Se guardo exitosamente'
            
        except Exception as e:
            response['error'] = str(e)

        return Response({'message':response})
    def procesData(self,data):
        return data[0]+ f"{int(data[1:])+1}".zfill(6)
        
    def querys(self,conn,sql, params,request):
        cursor = conn.cursor()
        cursor.execute(sql,params)
        if request == 'get':
            data = cursor.fetchall()
        elif request == 'post':
            data = "SUCCES"
        conn.commit()
        conn.close()
        return data
class OrdenListView(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        host = kwargs['host']
        db = kwargs['db']
        user = kwargs['user']
        password = kwargs['password']
        sql = f"""
            SELECT  ped_numero, ped_fecha, ped_area, ped_observ,ped_solic2,ped_priori, ped_mercad,PED_TIPO, 
            pag_nombre, ped_lentre, ped_codaux,pag_codigo,ped_estado
            FROM sol101{str(datetime.now().year)[2:]}"""
        conn = QuerysDb.conexion(host,db,user,password)
        result = self.querys(conn,sql,(),'get')
        orden_r = []
        for index,value in enumerate(result):
            d = {'id':index,'pedido_numero':value[0],'pedido_fecha':value[1].strftime('%Y-%m-%d'),'area':value[2],'obs1':value[3],'solicitante':value[4],"prioridad":value[5],'estado':value[-1]}
            orden_r.append(d)
        return Response({'message':orden_r})
    def querys(self,conn,sql,params,request):
        cursor = conn.cursor()
        cursor.execute(sql,params)
        if request == 'get':
            data = cursor.fetchall()
        elif request =='post':
            data = "success"
        conn.commit()
        conn.close()
        return data
class OrdenDetalleView(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        host = kwargs['host']
        db = kwargs['db']
        user = kwargs['user']
        password = kwargs['password']
        pedido_numero = kwargs['numero']
       
        sql = f"""
                SELECT 
                    ped_numero,
                    art_codigo,
                    art_nombre,
                    art_umed,
                    ped_cant,
                    ped_tipest
                FROM 
                    sol201{str(datetime.now().year)[2:]}
                WHERE
                    ped_numero=? 
            """
        conn = QuerysDb.conexion(host,db,user,password)
        cursor = conn.cursor()
        cursor.execute(sql,(pedido_numero,))
        data = cursor.fetchall()
        datas = []
        for index,value in enumerate(data):
            d = {'id':index,'pedido_numero':value[0],'codigo':value[1],'nombre':value[2].strip(),'unidad_medida':value[3],'cantidad':value[4],"tipo":value[5]}
            datas.append(d)
        return Response({'message':datas})
class EditOrdenView(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        host = kwargs['host']
        db = kwargs['db']
        user = kwargs['user']
        password = kwargs['password']
        pedido_numero = kwargs['numero']
        conn = QuerysDb.conexion(host,db,user,password)
        sql = f"""
                SELECT
                    ped_fecha, ped_area, ped_solici, ped_observ, 
                    pre_corre, ped_fechae,ped_solic2,ped_priori, ped_mercad,
                    PED_TIPO,ped_codaux,ped_lentre,pag_codigo
                FROM 
                    sol101{str(datetime.now().year)[2:]}
                WHERE
                    ped_numero = ?
            """
        
        result = self.querys(conn,sql,(pedido_numero,),'get')
        datas = {}
        ordenes = []
        for index,value in enumerate(result):
            d = {'id':index,'emision':value[0].strftime('%Y-%m-%d'),'area':value[1],'obs1':value[2],'obs2':value[3],'serie':value[4],'entrega':value[5].strftime('%Y-%m-%d'),\
                 'sol':value[6],'prioridad':value[7],'mercado':value[8],'tipo':value[9],'proveedor':value[10],'lugar_entrega':value[11],'tipo_pago':value[12],'pedido_numero':pedido_numero}
            ordenes.append(d)
        datas['ordenes'] = ordenes
        sql= f"""
            SELECT 
                art_codigo, ped_cant, art_nombre, art_umed, art_nombr2, ost_compro,ped_tipest,ped_stock
            FROM 
                    sol201{str(datetime.now().year)[2:]}
                WHERE
                    ped_numero = ?
            """

        conn = QuerysDb.conexion(host,db,user,password)
        result = self.querys(conn,sql,(pedido_numero,),'get')
        data = []
        for index, value in enumerate(result):
            d = {'id':index,'codigo':value[0],'cantidad':value[1],'nombre':value[2],'unidad':value[3],'descripcion':value[4],'op':value[5],'tipo':value[6],'stock':value[7]}
            data.append(d)
        datas['items'] = data
        return Response({'message':datas})
    def post(self,request,*args,**kwargs):
        host = kwargs['host']
        db = kwargs['db']
        user = kwargs['user']
        password = kwargs['password']
        pedido_numero = kwargs['numero']
        cabecera = request.data['cabeceras']
        res = {}
        try:
            sql = f""" UPDATE sol101{str(datetime.now().year)[2:]}
                            SET ped_area=?,  ped_solici=?, ped_observ=?, ped_fecha=?,
                                ped_fechae=?, ped_solic2=?, ped_priori=?, ped_mercad=?,
                                ped_lentre=?,  ped_codaux=?, pag_codigo=?
                        WHERE
                            ped_numero=?
                        """
        
            params = (cabecera['area'],cabecera['obs1'],cabecera['obs2'],cabecera['emision'],cabecera['entrega'],cabecera['sol'],cabecera['prioridad'],cabecera['mercado'],\
                    cabecera['lugar_entrega'],cabecera['proveedor'],cabecera['tipo_pago'],pedido_numero)
            conn = QuerysDb.conexion(host,db,user,password)
            self.querys(conn,sql,params,'post')
            sql  = f"DELETE FROM sol201{str(datetime.now().year)[2:]} WHERE ped_numero=?"
            conn = QuerysDb.conexion(host,db,user,password)
            self.querys(conn,sql,(pedido_numero,),'post')

            orden = request.data['orden']
            
            usuario = request.data['user']
            for item in orden:
                conn = QuerysDb.conexion(host,db,user,password)
                params= (pedido_numero,item['codigo'],item['cantidad'],0,item['nombre'],datetime.now().strftime('%Y-%m-%d'),datetime.now().strftime('%Y-%m-%d'),
                        usuario['codigo'],item['unidad'],item['descripcion'],item['cantidad'],item['op'],item['tipo'])
                sql = f"""
                    INSERT INTO sol201{str(datetime.now().year)[2:]} (
                        ped_numero, art_codigo, ped_cant, ped_reg, art_nombre, ped_fecha,
                        fechausu, usuario, art_umed, art_nombr2, ped_cants, ost_compro,ped_tipest)
                    VALUES ({','.join("?" for i in range(len(params)))})
                """
                self.querys(conn,sql,params,'post')
            res['success'] = f'Pedido {pedido_numero} editado exitosamente'
        except Exception as e:
            res['error'] = str(e)
        return Response({'message':res})
    def querys(self,conn,sql,params,request):
        cursor = conn.cursor()
        cursor.execute(sql,params)
        if request == 'get':
            data = cursor.fetchall()
        elif request == 'post':
            data = "SUCCESS"
        conn.commit()
        conn.close()
        return data
class AprobacionORView(generics.GenericAPIView):
    def post(self,request,*args,**kwargs):
        host = kwargs['host']
        db = kwargs['db']
        user = kwargs['user']
        password = kwargs['password']
        data = request.data
        sql = f"""
                UPDATE sol101{str(datetime.now().year)[2:]}
                SET
                    ped_estado=?
                WHERE
                    ped_numero=?
            """
        respuesta = {}
        try:
            conn = QuerysDb.conexion(host,db,user,password)
            cursor = conn.cursor()
            cursor.execute(sql,(data['opcion'],data['numero']))
            conn.commit()
            conn.close()
            respuesta['message'] = f'Se {"APROBO" if int(data["opcion"])==1 else "RECHAZO"} la O.R. {data["numero"]}'
        except Exception as e:
            respuesta['message'] = str(e)

        return Response(respuesta)