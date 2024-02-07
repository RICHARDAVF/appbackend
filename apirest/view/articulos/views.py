from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from datetime import datetime
from apirest.crendeciales import Credencial

from apirest.querys import CAQ
class ArticuloStock(GenericAPIView):
    anio = datetime.now().year
    credencial = None
    def post(self,request,*args,**kwargs):
        data = {}
        self.credencial = Credencial(request.data['credencial'])
        try:
            datos = request.data
           
            if datos['almacen']=='':
                data['error'] = 'Seleccione un almacen'
                return Response(data)
            if datos['ubicacion']=='':
                data['error'] = 'Seleccione una ubicacion'
                return Response(data)
            if int(datos['credencial']['codigo']) in [1,2,3]:
          
                sql = self.art_with_separacion()
            else:
                
                sql = self.art_off_separacion()
            params = (datos['almacen'],datos['ubicacion'])
        
            s,result = CAQ.request(self.credencial,sql,params,'get',1)
            if not s:
                data = result
                return Response(data)
        
            data= [
                {
                    'id':index,
                    'codigo':item[0].strip(),
                    'talla':item[1].strip(),
                    'stock':item[2],
                    'nombre':item[3].strip(),
                    'moneda':item[4].strip(),
                    'peso':item[5],
                    'vendedor':item[6].strip()

                }
                for index,item in enumerate(result)
            ]
            
        except Exception as e:
            print(str(e))
            data['error'] = 'Ocurrio un error al recuperar los articulos'
        return Response(data)

    def art_with_separacion(self):
        codigo = self.request.data['codigo']
       
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
                                                FROM movm{self.anio} z 
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
                    'lis_moneda' = ISNULL((SELECT par_moneda FROM t_parrametro WHERE par_anyo=YEAR(GETDATE())), ''),
                    a.ALM_CODIGO,
                    a.UBI_COD1,
                    b.art_peso,
                    b.ven_codigo
                    
                FROM movm{self.anio} AS a 
                LEFT JOIN t_articulo b ON a.ART_CODIGO=b.art_codigo 
                LEFT JOIN t_umedida c ON b.ume_precod=c.ume_codigo
                WHERE a.elimini=0 
                    AND b.art_mansto=0 
                    AND a.ALM_CODIGO=?
                    AND a.UBI_COD1=? 
                    {
                        f"AND ltrim(rtrim(a.mov_pedido))<>'{codigo.strip()}' " if codigo.strip()!='x' else ''
                    }
                GROUP BY a.art_codigo, b.ART_NOMBRE, c.ume_nombre, a.ALM_CODIGO, a.UBI_COD1, b.art_peso, b.art_mansto, a.tal_codigo,b.ven_codigo
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
                                    FROM movm{self.anio} AS z 
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
                ORDER BY b.art_nombre, c.ume_nombre"""
       
        return sql
    def art_off_separacion(self):
        codigo = self.request.data['codigo']
        sql = f"""
                SELECT
                        b.art_codigo,
                        a.tal_codigo,
                        'mom_cant' = SUM(CASE WHEN a.mom_tipmov = 'E' THEN a.mom_cant WHEN a.mom_tipmov = 'S' THEN a.mom_cant * -1 END),
                        b.ART_NOMBRE,        
                        'lis_moneda' = ISNULL((SELECT par_moneda FROM t_parrametro WHERE par_anyo = DATEPART(YEAR, GETDATE())), ''),   
                        b.art_peso,
                        b.ven_codigo
                    FROM
                        movm{self.anio} AS a
                    LEFT JOIN
                        t_articulo b ON a.ART_CODIGO = b.art_codigo
                    LEFT JOIN
                        t_umedida c ON b.ume_precod = c.ume_codigo
                    WHERE
                        a.elimini = 0
                        AND b.art_mansto = 0
                        AND a.ALM_CODIGO = ?
                        AND a.UBI_COD1 = ?
                        {
                            f'AND a.mov_pedido<>{codigo}' if codigo!='x' else ''
                        }
                    GROUP BY
                        b.art_codigo,
                        b.ART_NOMBRE,
                        c.ume_nombre,
                        a.ALM_CODIGO,
                        a.UBI_COD1,
                        a.tal_codigo,
                        b.art_peso,
                        b.ven_codigo                                
                    HAVING
                        SUM(CASE WHEN a.mom_tipmov = 'E' THEN a.mom_cant WHEN a.mom_tipmov = 'S' THEN a.mom_cant * -1 END) <> 0
                    ORDER BY
                        b.art_nombre,
                        c.ume_nombre
                                    
                """
        return sql
class ArticulosConTalla(GenericAPIView):
    anio = datetime.now().year
    credencial = None
    def post(self,request,*args,**kwargs):
        data = {}
        self.credencial = Credencial(request.data['credencial'])
        datos = request.data
        try:
            sql = f"""SELECT
                    a.tal_codigo,
                    'mom_cant' = SUM(CASE
                                        WHEN a.mom_tipmov = 'E' THEN a.mom_cant
                                        WHEN a.mom_tipmov = 'S' THEN a.mom_cant * -1
                                    END) - (
                                        SELECT 'mom_cant' = ISNULL(SUM(zzz.mom_cant), 0)
                                        FROM (
                                            SELECT 'mom_cant' = ISNULL(SUM(x.mom_cant), 0) + (
                                                SELECT ISNULL(SUM(CASE
                                                                    WHEN z.mov_pedido = '' THEN 0
                                                                    WHEN z.mom_tipmov = 'E' THEN z.mom_cant
                                                                    ELSE -z.mom_cant
                                                                END), 0)
                                                FROM movm{self.anio}z
                                                    LEFT JOIN cabepedido zz ON z.mov_pedido = zz.mov_compro
                                                WHERE y.mov_compro = z.mov_pedido
                                                    AND x.art_codigo = z.art_codigo
                                                    AND x.tal_codigo = z.tal_codigo
                                                    AND y.ubi_codig2 = z.alm_codigo
                                                    AND y.ubi_codigo = z.ubi_cod1
                                                    AND z.elimini = 0
                                                    AND zz.elimini = 0
                                                    AND zz.ped_cierre = 0
                                            )
                                            FROM movipedido x
                                                INNER JOIN cabepedido y ON x.mov_compro = y.mov_compro
                                            WHERE x.art_codigo = a.art_codigo
                                                AND y.ubi_codig2 = a.alm_codigo
                                                AND y.ubi_codigo = a.ubi_cod1
                                                AND x.tal_codigo = a.tal_codigo
                                                AND x.elimini = 0
                                                AND y.ped_cierre = 0
                                            GROUP BY y.mov_compro, x.art_codigo, x.tal_codigo, y.ubi_codig2, y.ubi_codigo
                                        ) AS zzz
                                    ),
                    a.art_codigo,
                    b.art_nombre
                FROM
                    movm{self.anio} a
                    LEFT JOIN t_articulo b ON a.art_codigo = b.art_codigo
                    LEFT JOIN t_umedida c ON b.ume_precod = c.ume_codigo
                WHERE
                    a.elimini = 0
                    AND b.art_mansto = 0
                    AND a.ALM_CODIGO = ?
                    AND a.UBI_COD1 = ?
                    AND SUBSTRING(a.art_codigo, 1, 7) = ?
                GROUP BY
                    a.art_codigo,
                    b.art_nombre,
                    a.alm_codigo,
                    a.ubi_cod1,
                    b.art_peso,
                    b.art_mansto,
                    a.tal_codigo
                HAVING
                    SUM(CASE
                            WHEN a.mom_tipmov = 'E' THEN a.mom_cant
                            WHEN a.mom_tipmov = 'S' THEN a.mom_cant * -1
                        END) - (
                            SELECT 'mom_cant' = ISNULL(SUM(zzz.mom_cant), 0)
                            FROM (
                                SELECT 'mom_cant' = ISNULL(SUM(x.mom_cant), 0) + (
                                    SELECT ISNULL(SUM(CASE
                                                        WHEN z.mov_pedido = '' THEN 0
                                                        WHEN z.mom_tipmov = 'E' THEN z.mom_cant
                                                        ELSE -z.mom_cant
                                                    END), 0)
                                    FROM movm{self.anio} z
                                        LEFT JOIN cabepedido zz ON z.mov_pedido = zz.mov_compro
                                    WHERE y.mov_compro = z.mov_pedido
                                        AND x.art_codigo = z.art_codigo
                                        AND x.tal_codigo = z.tal_codigo
                                        AND y.ubi_codig2 = z.alm_codigo
                                        AND y.ubi_codigo = z.ubi_cod1
                                        AND z.elimini = 0
                                        AND zz.elimini = 0
                                        AND zz.ped_cierre = 0
                                )
                                FROM movipedido x
                                    INNER JOIN cabepedido y ON x.mov_compro = y.mov_compro
                                WHERE x.art_codigo = a.art_codigo
                                    AND y.ubi_codig2 = a.alm_codigo
                                    AND y.ubi_codigo = a.ubi_cod1
                                    AND x.tal_codigo = a.tal_codigo
                                    AND x.elimini = 0
                                    AND y.ped_cierre = 0
                                GROUP BY y.mov_compro, x.art_codigo, x.tal_codigo, y.ubi_codig2, y.ubi_codigo
                            ) AS zzz
                        ) <> 0
                ORDER BY
                    b.art_nombre
                """
            params = (datos['almacen'],datos['ubicacion'],datos['codigo'][:-2])
            s,result = CAQ.request(self.credencial,sql,params,'get',1)
            if not s:
                data['error'] = 'Ocurrio un error al recuperar los articulos'
                return Response(data)
            
        except Exception as e:
            print(str(e))
            data['error'] = 'Ocurrio un error al recuperar los articulos'
        return Response(data)
    def grouped_data(self):
        return