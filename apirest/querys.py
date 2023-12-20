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
    def querys(self,sql,params,method,opt=1):
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
    def __init__(self,doc,tipo) :
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
