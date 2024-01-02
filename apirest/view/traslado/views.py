from collections import defaultdict
from rest_framework import generics
from rest_framework.response import Response
from apirest.views import QuerysDb
from numpy import array,char
from datetime import datetime
class TrasladoView(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        host = kwargs['host']
        db = kwargs['db']
        user = kwargs['user']
        password = kwargs['password']
        data = {}
        try:
            conn = QuerysDb.conexion(host,db,user,password)
            cursor = conn.cursor()
            sql = f"""
                    SELECT
                        OPE_CODIGO,
                        OPE_NOMBRE 
                    FROM 
                        t_operacion 
                    WHERE 
                        ope_activo=0
                    """
            cursor.execute(sql)
            datos = cursor.fetchall()
            conn.commit()
            conn.close()
            data = []
            for index,item in enumerate(datos):
                d = {'id':index,'value':item[0],'label':item[1].strip()}
                data.append(d)
        except Exception as e:
            data['error'] = str(e)
        return Response(data)

    def post(self,request,*args,**kwargs):
        response = {}
        data = request.data
        credenciales = request.data['cred']
        sql  = f"""
                SELECT
                    'stock' = SUM(CASE
                                    WHEN a.mom_tipmov = 'E' THEN a.mom_cant
                                    WHEN a.mom_tipmov = 'S' THEN a.mom_cant * -1
                                END)
                    - (SELECT
                        'mom_cant' = ISNULL(SUM(zzz.mom_cant), 0)
                    FROM
                        (SELECT
                                'mom_cant' = ISNULL(SUM(x.mom_cant), 0)
                                        + (SELECT ISNULL(SUM(CASE
                                                                WHEN z.mov_pedido = ''
                                                                THEN 0
                                                                WHEN z.mom_tipmov = 'E' THEN z.mom_cant
                                                                ELSE -z.mom_cant
                                                            END), 0)
                                            FROM movm{datetime.now().year} z
                                            LEFT JOIN cabepedido zz ON z.mov_pedido = zz.mov_compro
                                            WHERE y.mov_compro = z.mov_pedido
                                            AND x.art_codigo = z.art_codigo
                                            AND x.tal_codigo = z.tal_codigo
                                            AND y.ubi_codig2 = z.alm_codigo
                                            AND y.ubi_codigo = z.ubi_cod1
                                            AND z.elimini = 0
                                            AND zz.elimini = 0
                                            AND zz.ped_cierre = 0)
                        FROM movipedido x
                        INNER JOIN cabepedido y ON x.mov_compro = y.mov_compro
                        WHERE x.art_codigo = a.art_codigo
                            AND y.ubi_codig2 = a.alm_codigo
                            AND y.ubi_codigo = a.ubi_cod1
                            AND x.tal_codigo = a.tal_codigo
                            AND x.elimini = 0
                            AND y.ped_cierre = 0
                        GROUP BY y.mov_compro, x.art_codigo, x.tal_codigo, y.ubi_codig2, y.ubi_codigo) AS zzz)
                FROM movm{datetime.now().year} a
                LEFT JOIN cabepedido b ON a.mov_pedido = b.mov_compro
                WHERE a.art_codigo = ?
                AND a.alm_codigo = ?
                AND a.ubi_cod1 = ?
                AND a.tal_codigo = ?
                AND a.elimini = 0
                GROUP BY a.art_codigo, a.alm_codigo, a.ubi_cod1, a.tal_codigo
            """
        for item in data['items']:
            result = self.querys(credenciales,sql,(item['codigo'],data['almacen'],data['ubicacion_salida'],item['talla']))
            
            if result[0]<int(item['cantidad']):
                return Response({'message':f"No hay stock disponible para\nCodigo: {item['codigo']}\nTalla:{item['talla']}\nCantidad solicitada: {item['cantidad']}\nStock disponible: {int(result[0])} "})
        try:
            sql = f"""SELECT 
                        a.usu_almace,a.usu_docal2,a.usu_alma2,
                        b.doc_docum,a.usu_docalm,a.usu_alma,
                        c.doc_docum 
                    FROM t_usuario AS a LEFT JOIN t_documento AS b 
                    ON a.usu_docal2=b.doc_codigo AND a.usu_alma2=b.doc_serie 
                    LEFT JOIN t_documento AS c on a.usu_docalm=c.doc_codigo AND a.usu_alma=c.doc_serie WHERE a.usu_codigo=?"""
            result = self.querys(credenciales,sql,(data['usuario'],),'get')
            for item in data['items']:
                
                params = (data['almacen'],datetime.now().month,datetime.now().strftime('%Y-%m-%d'),item['codigo'],'S',data['operacion'],
                        data['ubicacion_salida'],data['ubicacion_salida'],item['cantidad'],data['usuario'],datetime.now(),
                        item['talla'],data['operacion'],data['ubicacion_entrada'],result[1].strip(),result[4].strip(),data['observacion'],f"{result[2].strip()}-{result[3].strip()}",
                        f"{result[5].strip()}-{result[6].strip()}",
                        
                        )
                sql = f""" INSERT INTO movm{datetime.now().year}(alm_codigo,mom_mes,mom_fecha,
                            art_codigo,mom_tipmov,ope_codigo,ubi_cod,ubi_cod1,mom_cant,
                            usuario,fechausu,tal_codigo,ope_codig2,ubi_cod2,doc_cod1,doc_cod2,mom_glosa,mom_d_int,mom_d_int2) VALUES({','.join('?' for i in params)}) 
                        """
                self.querys(credenciales,sql,params,'post')

                params = (data['almacen'],datetime.now().month,datetime.now().strftime('%Y-%m-%d'),item['codigo'],'E',data['operacion'],
                        data['ubicacion_entrada'],data['ubicacion_entrada'],item['cantidad'],data['usuario'],datetime.now(),
                        item['talla'],data['operacion'],data['ubicacion_salida'],result[4].strip(),result[1].strip(),data['observacion'],f"{result[5].strip()}-{result[6].strip()}",
                        f"{result[2].strip()}-{result[3].strip()}")
                self.querys(credenciales,sql,params,'post')
            sql  = "UPDATE t_documento SET doc_docum=? WHERE DOC_CODIGO=? AND doc_serie=?"
            params = (str(int(result[3])+1).zfill(7),result[1],result[2])
            self.querys(credenciales,sql,params,'post')
            params = (str(int(result[6])+1).zfill(7),result[4],result[5])
            self.querys(credenciales,sql,params,'post')
            response['message'] = f"Nota de salida:{result[2].strip()}-{result[3].strip()}\nNota de entrada: {result[5].strip()}-{result[6].strip()}"
        except Exception as e:
            print(str(e))
            response['error'] = f"Ocurrio un error {str(e)}"
        return Response(response)
    def querys(self,credenciales,sql,params,opt='get'):
        conn = QuerysDb.conexion(credenciales['bdhost'],credenciales['bdname'],credenciales['bduser'],credenciales['bdpassword'])
        cursor = conn.cursor()
        cursor.execute(sql,params)
        data = ''
        if opt=='get':
            data = cursor.fetchone()
        conn.commit()
        conn.close()
        return data
class ProducTrasladoView(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
       
        sql = f"""
                SELECT
                    a.art_codigo,
                    'tal_codigo' = a.tal_codigo,
                    'mom_cant' = SUM(CASE
                                    WHEN a.mom_tipmov='E' THEN a.mom_cant 
                                    WHEN a.mom_tipmov='S' THEN a.mom_cant*-1 
                                END) - (
                                    SELECT 
                                        'mom_cant' = ISNULL(SUM(zzz.mom_cant), 0) 
                                    FROM (
                                        SELECT 
                                            'mom_cant' = ISNULL(SUM(x.mom_cant), 0) + (
                                                SELECT 
                                                    ISNULL(SUM(
                                                        CASE 
                                                            WHEN z.mov_pedido='' THEN 0 
                                                            WHEN z.mom_tipmov='E' THEN z.mom_cant 
                                                            ELSE -z.mom_cant 
                                                        END
                                                    ), 0) 
                                                FROM movm{datetime.now().year} z 
                                                LEFT JOIN cabepedido zz ON z.mov_pedido=zz.mov_compro 
                                                WHERE y.mov_compro=z.mov_pedido 
                                                    AND x.art_codigo=z.art_codigo 
                                                    AND x.tal_codigo=z.tal_codigo 
                                                    AND y.ubi_codig2=z.alm_codigo 
                                                    AND y.ubi_codigo=z.ubi_cod1 
                                                    AND z.elimini=0 
                                                    AND zz.elimini=0 
                                                    AND zz.ped_cierre=0
                                            ) 
                                        FROM movipedido x 
                                        INNER JOIN cabepedido y ON x.mov_compro=y.mov_compro 
                                        WHERE x.art_codigo=a.art_codigo 
                                            AND y.ubi_codig2=a.alm_codigo 
                                            AND y.ubi_codigo=a.ubi_cod1 
                                            AND x.tal_codigo=a.tal_codigo 
                                            AND x.elimini=0 
                                            AND y.ped_cierre=0 
                                        GROUP BY y.mov_compro, x.art_codigo, x.tal_codigo, y.ubi_codig2, y.ubi_codigo
                                    ) AS zzz
                                ) 
                    ,b.ART_NOMBRE,
                    'ume_pres' = ISNULL(c.ume_nombre, ''),
                    a.ALM_CODIGO,
                    a.UBI_COD1,
                    'orden' = (
                        CASE 
                            WHEN a.tal_codigo='XS' THEN 'X1' 
                            WHEN a.tal_codigo='SS' THEN 'X2' 
                            WHEN a.tal_codigo='MM' THEN 'X3' 
                            WHEN a.tal_codigo='LL' THEN 'X4' 
                            WHEN a.tal_codigo='XL' THEN 'X5' 
                            ELSE a.tal_codigo 
                        END
                    )
                FROM movm{datetime.now().year} a 
                LEFT JOIN t_articulo b ON a.ART_CODIGO=b.art_codigo 
                LEFT JOIN t_umedida c ON b.ume_precod=c.ume_codigo
                WHERE a.elimini=0 
                    AND b.art_mansto=0 
                    AND a.ALM_CODIGO=?
                    AND a.UBI_COD1=?
                GROUP BY a.art_codigo, b.ART_NOMBRE, c.ume_nombre, a.ALM_CODIGO, a.UBI_COD1, b.art_peso, b.art_mansto, a.tal_codigo 
                HAVING 
                    SUM(CASE 
                        WHEN a.mom_tipmov='E' THEN a.mom_cant 
                        WHEN a.mom_tipmov='S' THEN a.mom_cant*-1 
                    END) - (
                        SELECT 
                            'mom_cant' = ISNULL(SUM(zzz.mom_cant), 0) 
                        FROM (
                            SELECT 
                                'mom_cant' = ISNULL(SUM(x.mom_cant), 0) + (
                                    SELECT 
                                        ISNULL(SUM(
                                            CASE 
                                                WHEN z.mov_pedido='' THEN 0 
                                                WHEN z.mom_tipmov='E' THEN z.mom_cant 
                                                ELSE -z.mom_cant 
                                            END
                                        ), 0) 
                                    FROM movm{datetime.now().year} z 
                                    LEFT JOIN cabepedido zz ON z.mov_pedido=zz.mov_compro 
                                    WHERE y.mov_compro=z.mov_pedido 
                                        AND x.art_codigo=z.art_codigo 
                                        AND x.tal_codigo=z.tal_codigo 
                                        AND y.ubi_codig2=z.alm_codigo 
                                        AND y.ubi_codigo=z.ubi_cod1 
                                        AND z.elimini=0 
                                        AND zz.elimini=0 
                                        AND zz.ped_cierre=0
                                ) 
                            FROM movipedido x 
                            INNER JOIN cabepedido y ON x.mov_compro=y.mov_compro 
                            WHERE x.art_codigo=a.art_codigo 
                                AND y.ubi_codig2=a.alm_codigo 
                                AND y.ubi_codigo=a.ubi_cod1 
                                AND x.tal_codigo=a.tal_codigo 
                                AND x.elimini=0 
                                AND y.ped_cierre=0 
                            GROUP BY y.mov_compro, x.art_codigo, x.tal_codigo, y.ubi_codig2, y.ubi_codigo
                        ) AS zzz
                    ) <> 0 
                ORDER BY b.art_nombre, c.ume_nombre, orden"""
        try:
            product = self.querys(sql,kwargs)
            codigo = char.strip(product[:, 0].tolist())
            talla = char.strip(product[:, 1].tolist())
            stock = product[:, 2].tolist()
            nombre = char.strip(product[:, 3].tolist())
            serialize_product = [{'id': index, 'codigo': code, 'stock': st, 'nombre': nom,
                    'talla': ta} for index, (code, st, nom, ta) in
                    enumerate(zip(codigo, stock, nombre, talla))]
            
            return Response({"message":serialize_product})
        except Exception as e:

            return Response({"error":f"Ocurrio un error {str(e)}"})
    def querys(self,sql,kwargs):
        host = kwargs['host']
        db = kwargs['db']
        user = kwargs['user']
        password = kwargs['password']
        local = kwargs['local']
        ubicacion = kwargs['ubi']
        conn = QuerysDb.conexion(host,db,user,password)
        cursor = conn.cursor()
        cursor.execute(sql,(ubicacion,local))
        product = array(cursor.fetchall())
        conn.commit()
        conn.close()
        return product
class StockViewProduct(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        data = {}
        try:
            codigo = kwargs['codigo']
            if codigo == '000':
                sql = "SELECT ART_CODIGO,ART_NOMBRE FROM t_articulo ORDER BY ART_NOMBRE ASC"
                data = array(self.querys(sql,kwargs))
                art_code = char.strip(data[:,0].tolist())
                nombre = char.strip(data[:,1].tolist())
                serializer = [{'id':index,'codigo':code,'nombre':name} for index,(code,name) in enumerate(zip(art_code,nombre))]
                return Response(serializer)  
            sql = f"""
                    SELECT
                        b.ubi_codigo,
                        b.ubi_nombre,
                        a.tal_codigo,
                        'mom_cant' = SUM(
                            CASE
                                WHEN a.mom_tipmov = 'E' THEN a.mom_cant
                                WHEN a.mom_tipmov = 'S' THEN a.mom_cant * -1
                            END
                        ) - (
                            SELECT 'mom_cant' = ISNULL(
                                SUM(zzz.mom_cant),
                                0
                            )
                            FROM (
                                SELECT
                                    'mom_cant' = ISNULL(
                                        SUM(x.mom_cant),
                                        0
                                    ) + (
                                        SELECT ISNULL(
                                            SUM(
                                                CASE
                                                    WHEN z.mov_pedido = '' THEN 0
                                                    WHEN z.mom_tipmov = 'E' THEN z.mom_cant
                                                    ELSE -z.mom_cant
                                                END
                                            ),
                                            0
                                        )
                                        FROM
                                            movm{datetime.now().year} z
                                        LEFT JOIN
                                            cabepedido zz
                                        ON
                                            z.mov_pedido = zz.mov_compro
                                        WHERE
                                            y.mov_compro = z.mov_pedido
                                            AND x.art_codigo = z.art_codigo
                                            AND x.tal_codigo = z.tal_codigo
                                            AND y.ubi_codig2 = z.alm_codigo
                                            AND y.ubi_codigo = z.ubi_cod1
                                            AND z.elimini = 0
                                            AND zz.elimini = 0
                                            AND zz.ped_cierre = 0
                                    )
                                FROM
                                    movipedido x
                                INNER JOIN
                                    cabepedido y
                                ON
                                    x.mov_compro = y.mov_compro
                                WHERE
                                    x.art_codigo = a.art_codigo
                                    AND y.ubi_codig2 = a.alm_codigo
                                    AND y.ubi_codigo = a.ubi_cod1
                                    AND x.tal_codigo = a.tal_codigo
                                    AND x.elimini = 0
                                    AND y.ped_cierre = 0
                                GROUP BY
                                    y.mov_compro,
                                    x.art_codigo,
                                    x.tal_codigo,
                                    y.ubi_codig2,
                                    y.ubi_codigo
                            ) AS zzz
                        ),
                        'orden' = (
                            CASE
                                WHEN a.tal_codigo = 'XS' THEN '0X1'
                                WHEN a.tal_codigo = 'SS' THEN '0X2'
                                WHEN a.tal_codigo = 'MM' THEN '0X3'
                                WHEN a.tal_codigo = 'LL' THEN '0X4'
                                WHEN a.tal_codigo = 'XL' THEN '0X5'
                                ELSE a.tal_codigo
                            END
                        )
                        FROM
                        movm{datetime.now().year} a
                        LEFT JOIN
                        t_ubicacion b
                        ON
                        a.ubi_cod1 = b.ubi_codigo
                        WHERE
                        a.art_codigo = ?
                        AND a.elimini = 0
                        GROUP BY
                        b.ubi_codigo,
                        b.ubi_nombre,
                        a.tal_codigo,
                        a.art_codigo,
                        a.alm_codigo,
                        a.ubi_cod1
                        ORDER BY
                        orden
            """

            
            data = self.querys(sql,kwargs,(codigo))
            items = []
            for item in data:
                d = {'codigo':item[0].strip(),'ubicacion':item[1].strip(),'talla':item[2].strip(),'cantidad':item[3]}
                items.append(d)

            grouped_data = defaultdict(lambda: {"codigo": None, "ubicacion": None, "tallas": [], "cantidades": []})
            for item in items:
                key = (item["codigo"], item["ubicacion"])
                grouped_data[key]["codigo"] = item["codigo"]
                grouped_data[key]["ubicacion"] = item["ubicacion"]
                grouped_data[key]["tallas"].append(item["talla"])
                grouped_data[key]["cantidades"].append(item["cantidad"])
                    
            data = list(grouped_data.values())
            
            tallas = []
            talla_orden = {'SS': 1, 'MM': 2, 'LL': 3, 'XL': 4}
            for item in data:
                for i in item['tallas']:
                    if i.strip() not in  tallas:
                        tallas.append(i.strip())
            if "XL" in tallas or 'SS' in tallas or 'MM' in tallas or 'LL' in tallas:
                tallas = sorted(tallas, key=lambda x: talla_orden.get(x, 99))
            for item in range(len(data)):
                cantidades = [0]*len(tallas)
                for i,j in zip(data[item]['cantidades'],data[item]['tallas']):
                    index = tallas.index(j)
                    cantidades[index] = int(i)
                data[item]['id'] = item+1
                data[item]['tallas'] = tallas 
                data[item]['cantidades'] = cantidades
                data[item]['stock'] = sum(data[item]['cantidades'])
         
        except Exception as e:
            data['error'] = f"Ocurrio un error : {str(e)}"

        return Response(data)
    def querys(self,sql,kwargs,params=()):
            
        host = kwargs['host']
        db = kwargs['db']
        user = kwargs['user']
        password = kwargs['password']

        conn = QuerysDb.conexion(host,db,user,password)
        cursor = conn.cursor()
        cursor.execute(sql,params)
        product = array(cursor.fetchall())
        conn.commit()
        conn.close()
        return product
