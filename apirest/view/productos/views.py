from rest_framework import generics
from rest_framework.response import Response
from apirest.views import QuerysDb
class ProductSeleView(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        host = kwargs['host']
        db = kwargs['db']
        user = kwargs['user']
        password = kwargs['password']
        codigo = kwargs['codigo'][:-2]
        conn = QuerysDb.conexion(host,db,user,password)
        sql = f"""
                SELECT 
                    a.art_codigo,
                    a.art_nombre,
                    a.art_partes,
                    b.tal_codigo 
                FROM 
                    (SELECT 
                        art_codigo,
                        art_nombre,
                        art_partes 
                    FROM t_articulo 
                    WHERE art_codigo LIKE '{codigo}%') AS a
                INNER JOIN t_tallas AS b
                ON a.art_partes=b.tal_grupo

                """

        cursor = conn.cursor()
        cursor.execute(sql)
        data = cursor.fetchall()
        conn.commit()
        conn.close()
        result = []
        for index,value in enumerate(data):
            d = {'id':index,'codigo':value[0].strip(),'nombre':value[1].strip(),'talla':value[3]}
            result.append(d)
        respuesta = {}
        for item in result:
            nombre = item["nombre"]
            talla = item["talla"]
            if nombre in respuesta:
                respuesta[nombre].append(talla)
            else:
                respuesta[nombre] = [talla]

        return Response({'message':respuesta})