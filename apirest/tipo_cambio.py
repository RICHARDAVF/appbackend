from datetime import datetime
import requests
from apirest.credenciales import Credencial
from apirest.querys import CAQ
class TipoCambio:
    date : datetime = datetime.now()
    credencial : object = None
    def __init__(self,kwargs:dict,user:dict):
        self.kwargs : dict = kwargs
        self.tipo_c : int = 0
        self.user : dict = user
        self.tipo_cambio()
    def tipo_cambio(self):
        try:
            self.credencial = Credencial(self.kwargs)
            sql = f"SELECT TC_VENTA FROM t_tcambio WHERE TC_FECHA='{self.date.strftime('%Y-%m-%d')}' "
            s,result = CAQ.request(self.credencial,sql,(),'get',0)
         
            if not s:
                raise Exception("Error al obtener el tipo de cambio")
            if result is None:
                self.get_tc()
            else:
                self.tipo_c = float(result[0])
                
        except :
            raise
    def get_tc(self):
        url = f"https://api.apis.net.pe/v1/tipo-cambio-sunat?fecha={self.date.strftime('%Y-%m-%d')}"
        res = requests.get(url)
        if res.status_code == 200:
            values = res.json()
            sql = f"INSERT INTO t_tcambio(tc_fecha,tc_compra,tc_venta,usuario,fechausu) VALUES(?,?,?,?,?)"

            params = (self.date.strftime('%Y-%m-%d'),values['compra'],values['venta'],self.user['codigo'],self.date.strftime('%Y-%m-%d')) 
            s,_ = CAQ.request(self.credencial,sql,params,'post')
            if not s:
                raise Exception('Error al insertar tipo de cambio')
        else:
            raise Exception ('Error al consultar por el tipo de cambio')

    def __float__(self):
        return float(self.tipo_c)