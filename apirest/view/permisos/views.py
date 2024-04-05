from rest_framework.response import Response
from rest_framework import generics,status
from apirest.querys import Querys
from datetime import datetime
class PermisosView(generics.GenericAPIView):
    def get(self,request,*args,**kwargs):
        data = {}
        try:
            sql = """SELECT opc_codigo,acceso,crear,editar,anular,eliminar
            FROM t_accesos
            WHERE usu_codigo=? AND opc_codigo IN ('050','051','060','629','005','008','285','251')"""
            perms = Querys(kwargs).querys(sql,(kwargs['usuario'],),'get',1)
            permisos = {}
            for perm in perms:
                permisos[perm[0].strip()] = {'acceso':perm[1]==1,
                                             'crear':perm[2]==1,
                                             'editar':perm[3]==1,
                                             'anular':perm[4]==1,
                                             'eliminar':perm[5]==1}
            sql = f"""
                SELECT opc_codigo,acceso,crear,modificar,anular,eliminar
                FROM t_niveles WHERE almacen=(SELECT top 1 alm_codigo FROM t_parrametro WHERE par_anyo={datetime.now().year}) AND usu_codigo=? AND opc_codigo IN ('171','167','299')
            """
            alm = Querys(kwargs).querys(sql,(kwargs['usuario'],),'get',1)
            for perm in alm:
                permisos[perm[0].strip()] = {'acceso':perm[1]==1,
                                             'crear':perm[2]==1,
                                             'editar':perm[3]==1,
                                             'anular':perm[4]==1,
                                             'eliminar':perm[5]==1}
            data['permisos'] = permisos
        except Exception as e:
            data['error'] = f"Ocurrio un error {str(e)}"
        return Response(data,status = status.HTTP_200_OK)