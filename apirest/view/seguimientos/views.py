from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from apirest.credenciales import Credencial
from apirest.querys import CAQ
from datetime import datetime
class SeguimientoPedidos(GenericAPIView):
    def post(self,request,*args,**kwargs):
        data = {}
        datos = request.data
        self.fecha = datetime.now()
        self.credencial = Credencial(datos['credencial'])
        try:
            filter_ = datos['filter']
            sql = f"""SELECT 
                        a.mov_compro,
                        COALESCE(c.aux_nombre,'') AS c,
                        a.MOV_FECHA,
                        COALESCE(b.gui_serie,'') AS gui_serie,
                        COALESCE(b.gui_docum,'') AS gui_docum,
                        COALESCE(b.fac_serie,'') AS fac_serie,
                        COALESCE(b.fac_docum,'') AS fac_docum,
                        COALESCE(d.tie_link,'')  AS url,
                        COALESCE(d.tie_nombre,'') AS nombre,
                        COALESCE(d.tie_docum,'') AS documento,
						COALESCE(d.tie_telef,'') AS celular,
						COALESCE(d.tie_direc,'') AS direccion,
                        COALESCE(e.usu_nombre,'') AS vendedor
                    FROM cabepedido AS a
                    LEFT JOIN guic{self.fecha.year} AS b ON a.MOV_COMPRO = b.mov_pedido
                    LEFT JOIN t_auxiliar AS c ON a.MOV_CODAUX = c.AUX_CLAVE
                    LEFT JOIN t_sucursal AS d ON a.gui_tienda = d.tie_codigo
                    LEFT JOIN t_usuario AS e ON a.ven_codigo = e.ven_codigo
                    WHERE 
                        a.edp_codigo='05'
                        AND a.elimini=0 
                        AND (a.mov_compro LIKE '%{filter_}%' OR c.aux_nombre LIKE '%{filter_}%')
             """

            s,res = CAQ.request(self.credencial,sql,(),'get',1)
            if not s:
                raise ValueError(res['error'])
           
            data = [
                {
                    'id':index,
                    'numero_pedido':value[0].strip(),
                    'cliente':value[1].strip(),
                    'fecha':value[2].strftime('%Y-%m-%d'),
                    'guia':f"{value[3].strip()}-{value[4].strip()}",
                    "factura":f"{value[5].strip()}-{value[6].strip()}",
                    "contacto":{
                        "url":value[7].strip(),
                        "nombre":value[8].strip(),
                        "documento":value[9].strip(),
                        "celular":value[10].strip(),
                        "direccion":value[11].strip(),
                        'vendedor':value[12].strip()
                        
                    }
                }
                for index,value in enumerate(res)
            ]
       
        except Exception as e:
            data['error'] = str(e)
        return Response(data)
class OptionsSeguimientos(GenericAPIView):
    def post(self,request,*args,**kwargs):
        data = {}
        self.fecha = datetime.now()
        datos = request.data

 
        self.credencial = Credencial(datos['credencial'])
        try:
            action = datos['action']
     
            if action == 'update_state':
                pass
            elif action == 'add_bonos':
                pass
            elif action == 'list_bonos':
                sql = f"""
                    SELECT 
                        mom_d_int,
                        cd_nomrut,
                        cd_image2,
                        cd_observ,
                        cd_monto,
                        cd_banco,
                        cd_numope,
                        cd_fecdep,
                        cd_monvou 
                    FROM m_contadigital 
                    WHERE 
                        mom_d_int=?
"""
                params = (datos['numero_pedido'],)
      
                s,res = CAQ.request(self.credencial,sql,params,'get',1)
            
                if not s:
                    raise ValueError(res['error'])
                data = [
                    {
                        'id':index,
                        'numero_pedido':value[0].strip(),
                        'filename':value[1].strip(),
                        'image':value[2].strip(),
                        'observacion':value[3].strip(),
                        'monto':f"{value[4]:.2f}",
                        'banco':value[5].strip(),
                        'numero_operacion':value[6].strip(),
                        'fecha_recepcion':value[7].strftime('%Y-%m-%d'),
                        'monto_voucher':f"{value[8]:.2f}"
                    }
                    for index,value in enumerate(res)
                ]
                
            else:
                data['error'] = 'No se ingreso una opcions correcta'
            
        except Exception as e:
            print(str(e))
            data['error'] = str(e)
        return Response(data)