from rest_framework import generics
from rest_framework.response import Response
from apirest.credenciales import Credencial
from apirest.querys import CAQ
from apirest.views import QuerysDb
from datetime import datetime
import logging
logger = logging.getLogger("django")
class StockView(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        host = kwargs['host']
        db = kwargs['db']
        user = kwargs['user']
        password = kwargs['password']
        alm = kwargs['alm']
        ubi = kwargs['ubi']
        talla = kwargs['talla']
        anio = datetime.now().year
        lista_ubicaciones = request.GET.getlist('arreglo[]', [])
        if len(lista_ubicaciones) == 0:
            ubis = [ubi]
        else:
            ubis = lista_ubicaciones
        sql = f"""
            SELECT
                a.art_codigo,
                b.ART_NOMBRE,
                ubi.ubi_nombre AS ubicacion,
                SUM(CASE WHEN a.mom_tipmov='E' THEN a.mom_cant ELSE -a.mom_cant END) AS mom_cant
            FROM
                movm{datetime.now().year} AS a
                INNER JOIN t_articulo AS b ON a.ART_CODIGO = b.art_codigo
                LEFT JOIN t_ubicacion AS ubi ON a.UBI_COD1 = ubi.ubi_codigo
            WHERE
                a.UBI_COD1 IN ({','.join(f"'{i}'" for i in ubis)})
                AND a.elimini = 0
                AND b.art_mansto = 0
                AND a.alm_codigo = ?
            GROUP BY
                a.art_codigo, b.ART_NOMBRE, ubi.ubi_nombre, a.col_codigo, a.mom_lote, a.tal_codigo, a.UBI_COD1
            ORDER BY
                b.ART_NOMBRE

            """
        if int(talla) == 1:
            sql = f"""
                select art_codigo,tal_codigo,'mom_cant'=sum(mom_cant),art_nombre,PA1_CODIGO,
                    PA2_CODIGO,
                    PA3_CODIGO,
					PA4_CODIGO,
                    tem_codigo,
					art_partes
					 from
                (SELECT
                    a.art_codigo,
                    c.ume_nombre,
                    a.tal_codigo,
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
                                                FROM movm{anio} z 
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
                    a.ALM_CODIGO,
                    a.UBI_COD1,
                    b.PA1_CODIGO,
                    b.PA2_CODIGO,
                    b.PA3_CODIGO,
                    b.PA4_CODIGO,
                    b.tem_codigo,
                    b.art_partes
                FROM movm{anio} a 
                LEFT JOIN t_articulo b ON a.ART_CODIGO=b.art_codigo 
                LEFT JOIN t_umedida c ON b.ume_precod=c.ume_codigo
                WHERE 
                    a.UBI_COD1 IN ({','.join(f"'{i}'" for i in ubis)})
                    AND a.elimini=0 
                    AND b.art_mansto=0 
                    AND a.ALM_CODIGO=?
                    
                    
                GROUP BY 
                    a.art_codigo, 
                    b.art_partes,
                    b.ART_NOMBRE, 
                    c.ume_nombre, 
                    a.ALM_CODIGO, 
                    a.UBI_COD1, 
                    b.art_mansto, 
                    a.tal_codigo,
                    b.PA1_CODIGO,
                    b.PA2_CODIGO,
                    b.PA3_CODIGO,
                    b.PA4_CODIGO,
                    b.tem_codigo
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
                                    FROM movm{anio} z 
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
                    ) <> 0 ) as az
                    group by az.art_codigo,az.art_nombre,az.tal_codigo,az.ume_nombre,az.alm_codigo,az.PA1_CODIGO,
                    az.PA2_CODIGO,
                    az.PA3_CODIGO,
					az.PA4_CODIGO,
                    az.tem_codigo,
					az.art_partes
                ORDER BY az.art_nombre, az.ume_nombre"""

        conn = QuerysDb.conexion(host,db,user,password)
        datos = self.querys(conn,sql,(alm,))
       
        if int(talla)==0:
            data = self.StockOffTallas(datos)
            return Response(data)
        if len(datos)==0:
            return Response({'error':'Almacen o ubicacion sin articulos'})
        stock = [
            {
                'id': index,
                'codigo': value[0].strip(),
                'talla': value[1].strip(),
                'stock': value[2],
                'nombre': value[3].strip(),
                'genero':value[4].strip(),
                'linea':value[5].strip(),
                'modelo':value[6].strip(),
                'color':value[7].strip(),
                'temporada':value[8].strip(),
                'parte':value[9]
            }
            for index, value in enumerate(datos)
        ]
        try:
            g = set([i['genero'] for i in stock if i['genero']!=''])
        
            sql = f"""SELECT pa1_nombre, pa1_codigo FROM t_parte1 WHERE alm_codigo = ? AND pa1_codigo IN ({','.join(f"'{i}'" for i in g)}) ORDER BY pa1_nombre;"""
        
            datos = self.querys(conn,sql,(alm,))
            genero = [
                {
                    'label':value[0],
                    'value':value[1],
                    'id':index
                }
                for index,value in enumerate(datos)
            ]
        except:
            genero = []

        try:

            l = set([i['linea'] for i in stock])
            sql = f"""select pa2_nombre,pa2_codigo from t_parte2 where alm_codigo=? AND pa2_codigo IN ({','.join(i for i in l)}) order by pa2_nombre"""
            datos = self.querys(conn,sql,(alm,))
            linea = [{'label':'LINEA',"value":'A'}]+[
                {
                    'label':value[0],
                    'value':value[1].strip(),
                    'id':index
                }
                for index,value in enumerate(datos)
            ]
        except:
            linea = [{'label':'LINEA',"value":'A'}]
        try:
            m = set([i['modelo'] for i in stock])
            sql = f"""select pa3_nombre,pa3_codigo from t_parte3 where alm_codigo=?  AND pa3_codigo IN ({','.join(i for i in m)}) order by pa3_nombre"""
            datos = self.querys(conn,sql,(alm,))

            modelo =[{'value':'A',"label":"MODELO"}]+ [
                {
                    'label':value[0],
                    'value':value[1],
                    'id':index
                }
                for index,value in enumerate(datos)
            ]
        except:
            modelo = [{'value':'A',"label":"MODELO"}]
        try:

            c = set([i['color'] for i in stock])
            sql = f"""select pa4_nombre,pa4_codigo from t_parte4 where alm_codigo=? AND pa4_codigo IN ({','.join(i for i in c)}) order by pa4_nombre"""
            datos = self.querys(conn,sql,(alm,))
            color = [{'label':'COLOR',"value":'A'}]+[
                {
                    'label':value[0],
                    'value':value[1].strip(),
                    'id':index
                }
                for index,value in enumerate(datos)
            ]
        except:
            color = [{'label':'COLOR',"value":'A'}]
        try:
            t  = set([i['temporada']  for i in stock if i['temporada'].strip()!=''])
            
            sql = f"""select tem_nombre,tem_codigo from t_temporada WHERE  tem_codigo IN ({','.join(i for i in t)}) order by tem_nombre"""
            datos = self.querys(conn,sql,())

            temporada = [{'label':'TEMPORADA',"value":'A'}]+[
                {
                    'label':value[0],
                    'value':value[1].strip(),
                    'id':index
                }
                for index,value in enumerate(datos)
            ]
        except :
            temporada = [{'label':'TEMPORADA',"value":'A'}]
        try:
            tl = set([i['talla'] for i in stock])
            sql = f"""select tal_nombre,tal_codigo from t_tallas WHERE tal_codigo IN ({",".join(f"'{i}'" for i in tl)}) order by tal_nombre"""

            datos = self.querys(conn,sql,())
            tallas =[{'label':'TALLA',"value":'A'}]+[
                {
                    'label':value[0],
                    'value':value[1].strip(),
                    'id':index
                }
                for index,value in enumerate(datos)
            ]
        except:
            tallas = [{'label':'TALLA',"value":'A'}]
        conn.commit()
        conn.close()
        return Response({'stock':stock,'genero':genero,'linea':linea,'modelo':modelo,'color':color,'temporada':temporada,'talla':tallas})
    def post(self,request,*args,**kwargs):
        data = {}
        try:
           
            datos = request.data
        
            self.credencial = Credencial(datos["credencial"])
            sql = ''
            if datos["credencial"]["codigo"]=='1':
                sql = self.stock_with_tallas()
            else:
                sql = self.stock_off_tallas()
            params = (datos["almacen"],)
            s,result = CAQ.request(self.credencial,sql,params,'get',1)
      
            if not s:
                raise Exception(result["error"])
            if datos["credencial"]["codigo"]=='1':
                stock = self.StockWithTallas(result)
                data = self.filters(stock,datos["almacen"],data)
            else:
                data = self.StockOffTallas(result)

        except Exception as e:
            data["errro"] = f"Ocurrio un errror: {str(e)}"
        return Response(data)
    def filters(self,stock,alm,data):
        try:
            g = set([i['genero'] for i in stock if i['genero']!=''])
        
            sql = f"""SELECT pa1_nombre, pa1_codigo FROM t_parte1 WHERE alm_codigo = ? AND pa1_codigo IN ({','.join(f"'{i}'" for i in g)}) ORDER BY pa1_nombre;"""
        
            s,datos =CAQ.request(self.credencial,sql,(alm,),"get",1) 
            genero = [
                {
                    'label':value[0],
                    'value':value[1],
                    'id':index
                }
                for index,value in enumerate(datos)
            ]
        except:
            genero = []

        try:

            l = set([i['linea'] for i in stock])
        
            sql = f"""select pa2_nombre,pa2_codigo from t_parte2 where alm_codigo=? AND pa2_codigo IN ({','.join(f"'{i}'" for i in l)}) order by pa2_nombre"""
            s,datos = CAQ.request(self.credencial,sql,(alm,),"get",1)
            
            linea = [{'label':'LINEA',"value":'A'}]+[
                {
                    'label':value[0],
                    'value':value[1].strip(),
                    'id':index
                }
                for index,value in enumerate(datos)
            ]
        except:
            linea = [{'label':'LINEA',"value":'A'}]
        try:
            m = set([i['modelo'] for i in stock])
            sql = f"""select pa3_nombre,pa3_codigo from t_parte3 where alm_codigo=?  AND pa3_codigo IN ({','.join(f"'{i}'" for i in m)}) order by pa3_nombre"""
            s,datos = CAQ.request(self.credencial,sql,(alm,),"get",1)

            modelo =[{'value':'A',"label":"MODELO"}]+ [
                {
                    'label':value[0],
                    'value':value[1],
                    'id':index
                }
                for index,value in enumerate(datos)
            ]
        except:
            modelo = [{'value':'A',"label":"MODELO"}]
        try:

            c = set([i['color'] for i in stock])

            sql = f"""select pa4_nombre,pa4_codigo from t_parte4 where alm_codigo=? AND pa4_codigo IN ({','.join(f"'{i}'" for i in c)}) order by pa4_nombre"""
            s,datos = CAQ.request(self.credencial,sql,(alm,),"get",1)
            color = [{'label':'COLOR',"value":'A'}]+[
                {
                    'label':value[0],
                    'value':value[1].strip(),
                    'id':index
                }
                for index,value in enumerate(datos)
            ]
        except:
            color = [{'label':'COLOR',"value":'A'}]
        try:
            t  = set([i['temporada']  for i in stock if i['temporada'].strip()!=''])
         
            sql = f"""select tem_nombre,tem_codigo from t_temporada WHERE  tem_codigo IN ({','.join(f"'{i}'" for i in t)}) order by tem_nombre"""
            _,datos = CAQ.request(self.credencial,sql,(),"get",1)

            temporada = [{'label':'TEMPORADA',"value":'A'}]+[
                {
                    'label':value[0],
                    'value':value[1].strip(),
                    'id':index
                }
                for index,value in enumerate(datos)
            ]
        except :
            temporada = [{'label':'TEMPORADA',"value":'A'}]
        try:
            tl = set([i['talla'] for i in stock])
            sql = f"""select tal_nombre,tal_codigo from t_tallas WHERE tal_codigo IN ({','.join(f"'{i}'" for i in tl)}) order by tal_nombre"""

            s,datos = CAQ.request(self.credencial,sql,(),"get",1)

            tallas =[{'label':'TALLA',"value":'A'}]+[
                {
                    'label':value[0],
                    'value':value[1].strip(),
                    'id':index
                }
                for index,value in enumerate(datos)
            ]
        except:
            tallas = [{'label':'TALLA',"value":'A'}]
        
        return {"stock":stock,"genero":genero,"linea":linea,"modelo":modelo,"color":color,"temporada":temporada,"talla":tallas}
    def stock_off_tallas(self):
        ubicaciones = ','.join(f"'{i}'" for i in self.request.data["lista_ubicaciones"])
        sql = f"""
                SELECT
                    a.art_codigo,
                    b.ART_NOMBRE,
                    ubi.ubi_nombre AS ubicacion,
                    SUM(CASE WHEN a.mom_tipmov='E' THEN a.mom_cant ELSE -a.mom_cant END) AS mom_cant
                FROM
                    movm{datetime.now().year} AS a
                    INNER JOIN t_articulo AS b ON a.ART_CODIGO = b.art_codigo
                    LEFT JOIN t_ubicacion AS ubi ON a.UBI_COD1 = ubi.ubi_codigo
                WHERE
                    a.UBI_COD1 IN ({ubicaciones})
                    AND a.elimini = 0
                    AND b.art_mansto = 0
                    AND a.alm_codigo = ?
                GROUP BY
                    a.art_codigo, b.ART_NOMBRE, ubi.ubi_nombre, a.col_codigo, a.mom_lote, a.tal_codigo, a.UBI_COD1
                ORDER BY
                    b.ART_NOMBRE
        """
        return sql
    def stock_with_tallas(self):
        anio = datetime.now().year
        data = self.request.data
        ubicaciones = ','.join(f"'{i}'" for i in data["lista_ubicaciones"])
        filters = ''
        if len(data["lista_generos"])!=0:
            generos = ','.join(f"'{i}'" for i in data["lista_generos"])
            filters+=f"AND b.PA1_CODIGO IN ({generos}) "
        if len(data["lista_lineas"])!=0:
            lineas = ','.join(f"'{i}'" for i in data["lista_lineas"])
            filters+=f"AND b.PA2_CODIGO IN ({lineas})"
        if len(data["lista_modelos"])!=0:
            modelos = ','.join(f"'{i}'" for i in data["lista_modelos"])
            filters+=f"AND b.PA3_CODIGO IN ({modelos})"
        if len(data["lista_colores"])!=0:
            colores = ','.join(f"'{i}'" for i in data["lista_colores"])
            filters+=f"AND b.PA4_CODIGO IN ({colores})"
        if len(data["lista_temporada"])!=0:
            temporada = ','.join(f"'{i}'" for i in data["lista_temporada"])
            filters+=f"AND b.tem_codigo IN ({temporada})"
        if len(data["lista_tallas"])!=0:
            tallas = ','.join(f"'{i}'" for i in data["lista_tallas"])
            filters+=f"AND a.tal_codigo IN ({tallas})"
        sql = f"""
        SELECT art_codigo,tal_codigo,'mom_cant'=sum(mom_cant),art_nombre,PA1_CODIGO,
                    PA2_CODIGO,
                    PA3_CODIGO,
					PA4_CODIGO,
                    tem_codigo,
					art_partes
					 from
                (SELECT
                    a.art_codigo,
                    c.ume_nombre,
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
                                                FROM movm{anio} z 
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
                    ,
                    b.ART_NOMBRE,
                    a.ALM_CODIGO,
                    a.UBI_COD1,
                    b.PA1_CODIGO,
                    b.PA2_CODIGO,
                    b.PA3_CODIGO,
                    b.PA4_CODIGO,
                    b.tem_codigo,
                    b.art_partes
                FROM movm{anio} a 
                LEFT JOIN t_articulo b ON a.ART_CODIGO=b.art_codigo 
                LEFT JOIN t_umedida c ON b.ume_precod=c.ume_codigo
                WHERE 
                    a.ALM_CODIGO=?
                    AND a.UBI_COD1 IN ({ubicaciones})
                    {filters}
                    AND a.elimini=0 
                    AND b.art_mansto=0   
                GROUP BY 
                    a.art_codigo, 
                    b.art_partes,
                    b.ART_NOMBRE, 
                    c.ume_nombre, 
                    a.ALM_CODIGO, 
                    a.UBI_COD1, 
                    b.art_mansto, 
                    a.tal_codigo,
                    b.PA1_CODIGO,
                    b.PA2_CODIGO,
                    b.PA3_CODIGO,
                    b.PA4_CODIGO,
                    b.tem_codigo
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
                                    FROM movm{anio} z 
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
                    ) <> 0 ) as az
                    group by az.art_codigo,az.art_nombre,az.tal_codigo,az.ume_nombre,az.alm_codigo,az.PA1_CODIGO,
                    az.PA2_CODIGO,
                    az.PA3_CODIGO,
					az.PA4_CODIGO,
                    az.tem_codigo,
					az.art_partes
                ORDER BY az.art_nombre, az.ume_nombre

        """
        return sql 
    def querys(self,conn,sql,params):
        cursor = conn.cursor()
        cursor.execute(sql,params)
        data = cursor.fetchall()
        return data
    def StockWithTallas(self,datos):
        stock = [
            {
                
                'id': index,
                'codigo': value[0].strip(),
                'talla': value[1].strip(),
                'stock': value[2],
                'nombre': value[3].strip(),
                'genero':value[4].strip(),
                'linea':value[5].strip(),
                'modelo':value[6].strip(),
                'color':value[7].strip(),
                'temporada':value[8].strip(),
                'parte':value[9]
            }
            for index, value in enumerate(datos)  
        ]
        return stock
    def StockOffTallas(self,datos):
       
        stock = [
            {
                'id': index,
                'codigo': value[0].strip(),
                'nombre': value[1].strip(),
                'ubicacion': value[2].strip(),
                'stock': value[3],
            }
            for index, value in enumerate(datos)
        ]
        
        return {'stock':stock,'genero':[],'linea':[],'modelo':[],'color':[],'temporada':[],'talla':[]}
class StockReview(generics.GenericAPIView):
    credencial : object = None
    def get(self,request,*args,**kwargs):
        
        host = kwargs['host']
        db = kwargs['db']
        user = kwargs['user']
        password = kwargs['password']
        pedido_numero = kwargs['pedido']
        ubicacion = kwargs['ubi']
        almacen = kwargs['alm']
        codigo = kwargs['codigo']
        talla = kwargs['talla']
        anio = datetime.now().year
        respuesta = {}
        params = (codigo,almacen,ubicacion)
        if talla!='x':
            params = (codigo,almacen,ubicacion,talla)

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
                    {'AND tal_codigo=?'if talla!='x' else ''}
                """
   
        conn = QuerysDb.conexion(host,db,user,password)
        data = self.querys(conn,sql,params)
        respuesta['stock_real'] = round(data[0],2)
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
                        {'AND tal_codigo = ?' if talla!='x' else ''}
                        AND a.elimini = 0
                        AND b.ped_status = 2
                        AND ped_statu2 = 2
                        AND b.ped_cierre = 0
                    GROUP BY b.mov_compro, a.art_codigo, a.tal_codigo, b.ubi_codig2, b.ubi_codigo
                ) AS zzz;

                """
       
       
        data = self.querys(conn,sql,params)
        respuesta['p_aprobados'] = round(data[0],2)
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
                        {' AND tal_codigo = ?' if talla!='x' else ''}
                        
                        AND a.elimini = 0
                        AND b.ped_status IN (0, 1)
                        AND ped_statu2 IN (0, 1)
                        AND b.ped_cierre = 0
                    GROUP BY b.mov_compro, a.art_codigo, a.tal_codigo, b.ubi_codig2, b.ubi_codigo
                ) AS zzz;
            """
      
        if pedido_numero!='x':
            if talla == 'x':
                params = (pedido_numero,codigo,almacen,ubicacion,pedido_numero)
            else:
                params = (pedido_numero,codigo,almacen,ubicacion,talla,pedido_numero)

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
                                AND zz.mov_compro <> ?
                        )
                        FROM movipedido a
                        INNER JOIN cabepedido b ON a.mov_compro = b.MOV_COMPRO
                        WHERE a.art_codigo = ?
                            AND b.ubi_codig2 = ?
                            AND b.ubi_codigo = ?
                            
                           { 'AND tal_codigo = ?' if talla!='x' else ''}
                            AND b.mov_compro <> ?
                            AND a.elimini = 0
                            AND b.ped_status IN (0, 1)
                            AND ped_statu2 IN (0, 1)
                            AND b.ped_cierre = 0
                        GROUP BY b.mov_compro, a.art_codigo, a.tal_codigo, b.ubi_codig2, b.ubi_codigo
                    ) AS zzz;

                    """

        data = self.querys(conn,sql,params)
        respuesta['p_pendientes'] = round(data[0],2)
        conn.commit()
        conn.close()
        return Response(respuesta)
    def post(self,request,*args,**kwagrs):
        datos = request.data
        self.credencial = Credencial(datos['credencial'])
        try:
            
            pedido_numero = datos['pedido']
            ubicacion = datos['ubicacion']
            almacen = datos['almacen']
            codigo = datos['codigo']
            talla = datos['talla']
            lote = datos['lote']
            fecha = datos['fecha']
            fecha_date = "-".join(i for i in reversed(fecha.split('/')))
            anio = datetime.now().year
            data = {}
          
            params = (codigo,almacen,ubicacion)


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
                            f"AND mom_lote='{fecha_date}' " if fecha!='' else ''
                        }
                    """
            s,date = CAQ.request(self.credencial,sql,params,'get',0)

            if not s:
                raise
            data['stock_real'] = round(float(date[0]),2)
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
                                f"AND a.tal_codigo ='{talla}' " if talla!='x' else ''
                                
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
        
        
            s,date = CAQ.request(self.credencial,sql,params,'get',0)
            if not s:
                raise
            data['p_aprobados'] = round(float(date[0]),2)
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
                                f"AND b.mov_compro<>'{pedido_numero}' " if pedido_numero!='x' else ''
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
        
        
            s,date = CAQ.request(self.credencial,sql,params,'get',0)
   
            data['p_pendientes'] = round(float(date[0]),2)


        except Exception as e:
            data["error"] = f"Error en stock {str(e)}"
            logger.error('An error occurred: %s', e)

        return Response(data)
    def querys(self,conn,sql,params):
        cursor= conn.cursor()
        cursor.execute(sql,params)
        data = cursor.fetchone()
        return data