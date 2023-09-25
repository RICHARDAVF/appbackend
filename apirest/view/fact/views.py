from rest_framework import generics
from rest_framework.response import Response
from dotenv import load_dotenv
import requests
import os
import json
from datetime import date,datetime
from apirest.views import QuerysDb
from apirest.view.fact.factappi import RequestAPI
load_dotenv()
class Facturacion(generics.GenericAPIView):
    def query(self,sql,params,opt='get'):
        conn = QuerysDb.conexion('192.168.1.80','siiasmartfc','sa','Noi2011')
        cursor = conn.cursor()
        cursor.execute(sql,params)
        data = ''
        if opt =='get':
            data = cursor.fetchone()
        conn.commit()
        conn.close()
        return data
    def post(self,request,*args,**kwargs):
        data = {}
        try:
            datos = request.data
            tipodoc = "ruc" if datos['tipodoc']==4 else "dni"
           
            url = f"https://my.apidevs.pro/api/dni/{datos['doc']}" if datos['tipodoc']==1 else f"https://apiperu.dev/api/{tipodoc}/{datos['doc']}"
       
            response = requests.get(url,headers={
                "Authorization":f"Bearer {os.getenv(f'TOKEN_{tipodoc.upper()}')}"
            })
            res=json.loads(response.text)
           
            if not res['success']:
                data[f'{tipodoc}'] = f"Numero de {tipodoc} invalido"
                return Response(data)
            if len(datos['direccion_llegada'])<=10:
                data['direccion'] = "No ingreso una direccion de entrega correcta"
                return Response(data)
            sql= "SELECT *FROM t_auxiliar WHERE AUX_DOCUM=? AND SUBSTRING(MAA_CODIGO,1,1)='C'"
            dates = self.query(sql,(datos['doc'],))
            
            codigo_cliente = ''
            if dates is None and res['success']:
                sql = f"""SELECT MAA_CODIGO, AUX_CODIGO
                                    FROM t_auxiliar
                                    WHERE AUX_CODIGO = (SELECT MAX(AUX_CODIGO) FROM t_auxiliar WHERE MAA_CODIGO='CT' ) AND  MAA_CODIGO='CT'"""
                result= self.query(sql,())
                if result is None:
                    maa,codigo='CT','1'
                else:
                    maa,codigo=result
                    codigo = int(codigo)+1
                tipope = 1
                tipedoc=2
                if datos['doc'][:2]=='20':
                    tipope=2
                    tipedoc=1
                if tipodoc=='dni':
                    params=(maa.strip(),str(codigo).zfill(6),f"{maa.strip()}{str(codigo).zfill(6)}",
                            res['data']['nombre_completo'],
                            res['data']['nombre_completo'],
                            '001',
                            "CLIENTE",
                            res['data']['direccion'],
                            res['data']['departamento'],
                            res['data']['provincia'],
                            res['data']['distrito'],
                            tipope,
                            datos['doc'],
                            res['data']['ubigeo_reniec'],
                            '121301',
                            '121302',
                            '',
                            '',
                            tipedoc,
                            date.today().strftime('%Y-%m-%d')
                            )
                else:
                    params=(maa.strip(),str(codigo).zfill(6),f"{maa.strip()}{str(codigo).zfill(6)}",
                            res['data']['nombre_o_razon_social'],
                            res['data']['nombre_o_razon_social'],
                            "001",
                            "CLIENTE",
                            res['data']['direccion'],
                            res['data']['departamento'],
                            res['data']['provincia'],
                            res['data']['distrito'],
                            tipope,
                            datos['doc'],
                            res['data']['ubigeo_sunat'],
                            '121301',
                            '121302',
                            res['data']['condicion'],
                            res['data']['estado'],
                            tipedoc,
                            date.today().strftime('%Y-%m-%d')
                            )
                codigo_cliente = params[2]
                sql = f""" 
                    INSERT INTO 
                        t_auxiliar(MAA_CODIGO,AUX_CODIGO,AUX_CLAVE,AUX_NOMBRE,AUX_RAZON,VEN_CODIGO,MAA_NOMBRE,AUX_DIRECC,
                        DEP_CODIGO,PRO_CODIGO,DIS_CODIGO,AUX_TIPOPE,AUX_DOCUM,AUX_EDI,aux_cuenta,aux_cuentd,aux_condic,aux_estado,aux_tipdoc,aux_fecoru) 
                        VALUES({','.join('?' for i in range(len(params)))})
                """
                # self.query(sql,params,'post')
            else:
                codigo_cliente=dates[2]
            sql = f"SELECT MOV_COMPRO FROM GUIC{date.today().strftime('%Y')} WHERE MOV_COMPRO=(SELECT MAX(MOV_COMPRO) FROM GUIC{date.today().strftime('%Y')})"
            result, = self.query(sql,())
            if result is None:
                result=0
            fecha = date.today().strftime('%Y-%m-%d')
            response = requests.get(f'https://api.apis.net.pe/v1/tipo-cambio-sunat?fecha={fecha}')
            tipo_c = ''
            if response.status_code ==200:
                tc = response.json()
                tipo_c = tc['compra']
            else:
                return Response({'error':'Errores en la conexion'})
            sql = "SELECT doc_docum,doc_serie FROM t_documento WHERE DOC_CODIGO=? AND doc_serie=?"

            num_doc,serie = self.query(sql,('GR','T001'))
            
            params = (str(int(result)+1).zfill(11),date.today().strftime('%Y-%m-%d'),codigo_cliente,
                        "01",
                        tipo_c,
                        '001',
                        date.today().strftime('%Y-%m-%d'),
                        date.today().strftime('%Y-%m-%d'),
                        1,
                        3,
                        1,
                        '24',
                        datos['direccion_llegada'],
                        datos['total'],
                        '01',
                        '001',
                        datos['doc'],
                        '05',
                        '01',
                        1,
                        datos['moneda'],
                        datos['base_imponible'],
                        18,
                        datos['igv'],
                        datos['total'],
                        serie,
                        num_doc,
                        '03',
                        datos['num_pedido'],
                        "0001"
                      )
            sql = f"""
                    INSERT INTO GUIC{date.today().strftime('%Y')}(
                        MOV_COMPRO,
                        MOV_FECHA,
                        MOV_CODAUX,
                        DOC_CODIGO,
                        MOV_T_C,
                        USUARIO,
                        FECHAUSU,
                        mov_fvenc,
                        rou_export,
                        gui_tipotr,
                        gui_motivo,
                        ubi_codigo,
                        gui_direc,rou_submon,alm_codigo,
                    ven_codigo,gui_ruc,ope_codigo,pag_codigo,gui_inclu,MOV_MONEDA,ROU_BRUTO,ROU_PIGV,ROU_IGV,ROU_TVENTA,fac_serie,fac_docum,doc_compro,gui_ordenc,tra_codigo) 
                    VALUES({','.join('?' for i in params)})
                    """
            self.query(sql,params,'post')
            items = datos['items']
            cont=1
            for item in items:
                params = (
                    '24',
                    date.today().strftime('%m'),
                    str(int(result)+1).zfill(11),
                    '01',
                    date.today().strftime('%Y-%m-%d'),
                    item['codigo'],
                    'S',
                    '05',
                    '24',
                    '24',
                    item['cantidad'],
                    round(item['cantidad']*item['precio'],2),
                    datos['moneda'],
                    tipo_c,
                    item['precio'],
                    '001',
                    date.today().strftime('%Y-%m-%d'),
                    '03',
                    'S',
                    1,
                    cont
                )
                sql1 = f"""
                    INSERT INTO GUID{date.today().strftime('%Y')}(ALM_CODIGO,MOM_MES,mov_compro,doc_codigo,MOM_FECHA,
                    ART_CODIGO,MOM_TIPMOV,OPE_CODIGO,UBI_COD,UBI_COD1,MOM_CANT,mom_valor,MOM_MONEDA,MOM_T_C,MOM_PUNIT,
                    USUARIO,FECHAUSU,doc_compro,art_afecto,gui_inclu,mom_linea) 
                    VALUES({','.join('?' for i in params)})
                """
                # self.query(sql1,params,'post')
                params = (
                    '01',
                    date.today().strftime('%m'),
                    '01',
                    date.today().strftime('%Y-%m-%d'),
                    item['codigo'],
                    'S',
                    '05',
                    '24',
                    '24',
                    item['cantidad'],
                    round(item['cantidad']*item['precio'],2),
                    datos['moneda'],
                    tipo_c,
                    item['precio'],
                    '001',
                    date.today().strftime('%Y-%m-%d'),
                    'S',
                    str(int(result)+1).zfill(11),
                    codigo_cliente,
                    "GR",
                    f"{serie}-{num_doc}"
                )
                sql2 = f"""
                    INSERT INTO MOVM{date.today().strftime('%Y')}(ALM_CODIGO,MOM_MES,doc_cod1,MOM_FECHA,
                    ART_CODIGO,MOM_TIPMOV,OPE_CODIGO,UBI_COD,UBI_COD1,MOM_CANT,mom_valor,MOM_MONEDA,MOM_T_C,MOM_PUNIT,USUARIO,FECHAUSU,art_afecto,MOM_D_INT,mom_codaux,mom_retip1,mom_redoc1) 
                    VALUES({','.join('?' for i in params)})
                """
                # self.query(sql2,params,'post')
                cont+=1
            sql = "UPDATE t_documento SET doc_docum=? WHERE DOC_CODIGO=? AND doc_serie=?"
            self.query(sql,(int(num_doc)+1,'GR','T001'),'post')
            self.beforepost(datos,num_doc)
            data['message'] = "Los datos se procesaron exitosamente"
        except Exception as e:
            data['error'] = f"Hubo un error en la peticion:{str(e)}"
        return Response(data)
    def beforepost(self,datos,num_doc):
        items = datos['items']
       
        articulos = []
        for item in items:
            sql = "SELECT ume_sunat FROM t_umedida WHERE UME_CODIGO=(SELECT UME_CODIGO FROM t_articulo WHERE ART_CODIGO=?)"
            medida= self.query(sql,(item['codigo'],))
            sql = "SELECT ART_NOMBRE FROM t_articulo WHERE ART_CODIGO=?"
            name=self.query(sql,(item['codigo'],))
           
            articulos.append(
                {
                    "cantidad":item['cantidad'],
                    "unidadMedida":medida[0].strip(),
                    "descripcion":name[0].strip(),
                    "codigoItem":item['codigo'],
                    "adicional":{
                        "peso":0.00,

                    }
                    
                }
            )
        sql = """
            SELECT ubi_nombre,ubi_direc,ubi_nompos FROM t_ubicacion WHERE ubi_codigo= ?
        """
        dates = self.query(sql,('24',))
        ubi_nombre,dir_partida,ubigeo_partida = dates
        data = {"serie": "T001",
                "numero": int(num_doc),
                "fechaEmision":datetime.now().strftime('%Y-%m-%d %H:%M:%S') ,
                "tipoDocumentoGuia": "09",
                "motivoTraslado": "01",
                "pesoBrutoTotal": "1",
                "unidadPesoBruto": "KGM",
                "modalidadTraslado": "02",
                "fechaInicioTraslado": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "ubigeoLlegada": datos['ubigeo_llegada'],
                "direccionLlegada": datos['direccion_llegada'],
                "direccionPartida": dir_partida.strip(),
                "ubigeoPartida": ubigeo_partida.strip(),
                "receptor": {
                    "tipo": datos['tipodoc'],
                    "nro": datos['doc'],
                    "razonSocial": datos['razon_social']
                },
                "adicional": {
                    "ordenCompra": datos['num_pedido'],
                    "vendedor": datos['vendedor'],
                    "ubicacion": ubi_nombre.strip(),
                    "descripcionMotivoTraslado": datos['motivo_traslado'],
                    "cotizacion": datos['num_cotizacion'],
                    "operacion": datos['operacion'],
                    "dirAlternativa": datos['dir_alternativa']
                },
                "items": articulos
            }
        sql = "SELECT TOP 1 par_url,par_acekey,par_seckey FROM fe_parametro"
        with open("prueba.json","w") as file:
            file.write(json.dumps(data))
        url,access_key,secret_key = self.query(sql,())
        response = requests.post(url.strip()+'/guiaremitente',headers={
            "Authorization":f"Fo {RequestAPI(access_key,secret_key).encryptdates()}",
            "Content-Type":"application/json"
            },
            data=data
        )
        print(response.text)
        
        