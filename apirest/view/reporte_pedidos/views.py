from rest_framework.generics import GenericAPIView 
from rest_framework.response import Response

from apirest.credenciales import Credencial
from apirest.querys import CAQ
class ReportePedidos(GenericAPIView):
    def post(self,request,*args,**kwargs):
        data = {}
        try:
            datos = request.data
            self.credencial = Credencial(datos['credencial'])
            action = datos['action']

            if action == 'report':
                sql = f"""
                    SELECT 
                        a.MOV_COMPRO,
                        b.aux_docum, 
                        b.aux_nombre,
                        SUM(c.mom_valor) AS monto,
                        d.USU_NOMBRE,
                        SUM(c.MOM_CANT) as items,
						COALESCE(c2.tem_nombre,'SIN TEMPORADA') AS temporada
                    FROM cabepedido AS a
                    LEFT JOIN t_auxiliar AS b ON a.MOV_CODAUX=b.AUX_CLAVE
                    LEFT JOIN movipedido AS c ON a.MOV_COMPRO=c.mov_compro
					LEFT JOIN t_articulo AS c1 ON c.ART_CODIGO = c1.ART_CODIGO
					LEFT JOIN t_temporada AS c2 ON c1.tem_codigo = c2.tem_codigo
                    LEFT JOIN t_usuario AS d ON a.USUARIO = d.USU_CODIGO
                    WHERE 
						a.MOV_FECHA BETWEEN '{datos["desde"]}' AND '{datos["hasta"]}'
                        {self.filters(datos)}
                    GROUP BY
                        a.MOV_COMPRO,
                        b.AUX_DOCUM,
                        b.AUX_NOMBRE,
                        d.USU_NOMBRE,
						c2.tem_nombre
					
					ORDER BY a.MOV_COMPRO  ASC
                    """
                s,result = CAQ.request(self.credencial,sql,(),'get',1)
                print(result)
                if not s:
                    raise Exception(result['error'])
                data = [
                    {
                        "id":index,
                        "num_pedido":value[0].strip(),
                        "documento":value[1].strip(),
                        "nombre":value[2].strip(),
                        "monto":f"{float(value[3]):,.2f}",
                        "vendedor":value[4].strip(),
                        "items":int(value[5]),
                        "temporada":value[6].strip()
                    } for index,value in enumerate(result)
                ]
            elif action == 'search_data':
                
                sql = f"""SELECT
                            aux_nombre,
                            aux_clave,
                            aux_docum
                        FROM t_auxiliar 
                        WHERE 
                          
                            MAA_CODIGO='CL'
                          """
                s, result = CAQ.request(self.credencial,sql,(),'get',1)
               
                data['clientes'] = [
                    {
                        "id":index,
                        "value":item[1].strip(),
                        "label":item[0].strip(),
                        "documento":item[2].strip()
                    } for index,item in enumerate(result)
                ]
                sql = f"""
                        SELECT 
                            usu_codigo,
                            usu_nombre
                        FROM t_usuario
                    """
                s, result = CAQ.request(self.credencial,sql,(),'get',1)
            
                data['vendedores'] = [
                    {
                        "id":index,
                        "value":item[0].strip(),
                        "label":item[1].strip()
                    } for index,item in enumerate(result)
                ]
                sql = f"""
                    SELECT 
                        tem_codigo,
                        tem_nombre
                    FROM t_temporada
                """
                s, result = CAQ.request(self.credencial,sql,(),'get',1)
                data['temporadas'] = [{'id':-1,'value':'A',"label":'Todas'}]+[
                    {
                        "id":index,
                        "value":item[0].strip(),
                        "label":item[1].strip()
                        } for index,item in enumerate(result)
                ]
        except Exception as e:
            data['error'] = f"Ocurrio un error : {str(e)}"
        return Response(data)
    def filters(self,datos):
        fil = ''
        if len(datos["lista_temporadas"])>0:
            partial = ','.join(f"'{i}'" for i in datos["lista_temporadas"])
            fil+=f'AND c1.tem_codigo IN ({partial}) '
        if datos["cliente"]!='':
            fil+=f"""AND a.mov_codaux='{datos["cliente"]}' """
        if datos["vendedor"]!='':
            fil+=f"""AND a.ven_codigo='{datos["vendedor"]}' """

        return fil