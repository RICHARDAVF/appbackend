from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from datetime import datetime

from apirest.querys import Querys
class Carga(GenericAPIView):
    def post(self,request,*args,**kwargs):
        data = {}
        try:
            datos = request.data
            for i in range(int(datos['cantidad_jaba'])):
                sql = "SELECT DOC_INGRE,doc_coding FROM t_almacen WHERE alm_codigo=?"
                doc_serie,doc_cod1 = Querys(kwargs).querys(sql,(datos['almacen'],),'get',0)
                sql = "SELECT doc_docum FROM  t_documento WHERE DOC_SERIE=? AND DOC_CODIGO='NE'"
                doc_corre =  Querys(kwargs).querys(sql,(doc_serie.strip(),),'get',0)[0]
                correlativo = f"{doc_serie.strip()}-{doc_corre}"
                fecha = datetime.now()
                mes = str(fecha.month).zfill(2)
                lote = ''.join([i[-2:] for i in reversed(datetime.now().strftime('%Y-%m-%d').split('-'))])
                params = (datos['almacen'],mes,fecha.strftime('%Y-%m-%d'),datos['codigo'],lote,'E',datos['operacion'],
                        datos['ubicacion'],datos['ubicacion'],1,100,lote,correlativo,datos['usuario'],
                        datetime.now(),doc_cod1,datos['proveedor'],datos['tra_codigo'],lote)
                sql = f"""
                        INSERT INTO movm{fecha.year}(
                        alm_codigo,mom_mes,mom_fecha,art_codigo,art_codadi,
                        mom_tipmov,ope_codigo,ubi_cod,ubi_cod1,mom_b_p_r,
                        mom_cant,mom_lote,mom_d_int,usuario,fechausu,
                        doc_cod1,mom_codaux,col_codigo,mom_lote2
                        ) VALUES({','.join('?' for i in params)})
                    """
                data = Querys(kwargs).querys(sql,params,'post')
                if not 'success' in data:
                    data['error'] = 'Ocurrio un error al grabar'
                    return Response(data)
                identi = ''.join(fecha.strftime('%d-%m-%Y').split('-'))
                sql = """SELECT top 1 identi3 FROM STK_MPT WHERE substring(identi3,1,8)=? order by identi3 desc"""
                identi3 = Querys(kwargs).querys(sql,(identi,),'get',0)
                
                if identi3 is None:
                    identi3 = '0001'
                else:
                    identi3 = str(int(identi3[0][8:])+1).zfill(4)
                
                params = (mes,datos['codigo'],100,1,lote,fecha,datos['usuario'],correlativo,lote,datos['tra_codigo'],f"{identi}{identi3}",fecha,datos['ubicacion'],
                        datos['proveedor'],lote)
                sql = f"""INSERT INTO STK_MPT(STK_MES,ART_CODIGO,STK_CANT,STK_B_P_R,STK_LOTE,fechausu,usuario,MOI_d_Int,art_codadi,
                col_codigo,IDENTI3,stk_fecha,ubi_codigo,mov_codaux,STK_LOTE2) VALUES({','.join('?' for i in params)})"""

                data = Querys(kwargs).querys(sql,params,'post')
                if not 'success' in data:
                    data['error'] = 'Ocurrio un error al grabar'
                    return Response(data)
                sql = "UPDATE t_documento SET doc_docum=? WHERE DOC_SERIE=? AND DOC_CODIGO='NE'"
                Querys(kwargs).querys(sql,(str(int(doc_corre)+1).zfill(7),doc_serie),'post')
        except Exception as e:
            data['error'] = 'Ocurrio un error al registrar'
        return Response(data)