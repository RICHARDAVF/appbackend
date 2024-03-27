from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from apirest.credenciales import Credencial
from apirest.querys import CAQ
class Cotizacion(GenericAPIView):
    def post(self,request,*args,**kwargs):
        data = {}
        datos = request.data

        self.credencial = Credencial(datos['credencial'])
        try:
            sql = f"""
                        SELECT a.MOV_COMPRO,a.gui_ruc,b.aux_razon,a.MOV_FECHA,a.MOV_MONEDA FROM cabecotiza AS a
                        LEFT JOIN t_auxiliar AS b ON a.gui_ruc = b.AUX_DOCUM
                    """
            s,result = CAQ.request(self.credencial,sql,(),'get',1)
            if not s:
                raise Exception('Error al recuperar las cotizaciones')
            
            data = [
                {
                    "id":index,
                    "numero_cotizacion":value[0].strip(),
                    "documento":value[1].strip(),
                    "razon_social":value[2].strip(),
                    "fecha_emision":value[3].strftime('%d/%m/%Y'),
                    "moneda":value[4].strip(),
                    
                } for index,value in enumerate(result)
            ]
            data = [data[i:i+100] for i in range(0,len(data),100) ]
        except Exception as e:
            data['error'] = str(e)

        return Response(data)