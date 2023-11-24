from django.shortcuts import render
from rest_framework import generics,status

from apirest.querys import Querys
from .models import UsuarioCredencial,VersionApp
from .serializer import UsuarioSerializer,VersionAppSerialiser
from rest_framework.response import Response
from .hash import HasPassword
from datetime import datetime
import pyodbc
from numpy import array,char
import requests
class QuerysDb:
    @classmethod
    def conexion(self,dbhost:str,dbname:str,dbuser,dbpassword):
        try:
            conn = pyodbc.connect('DRIVER={SQL Server};SERVER=' +
                               dbhost+';DATABASE='+dbname+';UID='+dbuser+';PWD=' + dbpassword)
            # conn = pyodbc.connect(
            # Trusted_Connection = 'Yes',
            # Driver = '{SQL Server}',
            # Server = dbhost,
            # Database = dbname,
            
            # )
            return conn
        except:
            return None
def index(request):
    return render(request,'index.html')

class VersionAppView(generics.GenericAPIView):
    serializer_class = VersionAppSerialiser
    def get(self,request,*args,**kwargs):
        data = {}
        try:
            version = VersionApp.objects.last()
           
            data['version'] = self.serializer_class(version).data
        except Exception as e:
            data['error'] = f"Ocurrio un error: {str(e)}"
        return Response(data)  
class UserView(generics.GenericAPIView):
    serializer_class = UsuarioSerializer
    def get(self, request, *args, **kwargs):
        
        ruc = kwargs['ruc']
        usuario = kwargs['usuario']
        password = kwargs['password']
        try:
            user = UsuarioCredencial.objects.get(ruc=ruc)
            password = HasPassword(password).hash()
    
            sql  = """SELECT 
                            a.usu_codigo,
                            a.ven_codigo,
                            a.usu_admin,
                            a.usu_autor3,
                            b.ven_nombre,
                            a.ubi_codigo,
                            a.usu_skype,
                            a.usu_alogi1,
                            a.usu_alogi2,
                            a.usu_alogi3,
                            a.usu_rangde,
                            a.usu_rangha,
                            a.usu_nombre,
                            a.usu_aprob1,
                            a.usu_aprob2,
                            a.usu_bconpa,
                            b.ven_email,
                            a.usu_nimpap,
                            a.usu_perped,
                            a.usu_almace
                        FROM t_usuario AS a 
                        LEFT JOIN t_vendedor AS b 
                        ON a.ven_codigo=b.ven_codigo 
                        WHERE 
                            a.USU_ABREV=? AND a.USU_LOGIN=?
                        
                    """
            
            conn = QuerysDb.conexion(user.bdhost,user.bdname,user.bduser,user.bdpassword)
            datos = {}
            if conn is not None:
                data = self.querys(conn,sql,params=(usuario,password))
                if data is  None :
                    datos['message']='Usuario o Contraseña incorrecta'
                    return Response(datos,status=status.HTTP_200_OK)
               
                d = {"cod":data[0][0],'codigo':data[0][1],"is_admin":data[0][2],'ubicacion':data[0][5].strip(),'apro_oc1':data[0][7],'apro_oc2':data[0][8],'apro_oc3':data[0][9],
                     "usuario":data[0][12].strip(),'aprobacion1':data[0][13],
                     'aprobacion2':data[0][14],'almacen':data[0][-1].strip()}
                      
                datos['user'] = d
                
                conn = QuerysDb.conexion(user.bdhost,user.bdname,user.bduser,user.bdpassword)
                sql1  ="""SELECT ALM_CODIGO,ALM_NOMBRE FROM t_almacen WHERE alm_grupo in(1,2) AND alm_nomost=0 ORDER BY ALM_CODIGO"""
                data_alm = self.querys(conn,sql1,())
                if data_alm is not None:
                    alms = []
                    for row in data_alm:
                        a = {'value':row[0],'label':row[1]}
                        alms.append(a)
                    datos['alms']=alms
                params = ()
                sql = """SELECT ubi_codigo,ubi_nombre,ubi_modelo,ubi_manpun,ubi_punsol,agr_codigo from t_ubicacion where modifica=1 order by ubi_codigo"""
                if datos['user']['ubicacion']!='':
                    sql  = "select ubi_codigo,ubi_nombre,ubi_modelo,ubi_manpun,ubi_punsol,agr_codigo from t_ubicacion where ubi_codigo=? or ubi_mosiem=1 order by ubi_mosiem,ubi_codigo"
                    params = (datos['user']['ubicacion'],)
                conn = QuerysDb.conexion(user.bdhost,user.bdname,user.bduser,user.bdpassword)
                ubic = self.querys(conn,sql,params)
                if ubic is not None:
                    ubicacion = []
                    for row in ubic:
                        a = {'value':str(row[0]).strip(),'label':str(row[1]).strip(),'modelo':str(row[2]).strip(),'manpun':str(row[3]).strip(),'punsol':str(row[4]).strip(),'agr_cod':str(row[5]).strip()}
                        ubicacion.append(a)
                    datos['ubicacion'] = ubicacion
                sql3 = """SELECT lis_codigo,lis_nombre FROM t_tipolista ORDER BY lis_codigo"""
                conn = QuerysDb.conexion(user.bdhost,user.bdname,user.bduser,user.bdpassword)
                precios = self.querys(conn,sql3,())
                
                if precios is not None:
                    d=[]
                    for row in precios:
                        a = {'value':row[0],'label':row[1]}
                        d.append(a)
                    datos['precios'] = d
                serializer = self.serializer_class(user)
                datos['creden'] = serializer.data
                return Response(datos,status=status.HTTP_200_OK)
            return Response({'message':'Error de servidor '},status=status.HTTP_424_FAILED_DEPENDENCY)

                
        except UsuarioCredencial.DoesNotExist:
            return Response({'message':'Esta empresa no esta resgitrado'}, status=status.HTTP_404_NOT_FOUND)
    def querys(self,conn,sql,params=()):
        cursor = conn.cursor()
        cursor.execute(sql,params)
        data = cursor.fetchall()
        conn.commit()
        conn.close()
        return  data if len(data)>0 else  None
class ProductoView(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        host = kwargs['host']
        db = kwargs['db']
        user = kwargs['user']
        password = kwargs['password']
        p = kwargs['p']
        m = kwargs['m']
        alm = kwargs['u']
        local = kwargs['l']
        tallas = kwargs['tallas']
        lote = kwargs['lote']
        if int(p)==1:
            p = ''
        else:
            p = int(p)
        conn = QuerysDb.conexion(host,db,user,password)
        params = (m,)
        sql=f"""SELECT lis_pmino{p},lis_moneda,lis_mindes,lis_maxdes,lis_dscto1,lis_dscto2,ART_CODIGO
            FROM maelista WHERE cast(GETDATE() AS date) BETWEEN cast(lis_fini AS date) AND cast(lis_ffin AS date) AND
            lis_tipo IN (1,0) AND lis_moneda=?
            """        
        p = self.querys(conn,sql,params)
       
        if len(p)==0:
            conn = QuerysDb.conexion(host,db,user,password)
            fecha = datetime.now()
            response = requests.get(f'https://api.apis.net.pe/v1/tipo-cambio-sunat?fecha={fecha.year}-{str(fecha.month).zfill(2)}-{str(fecha.day).zfill(2)}')
            if response.status_code ==200:
                data = response.json()
            p=self.querys(conn,sql,('S',))
            for item in range(len(p)):
                p[item][0] = round(float(p[item][0])/float(data['venta']),2)
           
        prices = {}
        for i in p:
            prices[str(i[-1]).strip()] = float(i[0]) if i[0] !=None else 0.00
        if int(tallas)==1:
            sql  = f"""
                 SELECT
                    a.art_codigo,
                    'col_codigo' = '',
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
                                                FROM movm2023 z 
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
                    'col_nombre' = '',
                    'tal_nombre' = '',
                    'lis_pmino' = '0',
                    'lis_moneda' = ISNULL((SELECT par_moneda FROM t_parrametro WHERE par_anyo=YEAR(GETDATE())), ''),
                    a.ALM_CODIGO,
                    a.UBI_COD1,
                    b.art_peso,
                    '0',
                    '0',
                    b.art_mansto,
                    'ven_nombre' = '',
                    'art_codadi' = '',
                    'mom_lote' = '',
                    'art_noprom' = '',
                    'art_norega' = '',
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
                FROM movm{datetime.now().year} AS a 
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
                                    FROM movm{datetime.now().year} AS z 
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
                ORDER BY b.art_nombre, c.ume_nombre, orden

                """
        else:
            sql = f"""
                SELECT
                    b.art_codigo,
                    'col_codigo' = '',
                    'tal_codigo' = '',
                    'mom_cant' = SUM(CASE WHEN a.mom_tipmov = 'E' THEN a.mom_cant WHEN a.mom_tipmov = 'S' THEN a.mom_cant * -1 END),
                    b.ART_NOMBRE,
                    'ume_pres' = ISNULL(c.ume_nombre, ''),
                    'col_nombre' = '',
                    'tal_nombre' = '',
                    'lis_pmino' = '0',
                    'lis_moneda' = ISNULL((SELECT par_moneda FROM t_parrametro WHERE par_anyo = DATEPART(YEAR, GETDATE())), ''),
                    a.ALM_CODIGO,
                    a.UBI_COD1,
                    b.art_peso,
                    '0',
                    '0',
                    b.art_mansto,
                    b.ven_codigo,
                    'art_codadi' = '',
                    'mom_lote' = '',
                    'art_noprom' = '',
                    'art_norega' = ''
                FROM
                    movm{datetime.now().year} AS a
                LEFT JOIN
                    t_articulo b ON a.ART_CODIGO = b.art_codigo
                LEFT JOIN
                    t_umedida c ON b.ume_precod = c.ume_codigo
                WHERE
                    a.elimini = 0
                    AND b.art_mansto = 0
                    {'AND a.ALM_CODIGO = ?' if alm!='x' else ''}
                    AND a.UBI_COD1 = ?
                GROUP BY
                    b.art_codigo,
                    b.ART_NOMBRE,
                    c.ume_nombre,
                    a.ALM_CODIGO,
                    a.UBI_COD1,
                    b.art_peso,
                    b.art_mansto,
                    b.ven_codigo
                HAVING
                    SUM(CASE WHEN a.mom_tipmov = 'E' THEN a.mom_cant WHEN a.mom_tipmov = 'S' THEN a.mom_cant * -1 END) <> 0
                ORDER BY
                    b.art_nombre,
                    c.ume_nombre
            """
        params = (alm,local)
        if alm=='x':
            params = (local,)
        conn = QuerysDb.conexion(host,db,user,password)
        if conn is not None:
            product = array(self.querys(conn,sql,params))
            if len(product)==0:
                return Response({'error':'El local no tiene Productos'})
            serialize_product = []
            if int(tallas)==1:
                codigo = char.strip(product[:, 0].tolist())
                stock = product[:, 3].tolist()
                nombre = char.strip(product[:, 4].tolist())
                precio = array([prices.get(str(code), 0.00) for code in codigo])
                talla = char.strip(product[:, 2].tolist())
                serialize_product = [{'id': index, 'codigo': code, 'stock': st, 'nombre': nom,
                      'precio': pr, 'talla': ta} for index, (code, st, nom, pr, ta) in
                     enumerate(zip(codigo, stock, nombre, precio, talla))]     
            else:
                codigo = char.strip(product[:, 0].tolist())
                stock = product[:, 3].tolist()
                nombre = char.strip(product[:, 4].tolist())
                precio = array([prices.get(str(code), 0.00) for code in codigo])
                serialize_product = [{'id': index, 'codigo': code, 'stock': st, 'nombre': nom,
                      'precio': pr, } for index, (code, st, nom, pr) in
                     enumerate(zip(codigo, stock, nombre, precio))]

            return Response(serialize_product,status=status.HTTP_200_OK)
        return Response({'message':'Error en la base de datos'})
    
 
    def querys(self,conn,sql,params=()):
        cursor = conn.cursor()
        cursor.execute(sql,params)
        datos = cursor.fetchall()
        return datos 
class ClienteView(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        sql = """SELECT aux_razon,aux_clave,aux_docum,aux_direcc,aux_telef,aux_email 
        FROM t_auxiliar WHERE substring(aux_clave,1,1)=? ORDER BY  aux_razon ASC"""
        params = 'C'
        host = kwargs['host']
        db = kwargs['db']
        user = kwargs['user']
        passwrod = kwargs['password']
        
        conn = QuerysDb.conexion(host,db,user,passwrod)
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute(sql,params)
            product = cursor.fetchall()
            serialize_client = []
            for index,row in enumerate(product):
                serialize_client.append({'id':index+1,'nombre':row[0].strip(),'codigo':row[1].strip(),'ruc':row[2].strip(),'direccion':row[3].strip(),'telefono':row[4].strip(),'email':str(row[5]).strip()})      
            return Response(serialize_client,status=status.HTTP_200_OK)
        return Response({'message':'Error en la base de datos'})       
class ProducAddView(generics.GenericAPIView):
   
    def addCabepedio(self,sql,params,cred):
        conn = QuerysDb.conexion(cred['bdhost'],cred['bdname'],cred['bduser'],cred['bdpassword'])
        return self.querys(conn,sql,params,'get')
    def post(self,request,*args,**kwargs):
        datas = request.data
   
        cred = datas['opt']['credencial']
        try:
            sql = "SELECT emp_inclu from t_empresa"
            conn = QuerysDb.conexion(cred['bdhost'],cred['bdname'],cred['bduser'],cred['bdpassword'])
            cursor = conn.cursor()
            cursor.execute(sql,())
            gui_inclu = cursor.fetchone()
            conn.commit()
            conn.close()
        except Exception as e:
            return Response({'message':str(e)})
        total1 = float(datas['opt']['total'])
        total=0
        base_impo=0
        if int(gui_inclu[0])==1:
            total = total1
            base_impo = round(float(total)/1.18,2)
        else:
            base_impo= total1
            total = round(float(base_impo)*1.18,2)
        igv=round(total-base_impo,2)
        try:

            conn = QuerysDb.conexion(cred['bdhost'],cred['bdname'],cred['bduser'],cred['bdpassword'])
            sql = " SELECT TOP 1 MOV_COMPRO FROM cabepedido WHERE SUBSTRING(mov_compro,1,3)=? ORDER BY MOV_COMPRO DESC"
            params = datas['vendedor']['codigo']
            data = self.querys(conn,sql,(params,),'get')[0]
          
            cor = str(params)+'-'+str(int(data[0].split('-')[-1])+1).zfill(7)
        
            sql5 = f"SELECT ope_codigo FROM t_parrametro WHERE par_anyo={datetime.now().year}"
            conn = QuerysDb.conexion(cred['bdhost'],cred['bdname'],cred['bduser'],cred['bdpassword'])
            data = self.querys(conn,sql5,(),'get')        
            fecha = datetime.now().strftime('%Y-%m-%d')

            
            params = (cor,fecha,datas['cabeceras']['codigo'],'S', datas['vendedor']['cod'],datetime.now().strftime('%Y-%m-%d %H:%M:%S'),\
                    total,1,datas['opt']['local'],datas['opt']['tipo'],datas['cabeceras']['direccion'],datas['opt']['precio'],params,\
                    str(data[0][0]).strip(),datas['opt']['almacen'],datas['cabeceras']['ruc'],datas['opt']['obs'],18,igv,base_impo,\
                    gui_inclu[0],'','',datas['tipo_venta'],'F1',0,0,0,0,0,0,datas['agencia'],'',datas['sucursal'],'',datas['nombre'],datas['direccion'],round(self.sumaSDesc(datas['detalle']),2),\
                    abs(round(total1-self.sumaSDesc(datas['detalle']),2)),datas['tipo_envio'])
            sql = """INSERT INTO cabepedido (MOV_COMPRO,MOV_FECHA,MOV_CODAUX,MOV_MONEDA,USUARIO,FECHAUSU,ROU_TVENTA,
            rou_export,ubi_codigo,pag_codigo,gui_direc,lis_codigo,ven_codigo,ope_codigo,ubi_codig2,gui_ruc,
            gui_exp001,ROU_PIGV,ROU_IGV,ROU_BRUTO,gui_inclu,mov_cotiza,aux_nuevo,ped_tipven,doc_codigo,
            gui_aprot1,gui_aprot2,gui_aprot3,gui_aprov1,gui_aprov2,gui_aproc1,tra_codig2,agr_codigo,gui_tienda,
            edp_codigo,gui_tiedir,ped_tiedir,rou_submon,rou_dscto,ped_tipenv) VALUES"""+'('+ ','.join('?' for i in params)+')'
           
            conn = QuerysDb.conexion(cred['bdhost'],cred['bdname'],cred['bduser'],cred['bdpassword'])
            res = self.querys(conn,sql,params,'post')
            sql1 = """INSERT movipedido (ALM_CODIGO,MOM_MES,mov_compro,MOM_FECHA,ART_CODIGO,col_codigo,tal_codigo,MOM_TIPMOV,
                ope_codigo,MOM_CANT,mom_valor,MOM_PUNIT,USUARIO,FECHAUSU,art_afecto,mom_dscto1,gui_inclu,
                mom_conpre,mom_peso,MOM_PUNIT2,doc_codigo,ped_priori,mom_linea,ped_observ,mom_conpro,mom_conreg,
                mom_confle,mom_cofleg,mom_concom,mom_concoa,mom_conpr2,art_codadi,mom_lote,mom_bruto) VALUES
                """
           
            for item in datas['detalle']:
                conn = QuerysDb.conexion(cred['bdhost'],cred['bdname'],cred['bduser'],cred['bdpassword'])
                params = ('53',str(fecha).split('-')[1],cor,fecha,item['codigo'],'',item['talla'],'S',str(data[0][0]).strip(),float(item['cantidad']),float(item['total']),float(item['precio']),\
                          datas['vendedor']['cod'],fecha,'S',float(item['descuento']),gui_inclu[0],'',0,0,'F1','',0,'',0,0,0,0,0,0,0,'','',0) 

                sql = sql1+'('+ ','.join('?' for i in range(len(params)))+')'
            
                res = self.querys(conn,sql,params,'post')
                
            return Response(res,status=status.HTTP_200_OK)
        except Exception as e :
            return Response({'message':str(e)})
    
    def sumaSDesc(self,datos):
        total = 0
        
        for item in datos:
            total+=float(item['cantidad'])*float(item['precio'])
          
        return total

    def querys(self,conn,sql,params=(),opt='get'):
        try:
            cursor = conn.cursor()
            
            if opt =='get':
                cursor.execute(sql,params)
                data = cursor.fetchall()
                conn.commit()
                conn.close()
                return data
            elif opt=='post':
                try:
                    cursor.execute(sql,params)
                    conn.commit()
                    conn.close() 
                    return {'message':'Se Guardo con exito'}
                except Exception as e:
                    return {'message':str(e)}
        except Exception as e:
            return {'message':str(e)}
class EditPedidoView(generics.GenericAPIView):
    def post(self,request,*args,**kwargs):
        data = request.data
        cred = data['credencial']
        conn = QuerysDb.conexion(cred['bdhost'],cred['bdname'],cred['bduser'],cred['bdpassword'])
        sql = "DELETE FROM cabepedido WHERE MOV_COMPRO=?"
        self.querys(conn,sql,(data['codigo_pedido'],),'post')
        conn = QuerysDb.conexion(cred['bdhost'],cred['bdname'],cred['bduser'],cred['bdpassword'])
        sql = "DELETE FROM movipedido WHERE mov_compro=?"
        self.querys(conn,sql,(data['codigo_pedido'],),'post') 
        total=0
        base_impo=0
        if int(data['gui_inclu'])==1:
            total = float(data['total'])
            base_impo = round(float(total)/1.18,2)
        else:
            base_impo= float(data['total'])
            total = round(float(base_impo)*1.18,2)
        igv=round(float(total)-float(base_impo),2)
        sql = f"SELECT ope_codigo FROM t_parrametro WHERE par_anyo={datetime.now().year}"
        conn = QuerysDb.conexion(cred['bdhost'],cred['bdname'],cred['bduser'],cred['bdpassword'])
        ope_codigo = self.querys(conn,sql,(),'get')
        params = (data['codigo_pedido'],datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),data['cabeceras']['codigo'],'S',\
                   data['codigo_usuario'],datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),\
                    total,1,data['local'],data['tipo'],data['cabeceras']['direccion'],data['precio'],data['codigo_usuario'],\
                    str(ope_codigo[0][0]).strip(),data['almacen'],data['cabeceras']['ruc'],data['obs'],18,igv,base_impo,\
                    data['gui_inclu'],data['tipo_venta'],'F1',0,0,0,0,0,0,data['agencia'],data['sucursal'],data['direccion'],data['nombre'],round(self.sumaSDesc(data['detalle']),2),\
                    round(float(data['total'])-self.sumaSDesc(data['detalle']),2),data['tipo_envio'])
        sql = """INSERT INTO cabepedido 
            (MOV_COMPRO,MOV_FECHA,MOV_CODAUX,MOV_MONEDA,USUARIO,FECHAUSU,ROU_TVENTA,
            rou_export,ubi_codigo,pag_codigo,gui_direc,lis_codigo,ven_codigo,ope_codigo,ubi_codig2,gui_ruc,
            gui_exp001,ROU_PIGV,ROU_IGV,ROU_BRUTO,gui_inclu,ped_tipven,doc_codigo,
            gui_aprot1,gui_aprot2,gui_aprot3,gui_aprov1,gui_aprov2,gui_aproc1,tra_codig2,gui_tienda,gui_tiedir,
            ped_tiedir,rou_submon,rou_dscto,ped_tipenv) VALUES"""+'('+ ','.join('?' for i in params)+')'
        c = data['credencial']
        credd = {'host':c['bdhost'],'db':c['bdname'],'user':c['bduser'],'password':c['bdpassword']}
        
        res = Querys(credd).querys(sql,params,'post',0)
      
        sql1 = """INSERT INTO movipedido (ALM_CODIGO,MOM_MES,mov_compro,MOM_FECHA,ART_CODIGO,col_codigo,tal_codigo,MOM_TIPMOV,
            ope_codigo,MOM_CANT,mom_valor,MOM_PUNIT,USUARIO,FECHAUSU,art_afecto,mom_dscto1,gui_inclu,
            mom_conpre,mom_peso,MOM_PUNIT2,doc_codigo,ped_priori,mom_linea,ped_observ,mom_conpro,mom_conreg,
            mom_confle,mom_cofleg,mom_concom,mom_concoa,mom_conpr2,art_codadi,mom_lote,mom_bruto) VALUES
            """
      
        for item in data['detalle']:
            conn = QuerysDb.conexion(cred['bdhost'],cred['bdname'],cred['bduser'],cred['bdpassword'])
            params = ('53',datetime.now().month,data['codigo_pedido'],datetime.now().strftime('%Y-%m-%d'),item['codigo'],'',item['talla'],'S','04',float(item['cantidad']),float(item['total']),float(item['precio']),\
                        data['codigo_usuario'],datetime.now().strftime('%Y-%m-%d'),'S',float(item['descuento']),data['gui_inclu'],'',0,0,'F1','',0,'',0,0,0,0,0,0,0,'','',0) 
            
            sql = sql1+'('+ ','.join('?' for i in range(len(params)))+')'
        
            res = self.querys(conn,sql,params,'post')
        return Response({'message':f'EL pedido {data["codigo_pedido"]} fue editado exitosamente.'} if res =='SUCCESS' else res )

    def get(self,request,*args,**kwargs):
        
        data = {}
        action = kwargs['action']
        try:
            if action == 'c':
                sql = """SELECT a.MOV_CODAUX, a.gui_ruc, a.gui_direc, b.AUX_NOMBRE,a.ubi_codig2,
                    a.ubi_codigo,a.pag_codigo,a.ped_tipenv,a.ped_tipven,a.pag_codigo
                        FROM cabepedido AS a
                        INNER JOIN t_auxiliar AS b ON a.MOV_CODAUX = b.AUX_CLAVE
                        WHERE a.MOV_COMPRO = ?"""
                result = Querys(kwargs).querys(sql,(kwargs['codigo'],),'get',0)
               
                data['cliente']  = {'codigo':result[0].strip(),'ruc':result[1].strip(),'direccion':result[2].strip(),
                         'nombre':result[3].strip(),'tipo_pago':result[6],'tipo_envio':result[7],'tipo_venta':result[8],'tipo_pago':result[9].strip()}
                data['res'] = {'almacen':result[4],'ubicacion':result[5]}
             
            elif action =='a':

              
                sql = """
                        SELECT a.ART_CODIGO, a.MOM_CANT, a.mom_valor, a.MOM_PUNIT, a.mom_dscto1, b.art_nombre,a.tal_codigo
                        FROM movipedido AS a 
                        INNER JOIN t_articulo AS b ON a.ART_CODIGO = b.art_codigo 
                        WHERE a.mov_compro = ?
                    """
        
                
                datos= Querys(kwargs).querys(sql,(kwargs['codigo'],),'get',1)
              
                articulos =[]
                for index,item in enumerate(datos):
                    d={'id':index,'codigo':item[0],'cantidad':item[1],'total':item[2],'precio':item[3],'descuento':item[4],'nombre':item[5].strip(),'talla':item[6].strip()}
                    articulos.append(d)
                data = articulos
            
            elif action == 'al':
                sql = """SELECT MOV_COMPRO,MOV_MONEDA,gui_exp001,gui_inclu,ped_tipven,tra_codig2,gui_tienda,gui_tiedir,ped_tiedir
                        FROM cabepedido WHERE MOV_COMPRO=?"""
                result = Querys(kwargs).querys(sql,(kwargs['codigo'],),'get',0)
                sql = "SELECT tra_nombre FROM t_transporte WHERE TRA_CODIGO=?"
                try:
                    agencia_nombre = Querys(kwargs).querys(sql,(result[5],),'get',0)[0]
                except :
                    agencia_nombre = ''
                data = {'codigo_pedido':result[0].strip(),'moneda':result[1].strip(),'obs':result[2].strip(),'gui_inclu':result[3],
                         'tipo_venta':result[4],'agencia_codigo':result[5].strip(),'agencia_nombre':agencia_nombre.strip(),'entrega_codigo':result[6].strip(),
                         'entrega_nombre':result[7].strip(),'entrega_direccion':result[8].strip()}
        except Exception as e:
            data['error'] = f"Ocurrio un error: {str(e)}"
        return Response(data)
    def querys(self,conn,sql,params,request):
        cursor = conn.cursor()
        cursor.execute(sql,params)
        try:
            if request=='get':
                data = cursor.fetchall()
            elif request=='post':
                data = 'SUCCESS'
            conn.commit()
            conn.close()
            return data
        except Exception as e:
            return str(e)
    def sumaSDesc(self,datos):
        total = 0
        
        for item in datos:
            total+=float(item['cantidad'])*float(item['precio'])
          
        return total
class PedidosView(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        all_items = kwargs['all']

        sql =f"""
        SELECT a.MOV_COMPRO, a.MOV_FECHA,
        ped_status = CASE 
            WHEN a.elimini = 1 THEN 'ANULADO' 
            WHEN (a.ped_status = 3 OR a.ped_statu2 = 3) THEN 'RECHAZADO' 
            WHEN (a.ped_status IN (1, 0) OR a.ped_statu2 IN (1, 0)) THEN 'PENDIENTE' 
            WHEN (a.ped_status = 2 AND a.ped_statu2 = 2) THEN 'APROBADO' 
        END,
        b.aux_razon, a.ROU_BRUTO, a.ROU_IGV, a.ROU_TVENTA,a.ven_codigo,a.MOV_MONEDA,
        COALESCE((SELECT TRA_NOMBRE FROM t_transporte WHERE TRA_CODIGO = a.tra_codig2), '') AS agencia,
        (SELECT TOP 1 mom_dscto1 FROM movipedido WHERE mov_compro = a.MOV_COMPRO) AS descuento,
        a.gui_exp001
        FROM cabepedido AS a 
        INNER JOIN t_auxiliar AS b ON a.MOV_CODAUX = b.aux_clave 
       {"WHERE a.ped_cierre=0 AND a.elimini=0" if all_items==0 else ''}
		ORDER BY MOV_FECHA DESC, MOV_COMPRO DESC

        """
        datos = Querys(kwargs).querys(sql,(),'get',1)
        estados = []
        for index,value in enumerate(datos):
            estados.append({'id':index,"codigo_pedido":value[0],"fecha":value[1].strftime('%Y-%m-%d'),'status':value[2],"cliente":value[3].strip(),\
                            "subtotal":value[4],"igv":value[5],"total":value[6],'codigo':value[7].strip(),'moneda':value[8].strip(),'agencia':value[9].strip(),
                            'descuento':value[10],'obs':value[11].strip()})
        
        return Response({'states':estados})
    def querys(self,conn,sql,params=()):
        cursor = conn.cursor()
        cursor.execute(sql,params)
        datos = cursor.fetchall()
        conn.commit()
        conn.close()
        return datos
class EstadoPedido(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        host = kwargs['host']
        db = kwargs['db']
        user = kwargs['user']
        password = kwargs['password']
        sql = """
         SELECT 
            a.MOV_COMPRO,
            a.MOV_FECHA,
            b.aux_razon,
            ROU_BRUTO,
            ROU_IGV,rou_submon,a.ped_status,a.ped_statu2,a.ven_codigo,a.MOV_MONEDA,a.gui_exp001
			
        FROM cabepedido AS a INNER JOIN t_auxiliar AS b ON a.MOV_CODAUX=b.aux_clave 
		WHERE (a.ped_status IN (1,0) OR a.ped_statu2 IN (1,0)) AND a.ped_cierre=0 AND a.elimini=0
        ORDER BY MOV_FECHA DESC,MOV_COMPRO DESC
        """
        try:
            conn = QuerysDb.conexion(host,db,user,password)
            cursor = conn.cursor()
            cursor.execute(sql)
            datos = cursor.fetchall()
            conn.commit()
            conn.close()
            estados = [{"id":index,"codigo_pedido":value[0],"fecha":value[1].strftime("%Y-%m-%d"),"cliente":value[2].strip(),\
                        "subtotal":value[3],"igv":value[4],"total":value[5],"status1":value[6],"status2":value[7],\
                            "codigo":value[8].strip(),'moneda':value[9].strip(),'obs':value[10].strip()}for index,value in enumerate(datos)]
           
            return Response({"states":estados})
        except Exception as e:
            return Response({'message':str(e)})
        
    def post(self,request,*args,**kwargs):
        data = request.data
        credencial = data['credencial']
        conn = QuerysDb.conexion(credencial['bdhost'],credencial['bdname'],credencial['bduser'],credencial['bdpassword'])
        cursor = conn.cursor()
        if data['aprobacion']==1:
            if int(data['user']['aprobacion1'])==1 and int(data['user']['aprobacion2'])==1:
                sql = """UPDATE cabepedido set ped_status=2,ped_statu2=2 WHERE MOV_COMPRO=?"""
            elif int(data['user']['aprobacion1'])==1 and int(data['user']['aprobacion2'])==0:
                sql = "UPDATE cabepedido SET ped_status=2 WHERE MOV_COMPRO=?"
            elif int(data['user']['aprobacion1'])==0 and int(data['user']['aprobacion2']==1):
                sql = "UPDATE cabepedido SET ped_statu2=2 WHERE MOV_COMPRO=?"
        else:
            sql = "UPDATE cabepedido SET ped_statu2=2 WHERE MOV_COMPRO=?"

        cursor.execute(sql,data['codigo_pedido'])
        conn.commit()
        conn.close()
        
        return Response({'message':'Aprobacion exitosa'})
class AgenciaView(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        host = kwargs['host']
        bd = kwargs['db']
        user = kwargs['user']
        password = kwargs['password']
        data = {}
        try:
            conn = QuerysDb.conexion(host,bd,user,password)
            cursor = conn.cursor()
            sql = f"""
                    SELECT TRA_CODIGO,TRA_NOMBRE,TRA_DIRECC FROM t_transporte
            """
            cursor.execute(sql)
            result = cursor.fetchall()
            conn.commit()
            conn.close()
            data = []
            for index,item in enumerate(result):
                d = {'id':index,'codigo':item[0].strip(),'nombre':item[1].strip(),'direccion':item[2].strip()}
                data.append(d)
        except Exception as e:
            data['error'] = f"Ocurrio un error: {str(e)}"
        return Response({'message':data})
class SucursalView(generics.GenericAPIView):
    def get(self,rquest,*args,**kwargs):
        host = kwargs['host']
        bd = kwargs['db']
        user = kwargs['user']
        password = kwargs['password']
        data = {}
        try:
            conn = QuerysDb.conexion(host,bd,user,password)
            cursor = conn.cursor()
            sql = f"""
                SELECT 
                    tie_codigo,
                    tie_nombre,
                    tie_direc,
                    tie_telef
                FROM t_sucursal 
                WHERE tie_codaux=?
            """
            cursor.execute(sql,(kwargs['codigo'],))
            result = cursor.fetchall()
           
            if len(result)==0:
                data['error'] = 'No hay ubicaciones para este cliente'
            else:
                data = []
                for index,value in enumerate(result):
                    d = {'id':index,'codigo':value[0].strip(),'nombre':value[1].strip(),'direccion':value[2].strip(),'celular':value[3].strip()}
                    data.append(d)
       
            conn.commit()
            conn.close()
        except Exception as e:
            data['error'] = f"Ocurrio un error: {str(e)}"
        return Response(data)
class UbigeoView(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        data = {}
        try:
            sql = """
                SELECT
                    ubi_CODIGO,
                    ubi_depart,
                    ubi_provin,
                    ubi_distri
                FROM mk_ubigeo
                """
            result = Querys(kwargs).querys(sql,(),'get',1)
            data = []
            for index,value in enumerate(result):
                d = {'id':index,'ubigeo':value[0].strip(),'departamento':value[1].strip().upper(),
                     'provincia':value[2].strip().upper(),'distrito':value[3].strip().upper()} 
                data.append(d)
            
        except Exception as e:
            data['error'] = f'Ocurrio un erro : {str(e)}'
        return Response(data)
class LugarEntregaView(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        
        data = {}
        try:
           
            sql = """
                SELECT 
                    tie_nombre,
                    tie_direc,
                    tie_telef,
                    tie_ubigeo,
                    tie_tipdoc,
                    tie_link,
                    tie_docum 
                FROM t_sucursal 
                WHERE 
                tie_codigo=? AND tie_codaux=?
                """
            res = self.querys(kwargs,sql,(kwargs['codigo'],kwargs['cliente']),'get')
           
            data = {'nombre':res[0].strip(),'direccion':res[1].strip(),'celular':res[2].strip(),
                    'ubigeo':res[3].strip(),'tipo_doc':res[4],'link':res[5].strip(),'documento':res[6].strip(),'index':0 if res[4]==1 else(1 if res[4]==2 else (2 if res[4]==3 else 4))}
        except Exception as e:
            data['error'] = f"Ocurrio un error: {str(e)}"
        return Response(data)
    def post(self,request,*args,**kwargs):
        data = request.data
        
        sql = """
            SELECT TOP 1
                'codigo'=LEFT(tie_codigo, 8) + '-' + RIGHT('0000000' + CAST(CAST(RIGHT(tie_codigo, 7) AS INT) + 1 AS VARCHAR(7)), 7)
            FROM t_sucursal
            WHERE
                tie_codaux = ?
                AND LEN(tie_codigo) = 16
                AND tie_codigo LIKE ?
            ORDER BY tie_codigo DESC;
            """
        codigo = self.querys(kwargs,sql,(kwargs['cliente'],kwargs['cliente']+'%'),'get')
        if codigo is None:
            codigo = f"{kwargs['cliente']}-{str(1).zfill(7)}"
        else:
            codigo = codigo[0]
   
        params = (data['nombre'],data['direccion'],data['celular'],data['ubigeo'],data['tipo_doc'],data['link'],data['documento'],codigo.strip(),kwargs['cliente'])
        try:
            sql = f"""
                INSERT INTO t_sucursal(
                    tie_nombre,
                    tie_direc,
                    tie_telef,
                    tie_ubigeo,
                    tie_tipdoc,
                    tie_link,
                    tie_docum,
                    tie_codigo,
                    tie_codaux)
                VALUES({','.join('?' for i in params)})
                """
            self.querys(kwargs,sql,params,'post')
            data['success'] = f" Se creo con exito lugar de entrega para {kwargs['cliente']}"
        except Exception as e:
            data['error'] = f"Ocurrio un error: {str(e)}"
        return Response(data)
    def put(self,request,*args,**kwargs):
        try:
            sql = """
                    UPDATE t_sucursal
                    SET
                        tie_nombre=?,
                        tie_direc=?,
                        tie_telef=?,
                        tie_ubigeo=?,
                        tie_tipdoc=?,
                        tie_link=?,
                        tie_docum=? 
                    WHERE 
                        tie_codigo=? AND tie_codaux=?
                """
            data = request.data
        
            params = (data['nombre'],data['direccion'],data['celular'],data['ubigeo'],data['tipo_doc'],data['link'],data['documento'],kwargs['codigo'],kwargs['cliente'])
            res = self.querys(kwargs,sql,params,'post')
            if res==200:
                data['success'] = f'Los cambios para {kwargs["codigo"]} fueron exitosos'
        except Exception as e:
            data['error'] = f"Ocurrio un error : {str(e)}"
        return Response(data)
    def querys(self,kwargs,sql,params=(),tipo='post'):
        host = kwargs['host']
        bd = kwargs['db']
        user = kwargs['user']
        password = kwargs['password']
        conn = QuerysDb.conexion(host,bd,user,password)
        cursor = conn.cursor()
        data = 200
        if tipo =='post':
            cursor.execute(sql,params)
        else:
            cursor.execute(sql,params)
            data = cursor.fetchone()
        conn.commit()
        conn.close()            
        return data
class TipoPago(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        data = {}
        try:
            sql = """SELECT PAG_CODIGO,PAG_NOMBRE,pag_nvallc FROM t_maepago WHERE pag_activo='1' AND PAG_NOMBRE<>'' ORDER BY PAG_CODIGO"""

            tipo_pago = Querys(kwargs).querys(sql,(),'get')
            types_paymonts = []
            if tipo_pago is not None:
                for row in tipo_pago:
                    a = {'value':str(row[0]).strip(),'label':str(row[1]).strip()}
                    types_paymonts.append(a)
            data['tipo_pago'] = types_paymonts
        except Exception as e:
            data['error'] = 'Ocurrio un error'
        return Response(data)