from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from datetime import datetime
import random
from apirest.querys import Querys
class Carga(GenericAPIView):
    def validaciones(self,datos):
        data = {}
        try:
            if not datos['cantidad'].isdigit() or int(datos['cantidad'])==0:
                data['error'] = 'Ingrese una cantidad correcta'
                return False,data
        except Exception as e:
            data['error'] = 'Ocurrio un error, verifique que todos los campos sean correctos y coherentes'
            return False,data
    def post(self,request,*args,**kwargs):
        data = {}
        try:
            datos = request.data
            
            if datos['cantidad'].strip()=='' or not datos['cantidad'].isdigit() or int(datos['cantidad'])<=0  :
                data['error'] = 'La cantidad no es correcta'
                return Response(data)
            if  not datos['cantidad_jaba'].isdigit() or datos['cantidad_jaba'].strip()=='' or int(datos['cantidad_jaba'])<=0 :
                data['error'] = 'La cantidad de jabas es incorrecta'
                return Response(data)
            fecha = datetime.now()
            for i in range(int(datos['cantidad_jaba'])):
                sql = "SELECT DOC_INGRE,doc_coding FROM t_almacen WHERE alm_codigo=?"
                doc_serie,doc_cod1 = Querys(kwargs).querys(sql,(datos['almacen'],),'get',0)
                sql = "SELECT doc_docum FROM  t_documento WHERE DOC_SERIE=? AND DOC_CODIGO='NE'"
                doc_corre =  Querys(kwargs).querys(sql,(doc_serie.strip(),),'get',0)[0]
                correlativo = f"{doc_serie.strip()}-{doc_corre}"
                mes = str(fecha.month).zfill(2)
                params = (datos['almacen'],mes,fecha.strftime('%Y-%m-%d'),datos['codigo'],datos['lote'],'E',datos['operacion'],
                        datos['ubicacion'],datos['ubicacion'],1,int(datos['cantidad']),datos['lote'],correlativo,datos['usuario'],
                        fecha.strftime('%Y-%m-%d %H:%M:%S'),doc_cod1,datos['proveedor'],datos['tra_codigo'],datos['lote2'])
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
                
                params = (mes,datos['codigo'],100,1,datos['lote'],fecha.strftime('%Y-%m-%d %H:%M:%S'),datos['usuario'],correlativo,datos['lote'],datos['tra_codigo'],f"{identi}{identi3}",fecha.strftime('%Y-%m-%d'),datos['ubicacion'],
                        datos['proveedor'],datos['lote2'],0)
                sql = f"""INSERT INTO STK_MPT(STK_MES,ART_CODIGO,STK_CANT,STK_B_P_R,STK_LOTE,fechausu,usuario,MOI_d_Int,art_codadi,
                col_codigo,IDENTI3,stk_fecha,ubi_codigo,mov_codaux,STK_LOTE2,stk_serie) VALUES({','.join('?' for i in params)})"""

                data = Querys(kwargs).querys(sql,params,'post')
               
                if not 'success' in data:
                    data['error'] = 'Ocurrio un error al grabar'
                    return Response(data)
                sql = "UPDATE t_documento SET doc_docum=? WHERE DOC_SERIE=? AND DOC_CODIGO='NE'"
                res = Querys(kwargs).querys(sql,(str(int(doc_corre)+1).zfill(7),doc_serie),'post')
                if not 'success' in res:
                    data['error'] = 'Ocurrio un error el grabar en los documentos'
                    return Response(data)
            data['success'] = data['success']+f"\n{self.consultar_jabas()}"
            if self.exist_peso():
                data['success'] = f"{data['success']} \n✔Falta registrar los pesos"
        except Exception as e:
            print(str(e),'Registrar jabas')
            data['error'] = 'Ocurrio un error al registrar'
        return Response(data)
    def consultar_jabas(self):
        datos = self.request.data
        fecha = datetime.now().strftime('%Y-%m-%d')
        data = 0
        anio = datetime.now().year
        sql  = f"""SELECT 
                    COUNT(*) AS jabas 
                FROM MOVM{anio} 
                WHERE 
                    col_codigo=?
                    AND MOM_FECHA=? """
        params = (datos['tra_codigo'],fecha)
        data = Querys(self.kwargs).querys(sql,params,'get',0)
        return f'✔ El operario va {data[0]} jabas'
    def exist_peso(self):
        sql = "SELECT*FROM m_peso_aleatorio WHERE bal_fecha=?"
        fecha = datetime.now().strftime('%Y-%m-%d')
        result = Querys(self.kwargs).querys(sql,(fecha,),'get',0)
        return result is None
class RegistroPeso(GenericAPIView):
    def post(self,request,*args,**kwargs):
        data ={}
        try:
            datos = request.data
            if datos['action'] == 'edit':
                status,message = self.data_update()
               
                if status:
                    data['success'] = message['success']
                else:
                    data['error'] = message['error']
                return Response(data)
            val = datos['pesos']
            dates = [val[i][f'value-id{i+1}'] for i in range(len(val))]
            status,dates = self.validate(dates)
            if not status:
                data['error'] = 'Ingrese pesos validos y mayores a cero'
                return Response(data)
            fecha = datetime.now()
            params = (fecha.strftime('%Y-%m-%d'),'001',fecha,*dates)
            sql = f"""
                INSERT INTO m_peso_aleatorio
                    (bal_fecha,usuario,fechausu,{','.join(f'bal_peso'+str(i+1).zfill(2) for i in range(len(dates)))})
                    VALUES ({','.join('?' for i in params)}) 
                """
          
            data = Querys(kwargs).querys(sql,params,'post')

        except Exception as e:
            print(str(e))
            data['error'] = 'Ocurrio un error al registrar los pesos'
        return Response(data)
    def validate(self,dates):
        date = []
        try:
            for i in dates:
                if float(i)<=0:
                    return False,date
                date.append(float(i))
            return True,date 
        except:
            return False,date

    def data_update(self):
        data = {}
        try:
            datos = self.request.data
            val = datos['pesos']
            dates = [val[i][f'value-id{i+1}'] for i in range(len(val))]
            status,dates = self.validate(dates)
            if not status:
                data['error'] = 'Ingrese pesos validos y mayores a cero'
                return False,data
            sql = f""" UPDATE m_peso_aleatorio SET {','.join('bal_peso'+f'{str(i+1).zfill(2)}=?' for i in range(20))} WHERE bal_fecha=?"""
            params = (*dates,datetime.now().strftime('%Y-%m-%d'))
            res = Querys(self.kwargs).querys(sql,params,'post')
            if 'error' in res:
                data['error'] = 'Ocurrio un error al editar los pesos'
                return False,data
            data['success'] = 'Los pesos se editaron exitosamente'
            return True,data
        except Exception as e:
            data['error'] = 'Ocurrio un error en la edicion'
            return False,data
    def get(self,request,*args,**kwargs):
        data = {}
        try:
            sql = f"SELECT TOP 1 {','.join('bal_peso'+f'{i+1}'.zfill(2) for i in range(20))} FROM m_peso_aleatorio WHERE bal_fecha=? ORDER BY bal_fecha DESC"
            result = Querys(kwargs).querys(sql,(datetime.now().strftime('%Y-%m-%d'),),'get',0)
            if not result is None:
                data['inputs'] = [{'id':f'id{index+1}','placeholder':f'Peso {index+1}','value':str(value)} for index,value in enumerate(result)]
            else:
                data['inputs'] = []
        except Exception as e:
            data['error'] = 'Ocurrio un error al recuperar los datos'
        return Response(data)

class ProcessData(GenericAPIView):
    def post(self,request,*args,**kwargs):
        data = {}
        try:
            fecha = datetime.now()
            sql = f"SELECT  {','.join('bal_peso'+f'{i+1}'.zfill(2) for i in range(20))} FROM m_peso_aleatorio WHERE bal_fecha=? ORDER BY bal_fecha DESC"
            result = Querys(kwargs).querys(sql,(fecha.strftime('%Y-%m-%d'),),'get',0)
            if result is None:
                data['error'] = 'Falta registrar los pesos'
                return Response(data)
            pesos = list(result)
            sql = f"SELECT MOI_d_Int FROM STK_MPT WHERE stk_fecha =?  AND stk_bruto=0 "
            result = Querys(kwargs).querys(sql,(fecha.strftime('%Y-%m-%d'),),'get',1)
            
            if len(result)==0:
                data['success'] = 'Los datos se procesaron correctamente'
                return Response(data)
            for i in range(len(result)):
                sql = f'UPDATE  MOVM{fecha.year} SET mom_bruto=? WHERE MOM_FECHA=?  AND MOM_D_INT=?'
                peso = random.choice(pesos)
                params = (peso,fecha.strftime('%Y-%m-%d'),result[i][0])
                data = Querys(kwargs).querys(sql,params,'post')
             
                params = (peso,fecha.strftime('%Y-%m-%d'),result[i][0])
                sql = f'UPDATE  STK_MPT SET stk_bruto=? WHERE stk_fecha=?  AND MOI_d_Int=?'
                data = Querys(kwargs).querys(sql,params,'post')
               
            if 'success' in data:
                data['success'] = 'Lo datos se procesaron correctamente'
            else:
                data['error'] = 'No se procesaron los datos'
            
        except Exception as e :
            print(str(e),'procesamiento de datos')
            data['error'] = 'Ocurrio un error al procesar la data'
        return Response(data)
class ListadoCarga(GenericAPIView):
    def post(self,request,*args,**kwargs):
        data = {}
        anio = datetime.now().year
        try:
            fecha = datetime.now()
            datos = request.data
            sql = f"""SELECT 
                        COUNT(*) as jabas,
                        a.FECHAUSU,
                        'provedor' = COALESCE(aux.AUX_NOMBRE, ''),
                        'operario' = COALESCE(tra.TRA_NOMBRE, ''),
                        'almacen' = COALESCE(alm.ALM_NOMBRE, ''),
                        'ubicacion' = COALESCE(ubi.ubi_nombre, '')
                    FROM movm{anio} AS a
                    LEFT JOIN t_auxiliar AS aux ON aux.MAA_CODIGO = 'PR' AND aux.AUX_CLAVE = a.mom_codaux
                    LEFT JOIN TRABAJADOR AS tra ON tra.TRA_CODIGO = a.col_codigo
                    LEFT JOIN t_almacen AS alm ON alm.ALM_CODIGO = a.ALM_CODIGO
                    LEFT JOIN t_ubicacion AS ubi ON ubi.ubi_codigo = a.UBI_COD1
                    WHERE 
                        a.col_codigo = ?
                        AND a.MOM_FECHA = ?
                    GROUP BY a.FECHAUSU,aux.AUX_NOMBRE,tra.TRA_NOMBRE,alm.ALM_NOMBRE,ubi.ubi_nombre
                    ORDER BY a.FECHAUSU

                        """
            params = (datos['codigo'],fecha.strftime('%Y-%m-%d'))
            result = Querys(kwargs).querys(sql,params,'get',1)
            if len(result)==0:
                data['msg'] = 'El operario aun no tiene registros'
                return Response(data)
           
            dates = [
                {
                    'id':index+1,
                    'n_jabas':int(value[0]),
                    'fecha':value[1].strftime('%Y-%m-%d %H-%M-%S'),
                    'proveedor':value[2].strip(),
                    'operario':value[3].strip(),
                    'almacen':value[4].strip(),
                    'ubicacion':value[5].strip(),
                } for index, value in enumerate(result)
                    ]
            total_jabas = sum([item['n_jabas'] for item in dates])
            data['list'] = dates
            data['total'] = total_jabas
            return Response(data)
        except Exception as e:
            print(str(e),'listado carga')
            data['error'] = 'Ocurrio un error al carga los datos'
        return Response(data)
class JabaUbicacion(GenericAPIView):
    def get(self,request,*args,**kwargs):
        data = {}
        anio = datetime.now().year
        try:
            sql =f"""
                SELECT 
                    COUNT(*) AS jabas 
                FROM movm{anio} 
                WHERE 
                    MOM_FECHA=? 
                    AND UBI_COD1=? """
            params = (datetime.now().strftime('%Y-%m-%d'),kwargs['ubi'])
            result = Querys(kwargs).querys(sql,params,'get',0)
            if result is None:
                total = 0
            else:
                total = result[0]
            data['total_jabas'] = total
        except Exception as e:
            print(str(e))
            data['error'] = 'Ocurrio un error al recuperar el total de las jabas'
        return Response(data)
