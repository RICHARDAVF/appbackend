from rest_framework import generics
from rest_framework.response import Response
from datetime import datetime
from apirest.views import QuerysDb
class LiquiRegaView(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        data = {}
        sql  = f"""
            SELECT 
                'mov_pedido'=ISNULL(b.mov_compro,''),
                'mov_fecha'=ISNULL(b.mom_fecha,''),
                a.mov_codaux,
                'aux_razon'=ISNULL(c.aux_razon,''),
                'rou_tventa'=SUM(ISNULL(b.mom_valor,0))

            FROM guic{datetime.now().year} a 
            LEFT JOIN movipedido b 
            ON a.mov_pedido=b.mov_compro 
            LEFT JOIN t_auxiliar c ON a.mov_codaux=c.aux_clave 
            INNER JOIN guid{datetime.now().year} d ON a.mov_compro=d.mov_compro 
                AND b.art_codigo=d.art_codigo 
                LEFT JOIN t_articulo e ON b.art_codigo=e.art_codigo
            WHERE a.fac_coddoc<>' ' 
            AND a.elimini=0 
            AND a.gui_titgra=0 
            AND e.art_norega=0 
            GROUP BY 
                b.mov_compro,
                a.mov_codaux,
                c.aux_razon,
                b.mom_fecha

            HAVING SUM(ISNULL(b.mom_conreg,0))=0

            ORDER BY mov_codaux,mov_pedido

        """
        host = kwargs['host']
        db = kwargs['db']
        user = kwargs['user']
        password = kwargs['password']
        try:
            conn = QuerysDb.conexion(host,db,user,password)
            cursor = conn.cursor()
            cursor.execute(sql)
            dato = cursor.fetchall()
            conn.commit()
            conn.close()
            data=[]
            for index,item in enumerate(dato):
                d = {'id':index,'pedido':item[0],"fecha":item[1].strftime("%Y-%m-%d"),'codigo':item[2].strip(),'nombre':item[3].strip(),'monto':item[4]}
                data.append(d)
        except Exception as e:
            data['error'] = str(e)
        return Response(data)