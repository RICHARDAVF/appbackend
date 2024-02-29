from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from apirest.crendeciales import Credencial
from datetime import datetime
from apirest.querys import CAQ
from tabulate import tabulate
class TicketFactura(GenericAPIView):
    credencial : object = None
    anio : int = datetime.now().year
    def post(self,request,*args,**kwagrs):
        data = {}
        datos = request.data
        self.credencial = Credencial(datos['credencial'])
        try:
            sql = f"""SELECT
                        a.MOV_COMPRO,
                        a.ROU_TVENTA,
                        b.AUX_NOMBRE,
                        b.AUX_DOCUM,
                        a.MOV_FECHA
                    FROM guic{self.anio} AS a
                    LEFT JOIN t_auxiliar AS b ON b.AUX_CLAVE = a.MOV_CODAUX
                    WHERE  a.MOV_COMPRO=?
                """
           
            s,result = CAQ.request(self.credencial,sql,(datos['pedido'],),'get',0)
            print(result)
            if not s:
                raise Exception('Ocurrio un error al recuperar los datos del pedido')
            data['datos'] = {
                'numero_pedido':result[0].strip(),
                'total':float(result[1]),
                'cliente':result[2].strip(),
                'documento':result[3].strip(),
                'fecha':result[4].strftime('%Y-%m-%d')
            }
            sql = f"""
                    SELECT
                        a.mom_cant,
                        a.mom_valor,
                        a.mom_punit,
                        b.ART_NOMBRE
                    FROM guid{self.anio} AS a

                    LEFT JOIN t_articulo AS b ON b.ART_CODIGO=a.ART_CODIGO

                    WHERE  a.mov_compro=?
                """
            s,result = CAQ.request(self.credencial,sql,(datos['pedido'],),'get',1)
            print(result)
            if not s:
                raise Exception('Error al recuperar los items de la factura')
            data['items'] = [
                {
                    'cantidad':float(item[0]),
                    'subtotal':item[1].strip(),
                    'descripcion':item[3].strip(),
                } for item in result
            ]
        except Exception as e:
            data['error'] = str(e)
        return Response(data)
class TickeNP(GenericAPIView):
    credencial : object = None
    anio : int = datetime.now().year
    def post(self,request,*args,**kwagrs):
        data = {}
        datos = request.data
        self.credencial = Credencial(datos['credencial'])
        try:
            sql = f"""SELECT
                        a.MOV_COMPRO,
                        a.ROU_TVENTA,
                        b.AUX_NOMBRE,
                        b.AUX_DOCUM,
                        a.MOV_FECHA,
                        a.mov_moneda
                    FROM cabepedido AS a
                    LEFT JOIN t_auxiliar AS b ON b.AUX_CLAVE = a.MOV_CODAUX
                    WHERE  a.MOV_COMPRO=?
                """
           
            s,result = CAQ.request(self.credencial,sql,(datos['pedido'],),'get',0)

            if not s:
                raise Exception('Ocurrio un error al recuperar los datos del pedido')
            data['datos'] = {
                'numero_pedido':result[0].strip(),
                'total':float(result[1]),
                'cliente':result[2].strip(),
                'documento':result[3].strip(),
                'fecha':result[4].strftime('%Y-%m-%d'),
                'moneda':'S/' if result[5].strip()=='S' else '$'
            }
            formato_ticket = f"""
Cliente : {data['datos']['numero_pedido']}
Documento: {data['datos']['documento']}
Fecha : {data['datos']['fecha']}

"""
            sql = f"""
                    SELECT
                        a.mom_cant,
                        a.mom_valor,
                        a.mom_punit,
                        b.ART_NOMBRE
                       
                    FROM movipedido AS a

                    LEFT JOIN t_articulo AS b ON b.ART_CODIGO=a.ART_CODIGO

                    WHERE  a.mov_compro=?
                """
         
            s,result = CAQ.request(self.credencial,sql,(datos['pedido'],),'get',1)
            if not s:
                raise Exception('Error al recuperar los items de la factura')
            data['items'] = [
                {
                    'cantidad':float(item[0]),
                    'subtotal':float(item[1]),
                    'descripcion':item[3].strip(),
                } for item in result
            ]
            cadena = tabulate(tabular_data=[[item['cantidad'],item['descripcion'],item['subtotal']] for item in  data['items']],headers=['Cant','Descripcion','Subtotal'],tablefmt='simple')
            data['f'] = cadena+'\n\n'
        except Exception as e:
            data['error'] = str(e)
        return Response(data)