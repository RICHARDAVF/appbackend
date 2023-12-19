from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from apirest.hash import HasPassword
from apirest.models import UsuarioCredencial
from apirest.querys import Querys
from apirest.serializer import UsuarioSerializer
 
class Login(GenericAPIView):
    serializer_class = UsuarioSerializer

    def get(self,request,*args,**kwargs):
        data = {}
        ruc = kwargs['ruc']
        usuario = kwargs['usuario']
        password = kwargs['password']

        try:
            user = UsuarioCredencial.objects.get(ruc=ruc)
            password = HasPassword(password).hash()
            sql = """SELECT 
                usu_codigo,
                ven_codigo,
                USU_ABREV
                FROM t_usuario
                WHERE 
                    USU_ABREV=?
                    AND USU_LOGIN=? 
                """
            params = (usuario,password)
            result = Querys({'host':user.bdhost,'db':user.bdname,'user':user.bduser,'password':user.bdpassword}).querys(sql,params,'get',0)
            if result is None:
                data['error'] = "Usuario o contraseña incorrecta"
                return Response(data)
            user = self.serializer_class(user).data
            data['credencial'] = user
            data['usuario'] = {
                'codigo_usuario':result[0].strip(),
                'codigo_vendedor':result[1].strip(),
                'nombre_usuario':result[2].strip()
                }
        except UsuarioCredencial.DoesNotExist:
            data['error'] = f'Empresa no registrada'
        return Response(data)
