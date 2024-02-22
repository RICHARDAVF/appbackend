
import requests
import json
import dotenv
import os
import pyodbc
dotenv.load_dotenv()
class Querys:
    def __init__(self,kwargs):
        self.kwargs = kwargs
    def conexion(self):
       
        return pyodbc.connect('DRIVER={SQL Server};SERVER=' +
                               self.kwargs['host']+';DATABASE='+self.kwargs['db']+';UID='+self.kwargs['user']+';PWD=' + self.kwargs['password'])
    def querys(self,sql:str,params:tuple,method:str,opt:int=1):
        conn = self.conexion()
        data = {}
        if conn is None:
            return conn
        try:
            cursor = conn.cursor()
            cursor.execute(sql,params)
            if method == 'get' and opt==1:
                data = cursor.fetchall()
            elif method == 'get' and opt==0:
                data = cursor.fetchone()
            elif method=='post':
                data['success'] = "Se guardo con exito"
            conn.commit()
            conn.close()
        except Exception as e:
            print(str(e),'consulta a la base de datos')
            data['error'] = f'Ocurrio un error : {str(e)}'
        return data 


class Validation:
    def __init__(self,doc:str,tipo:str) :
        self.doc  = doc
        self.tipo = tipo

    def valid(self):
        data = {}
        url = f"https://my.apidev.pro/api/dni/{self.doc}" if self.tipo=='dni' else f"https://apiperu.dev/api/ruc/{self.doc}"      
        response = requests.get(url,headers={
                "Authorization":f"Bearer {os.getenv(f'TOKEN_{self.tipo.upper()}')}"
            })
        res=json.loads(response.text)
        if not (res['success']):
            data['error'] = res['message']
        else:
            data = res
        return data
class CAQ:
    def conexion(self,credenciales:object):
         return pyodbc.connect("""DRIVER={SQL Server}
                               ;SERVER=""" +credenciales.host+
                               ';DATABASE='+credenciales.name+
                               ';UID='+credenciales.user+
                               ';PWD=' + credenciales.password)
    @classmethod
    def request(cls,credencial:object,sql:str,params:tuple,method:str,option:int=-1):
        """
        crendecial:Es un objeto que que atributos,host,name,user y passord
        sql:Consulta sql para sql server 2016 o superrior
        params: Los parametros para la condicion 
        method:
            GET:'Para recuperar los datos'
                'option':
                    1:Para consulta fetchall()
                    0:Para consulta fetchone()
            POST:'Para guardar los datos'
        """
        data = {}
        try:
            instance = cls()
            conn = instance.conexion(credencial)
            if conn is None:
                data['error'] = 'No se puede establecer una conexion con la base de datos'
                return False,data
            cursor = conn.cursor()
            cursor.execute(sql,params)
            if method == 'get' and option == 1:
                data = cursor.fetchall()
            
            elif method == 'get' and option == 0:
                data = cursor.fetchone()
            else:
                pass
            conn.commit()
            conn.close()
            return True,data
        except Exception as e:
            print(str(e))
            data['error'] = 'Ocurrio un error en el servidor'
            return False,data
        
