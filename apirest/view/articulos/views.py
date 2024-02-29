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
            if datos['config']['separacion_pedido']:
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
        caida_codigo = self.request.data['caida_codigo']
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
                    {
                        f"AND b.PA1_CODIGO='{caida_codigo}' " if caida_codigo!='' else  ''
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
class ArticuloLote(GenericAPIView):
    credencial : object = None
    def post(self,request,*args,**kwargs):
        data = {}
        datos = request.data
       
        try:
            self.credencial = Credencial(datos['credencial'])
            
            if request.data['almacen']=='':
                raise Exception('No existe almacen')
            codigo,lote,fecha_vencimiento = self.codigo_lote_fecha()
            sql = f"""SELECT 
                    art_codigo,
                    art_nombre,
                    'moneda'=ISNULL((SELECT par_moneda FROM t_parrametro WHERE par_anyo=YEAR(GETDATE())), ''),
                    art_peso 
                FROM t_articulo WHERE ART_CODIGO=? """
            s,result = CAQ.request(self.credencial,sql,(codigo,),'get',0)
  
            if not s or result is None:
                raise Exception('Articulo no encontrado')
            data = {
                    "codigo":result[0].strip(),
                    "nombre":result[1].strip(),
                    "moneda":result[2].strip(),
                    "peso":result[3],
                    "talla":"",
                    "vendedor":"",
                    "lote":lote,
                    "fecha":fecha_vencimiento
                    }         
        except Exception as e:
            
            data['error'] = str(e)
        return Response(data)
    def codigo_lote_fecha(self):
        codigo_qr = self.request.data['lote']
        sql = f"""
            SELECT  'longitud' = cre_long1+cre_long2+cre_long3+cre_long4+cre_long5+cre_long7+cre_long8 
            FROM t_creacodigo 
            WHERE alm_codigo=?"""
  
        s,result = CAQ.request(self.credencial,sql,(self.request.data['almacen'],),'get',0)
        if not s:
            raise
        try:
            longitud = int(result[0])
            codigo = codigo_qr[:longitud]
            fecha_vencimiento = codigo_qr[-10:]
            lote = codigo_qr[longitud:-10]
        except:
            raise Exception('Codigo QR no valido')
        return (codigo,lote,fecha_vencimiento)
class ArticulosFacturacion(GenericAPIView):
    credencial : object = None
    lote : str =  ''
    fecha : str = ''
    codigo : str = ''
    def post(self,request,*args,**kwargs):
        data = {}
        datos = request.data
        self.credencial = Credencial(datos['credencial'])
        ubicacion = datos['ubicacion']
        qr_code = datos['qr_codigo'] if 'qr_codigo' in datos else ''
        try:
            if qr_code!='':
                self.codigo_lote_fecha()
            sql = f"""
                    SELECT 
                        a.art_codigo,
                        a.art_nombre,
                        'precio'=ISNULL(b.lis_pmino, ISNULL(c.lis_pmino, 0)),
                        a.art_provee,
                        'des_max'=ISNULL(b.lis_mindes, ISNULL(c.lis_mindes, 0)),
                        'min_des'=ISNULL(b.lis_maxdes, ISNULL(c.lis_maxdes, 0)),
                        a.pla_almain
                    FROM 
                        t_articulo a 
                    LEFT JOIN 
                        maelista_ubicacion b 
                    ON 
                        a.art_codigo = b.art_codigo 
                        AND CAST(GETDATE() AS date) BETWEEN CAST(b.lis_fini AS date) AND CAST(b.lis_ffin AS date) 
                        AND b.lis_tipo = 3 
                        AND b.lis_moneda = 'S'
                        AND b.lis_ubica = '{ubicacion}'
                    LEFT JOIN 
                        maelista c 
                    ON 
                        a.art_codigo = c.art_codigo 
                        AND CAST(GETDATE() AS date) BETWEEN CAST(c.lis_fini AS date) AND CAST(c.lis_ffin AS date) 
                        AND c.lis_tipo = 3 
                        AND c.lis_moneda = 'S'
                    {
                        f"WHERE a.art_codigo='{self.codigo}' " if self.codigo!='' else ''
                    }
                    """
          
            s,result = CAQ.request(self.credencial,sql,(),'get',1)
            if not s:
                raise Exception('Ocurrio un error al recuperar los articulos')
            if result is None:
                raise Exception('No hay articulos para mostrar')

            data = [
                {
                    "id":index,
                    "codigo":value[0].strip(),
                    "nombre":value[1].strip(),
                    "precio":round(float(value[2]),2),
                    "codigo_ena":value[3].strip(),
                    "des_max" :float(value[4]),
                    "des_min" : float(value[5]),
                    "cuenta":value[6].strip(),
                    "lote":self.lote,
                    "fecha":self.fecha

                } for index,value in enumerate(result)
            ]
        except Exception as e:
            data['error'] = str(e)
        return Response(data)
    def codigo_lote_fecha(self):
        codigo_qr = self.request.data['qr_codigo']
        if self.request.data['almacen']=='':
            raise Exception('No tiene un almacen asignado')
        sql = f"""
            SELECT  'longitud' = cre_long1+cre_long2+cre_long3+cre_long4+cre_long5+cre_long7+cre_long8 
            FROM t_creacodigo 
            WHERE alm_codigo=?"""
  
        s,result = CAQ.request(self.credencial,sql,(self.request.data['almacen'],),'get',0)
        if not s:
            raise Exception('Error al consultar con los datos proporcionados')
        try:
           
            longitud = int(result[0])
            codigo = codigo_qr[:longitud]
            fecha_vencimiento = codigo_qr[-10:]
            lote = codigo_qr[longitud:-10]

            self.fecha = self.convert_date_string(fecha_vencimiento)

            self.lote = lote 
            self.codigo= codigo
        except Exception as e:
          
            raise Exception(str(e))
    def validar_fecha(self,date):
      
        try:
            datetime.strptime(date,"%d/%m/%Y")
            return True
        except Exception as e:
            print(str(e))
            return False
    def convert_date_string(self,fecha:str):
        if self.validar_fecha(fecha):
       
            if self.request.data['config']['guid_lote']:
                return fecha
            else:
                return '-'.join(i for i in reversed(fecha.split('/')))
        else:
            raise Exception('Formato de fecha de vencimiento invalida')