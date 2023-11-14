from rest_framework import generics,status
from rest_framework.response import Response
from dotenv import load_dotenv
import requests
import os
import json
from datetime import date,datetime
from apirest.views import QuerysDb
from apirest.view.guias.factappi import RequestAPI
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
import base64
load_dotenv()
class Facturacion(generics.GenericAPIView):
    # authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]
    def validfecha(self,fecha):
        try:
            datetime.strptime(fecha, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    def guia_traslado(self,datos):
        return len(datos['num_pedido'].strip())!=8 or datos['num_pedido'][0]!='T'
    def guia_venta(self,datos):
        return len(datos['num_pedido'].strip())== 0 or datos['num_pedido'][0]=='T'
    # def valid_importe(self,datos):
    #     if datos['codigo_operacion'] =='18':
    #         for item in datos['items']:
    #             if item['precio']!=0:
    #                 return False
    #     return True
    def post(self,request,*args,**kwargs):
        data = {}
        try:
            datos = request.data
            if datos['tipodoc'] not in [1,6]:
                data['error'] = "Tipo de documento no permitido"
                data['status'] = 400
                return Response(data,status=status.HTTP_200_OK) 
            if len(datos['codigo_operacion'].strip()) == 0 or not datos['codigo_operacion'] in ['05','06']:
                data['error'] = 'Codigo de operacion no permitido'
                data['status'] = 400
                return Response(data,status=status.HTTP_200_OK)
            elif datos['codigo_operacion']=='05' and  self.guia_venta(datos):
                data['error'] =  "Ocurrio un error con el numero de pedido"
                data['status'] = 400
                return Response(data,status=status.HTTP_200_OK)
            elif datos['codigo_operacion']=='06' and  self.guia_traslado(datos):
                data['error'] = "Ocurrio un error con el correlativo de la guia de traslado"
                data['status'] = 400
                return Response(data,status=status.HTTP_200_OK)
            for item in datos['items']:
                if not self.validfecha(item['fecha_vencimiento']):
                    return Response({'error':"formato de la fecha es de vencimiento es  incorrecto (YYYY-MM-DD)"})
            # if not self.valid_importe(datos):
            #     data['error'] = "Error en el importe para una guia de traslado"
            #     data['status'] = 400
            #     return Response(data,status=status.HTTP_200_OK)
            tipodoc = "ruc" if datos['tipodoc']==6 else "dni"
            if len(datos['doc'])==0:
                data['error'] = "Error en el numero de documento"
                data['status'] = 400
                return Response(data,status=status.HTTP_200_OK)
            url = f"https://my.apidevs.pro/api/dni/{datos['doc']}" if datos['tipodoc']==1 else f"https://apiperu.dev/api/{tipodoc}/{datos['doc']}"
       
            response = requests.get(url,headers={
                "Authorization":f"Bearer {os.getenv(f'TOKEN_{tipodoc.upper()}')}"
            })
            res=json.loads(response.text)
            sql = f"SELECT gui_serie,gui_docum FROM GUIC{datetime.now().year} WHERE gui_ordenc=?"
            band = False
            gui_serie = self.query(sql,(datos['num_pedido']))
            sql = "SELECT doc_docum,doc_serie FROM t_documento WHERE DOC_CODIGO=? AND doc_serie=?"
            num_doc,serie = self.query(sql,('GR','T003'))
            if gui_serie is  None:
                gui_serie = num_doc
                band = True
            else:
                gui_serie = gui_serie[1]
            if not res['success']:
                data[f'{tipodoc}'] = f"Numero de {tipodoc} invalido"
                return Response(data)
            if len(datos['direccion_llegada'])<=10:
                data['direccion'] = "No ingreso una direccion de entrega correcta"
                return Response(data,status=status.HTTP_400_BAD_REQUEST)
            sql= "SELECT *FROM t_auxiliar WHERE AUX_DOCUM=? AND SUBSTRING(MAA_CODIGO,1,1)='C'"
            dates = self.query(sql,(datos['doc'],))
            codigo_cliente = ''
            dir_alternativa = ''
            if dates is None and res['success']:
                sql = f"""SELECT MAA_CODIGO, AUX_CODIGO,AUX_DIRECC,DIS_CODIGO,PRO_CODIGO
                                    FROM t_auxiliar
                                    WHERE AUX_CODIGO = (SELECT MAX(AUX_CODIGO) FROM t_auxiliar WHERE MAA_CODIGO='CT' ) AND  MAA_CODIGO='CT'"""
                result= self.query(sql,())
  
                if result is None:
                    maa,codigo='CT','1'
                else:
                    maa,codigo,direccion,distrito,provincia=result
                    codigo = int(codigo)+1
                    dir_alternativa = f"{direccion.strip()}-{distrito.strip()}-{provincia.strip()}"
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
                    dir_alternativa = f"{ res['data']['direccion']}-{res['data']['distrito']}-{res['data']['provincia']}"
                codigo_cliente = params[2]
                sql = f""" 
                    INSERT INTO 
                        t_auxiliar(MAA_CODIGO,AUX_CODIGO,AUX_CLAVE,AUX_NOMBRE,AUX_RAZON,VEN_CODIGO,MAA_NOMBRE,AUX_DIRECC,
                        DEP_CODIGO,PRO_CODIGO,DIS_CODIGO,AUX_TIPOPE,AUX_DOCUM,AUX_EDI,aux_cuenta,aux_cuentd,aux_condic,aux_estado,aux_tipdoc,aux_fecoru) 
                        VALUES({','.join('?' for i in range(len(params)))})
                """
                self.query(sql,params,'post')
            else:
                codigo_cliente=dates[2]
            data = self.beforepost(datos,gui_serie,dir_alternativa)
            #USUARIOS DE PRUEBA
            self.query(f"INSERT INTO corret{datetime.now().year}(usuario,fechausu) VALUES(?,?)",('000',datetime.now().strftime('%Y-%m-%d')),'post')
            sql = f"SELECT numero FROM corret{datetime.now().year} WHERE numero=(SELECT MAX(numero) FROM corret{datetime.now().year} WHERE usuario=000)"
            result= self.query(sql,())
            
            fecha = date.today().strftime('%Y-%m-%d')
            response = requests.get(f'https://api.apis.net.pe/v1/tipo-cambio-sunat?fecha={fecha}')
            tipo_c = ''
            if response.status_code ==200:
                tc = response.json()
                tipo_c = tc['compra']
            else:
                return Response({'error':'Errores en la conexion para tipo de cambio'})
            

            if  band:
                for item in datos['items']:
                   
                    if self.valid(item['codigo']) is None:
                        return Response({"error":f"El codigo {item['codigo']} no existe en la base  de datos"})
               
                params = (str(result[0]).zfill(11),date.today().strftime('%Y-%m-%d'),codigo_cliente,
                            "01",
                            tipo_c,
                            '001',
                            date.today().strftime('%Y-%m-%d'),
                            date.today().strftime('%Y-%m-%d'),
                            1,
                            3,
                            1 if datos['codigo_operacion']=='05' else 6,
                            '24',
                            datos['direccion_llegada'],
                            datos['total'],
                            '01',
                            '001',
                            datos['doc'],
                            datos['codigo_operacion'],
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
                            "0001",
                            "GR",
                            datos['ubigeo_llegada'],
                            datos['observacion']
                        )
                sql = f"""
                        INSERT INTO GUIC{date.today().strftime('%Y')}(
                            MOV_COMPRO,MOV_FECHA,MOV_CODAUX,DOC_CODIGO,MOV_T_C,USUARIO,
                            FECHAUSU,
                            mov_fvenc,
                            rou_export,
                            gui_tipotr,
                            gui_motivo,
                            ubi_codigo,
                            gui_direc,rou_submon,alm_codigo,
                        ven_codigo,gui_ruc,ope_codigo,pag_codigo,
                        gui_inclu,MOV_MONEDA,ROU_BRUTO,ROU_PIGV,ROU_IGV,ROU_TVENTA,
                        gui_serie,gui_docum,doc_compro,gui_ordenc,tra_codigo,gui_coddoc,gui_textol,gui_exp001) 
                        VALUES({','.join('?' for i in params)})
                        """
                self.query(sql,params,'post')
                items = datos['items']
                cont=1
                for item in items:
                    cod,name,peso=self.valid(item['codigo'])
                   
                    params = (
                        '24',
                        date.today().strftime('%m'),
                        str(result[0]).zfill(11),
                        '01',
                        date.today().strftime('%Y-%m-%d'),
                        cod.strip(),
                        'S',
                        datos['codigo_operacion'],
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
                        cont,
                        '/'.join(str(i) for i in reversed(item['fecha_vencimiento'].split('-'))),
                        item['lote'],
                        int(item['cantidad'])*peso
                    )
                    
                    sql1 = f"""
                        INSERT INTO GUID{date.today().strftime('%Y')}(ALM_CODIGO,MOM_MES,mov_compro,doc_codigo,MOM_FECHA,
                        ART_CODIGO,MOM_TIPMOV,OPE_CODIGO,UBI_COD,UBI_COD1,MOM_CANT,mom_valor,MOM_MONEDA,MOM_T_C,MOM_PUNIT,
                        USUARIO,FECHAUSU,doc_compro,art_afecto,gui_inclu,mom_linea,mom_lote,art_codadi,mom_bruto) 
                        VALUES({','.join('?' for i in params)})
                    """
                    self.query(sql1,params,'post')
                    params = (
                        '24',
                        date.today().strftime('%m'),
                        '01',
                        date.today().strftime('%Y-%m-%d'),
                        cod.strip(),
                        'S',
                        datos['codigo_operacion'],
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
                        str(result[0]).zfill(11),
                        codigo_cliente,
                        "GR",
                        f"{serie}-{num_doc}",
                        datetime.strptime(item['fecha_vencimiento'],'%Y-%m-%d'),
                        item['lote'],
                        int(item['cantidad'])*peso,
                        cont,
                        1
                    )
                   
                    sql2 = f"""
                        INSERT INTO MOVM{date.today().strftime('%Y')}(ALM_CODIGO,MOM_MES,doc_cod1,MOM_FECHA,
                        ART_CODIGO,MOM_TIPMOV,OPE_CODIGO,UBI_COD,UBI_COD1,MOM_CANT,mom_valor,MOM_MONEDA,
                        MOM_T_C,MOM_PUNIT,USUARIO,FECHAUSU,art_afecto,MOM_D_INT,mom_codaux,mom_retip1,
                        mom_redoc1,mom_lote,art_codadi,mom_bruto,mom_linea,gui_inclu) 
                        VALUES({','.join('?' for i in params)})
                    """
                    self.query(sql2,params,'post')
                    cont+=1
                sql = "UPDATE t_documento SET doc_docum=? WHERE DOC_CODIGO=? AND doc_serie=?"
               
                self.query(sql,(int(num_doc)+1,'GR','T003'),'post')
             
            #data['message'] = "Los datos se procesaron exitosamente"
        except Exception as e:
            data['error'] = f"Hubo un error en la peticion:{str(e)}"
        return Response(data)
    def query(self,sql,params,opt='get'):
        conn = QuerysDb.conexion('192.168.1.40','siiasmartfc','sa','Noi2011')
        cursor = conn.cursor()
        cursor.execute(sql,params)
        data = ''
        if opt =='get':
            data = cursor.fetchone()
        conn.commit()
        conn.close()
        return data
    def valid(self,codigo):
        sql =  "SELECT ART_CODIGO,ART_NOMBRE,art_peso FROM t_articulo WHERE art_provee=?"
        return self.query(sql,(codigo,))
    def beforepost(self,datos,num_doc,direc):
        items = datos['items']
        articulos = []
        peso = 0
        for item in items:
            sql = "SELECT ume_sunat FROM t_umedida WHERE UME_CODIGO=(SELECT UME_CODIGO FROM t_articulo WHERE art_provee=?)"
            medida= self.query(sql,(item['codigo'],))
            sql = "SELECT ART_CODIGO,ART_NOMBRE,art_peso FROM t_articulo WHERE art_provee=?"
            
            res=self.query(sql,(item['codigo'],))
            peso+=res[2]*int(item['cantidad'])
            articulos.append(
                {
                    "cantidad":f"{item['cantidad']}",
                    "unidadMedida":medida[0].strip(),
                    "descripcion":res[1].strip(),
                    "codigoItem":res[0].strip(),
                    "adicional":{
                        "peso":f"{res[2]*int(item['cantidad'])}",
                        "lote":item['codigo'],
                        "fechaVencimiento":item['fecha_vencimiento']

                    }
                    
                }
            )
        sql = """
            SELECT ubi_nombre,ubi_direc,ubi_nompos FROM t_ubicacion WHERE ubi_codigo= ?
        """
        dates = self.query(sql,('24',))
       
        ubi_nombre,dir_partida,ubigeo_partida = dates
        sql = "SELECT tra_nombre,TRA_RUC FROM T_transporte WHERE TRA_CODIGO=001"
        nombre,ruc = self.query(sql,())
        
        data = {"serie": "T003",
                "numero": int(num_doc),
                "fechaEmision":datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "tipoDocumentoGuia": "09",
                "motivoTraslado": "01" if datos['codigo_operacion']=='05' else "04",
                "pesoBrutoTotal": f"{peso}",
                "unidadPesoBruto": "KGM",
                "modalidadTraslado": "01",
                "fechaInicioTraslado":datetime.now().strftime('%Y-%m-%d %H:%M:%S') ,
                "ubigeoLlegada": datos['ubigeo_llegada'],
                "direccionLlegada": datos['direccion_llegada'],
                "ubigeoPartida": ubigeo_partida.strip(),
                "direccionPartida": dir_partida.strip(),
                "receptor": {
                    "tipo": datos['tipodoc'],
                    "nro": datos['doc'],
                    "razonSocial": datos['razon_social']
                },
                "adicional": {
                    "numeroRucTransportista": ruc.strip(),
                    "tipoDocumentoTransportista": "6",
                    "denominacionTransportista": nombre.strip(),
                    "ordenCompra": datos['num_pedido'],
                    "descripcionMotivoTraslado": "VENTAS" if datos['num_pedido'] =='05' else 'TRASLADO',
                    "dirAlternativa": direc,
                    "observaciones":datos['observacion']
                },
                "items": articulos
            }
        sql = "SELECT TOP 1 par_url,par_acekey,par_seckey FROM fe_parametro"

        url,access_key,secret_key = self.query(sql,())
        token,timestap = RequestAPI(access_key.strip(),secret_key.strip()).encryptdates()
        
        response = requests.post(f"{url.strip()}guiaremitente",headers={
            "Authorization":f"Fo {access_key.strip()}:{token}:{timestap}",
            },
            json=data
        )
        return response.json()
        
        
class PDFFACTView(generics.GenericAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self,request,*args,**kwargs):
        serie,numero = kwargs['serie'],kwargs['num']
        sql = "SELECT TOP 1 par_url,par_acekey,par_seckey FROM fe_parametro"
        url,access_key,secret_key = self.query(sql,())
        token,timestap = RequestAPI(access_key.strip(),secret_key.strip()).encryptdates()
        response = requests.get(f"{url.strip()}guiaremitente/{serie}{numero}/exportar/",headers={
            "Authorization":f"Fo {access_key.strip()}:{token}:{timestap}",
            },)
        if response.status_code==200:
            base = base64.b64encode(response.content).decode('utf-8')

            return Response({'pdf':base})
        return Response(json.loads(response.text))
    def query(self,sql,params,opt='get'):
        conn = QuerysDb.conexion('192.168.1.40','siiasmartfc','sa','Noi2011')
        cursor = conn.cursor()
        cursor.execute(sql,params)
        data = ''
        if opt =='get':
            data = cursor.fetchone()
        conn.commit()
        conn.close()
        return data
class AnulacionGuiaView(generics.GenericAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self,request,*args,**kwargs):

        data = {}
        try:
            sql = f"SELECT MOV_COMPRO FROM GUIC{datetime.now().year} WHERE gui_serie=? AND gui_docum=?"

            numero_pedido = self.query(sql,(kwargs['serie'],kwargs['numero']),'get')

            sql = f"""
                    UPDATE GUIC{datetime.now().year} set elimini=1 WHERE MOV_COMPRO = ? 
                """
            res = self.query(sql,(numero_pedido[0],),'post')
            sql = f"""
                    UPDATE GUID{datetime.now().year} set elimini=1 WHERE mov_compro = ? 
                """
            res = self.query(sql,(numero_pedido[0],),'post')
            
            sql = f"""
                    UPDATE MOVM{datetime.now().year} set elimini=1 WHERE MOM_D_INT = ? 
                """
            res = self.query(sql,(numero_pedido[0],),'post')
            if res ==200:
                data['success'] = "La anulacion fue exitosa" 
            
        except Exception as e:
            data['error'] = f"Ocurrio un error : {str(e)}"
        
        
        return Response(data)
    def query(self,sql,params,opt='get'):
        conn = QuerysDb.conexion('192.168.1.40','siiasmartfc','sa','Noi2011')
        cursor = conn.cursor()
        cursor.execute(sql,params)
        data  = 200
        if opt =='get':
            data = cursor.fetchone()
        conn.commit()
        conn.close()
        return data