from apirest.querys import CAQ


class Credencial:
    host:str = None
    name:str = None
    user:str = None
    password:str = None
    def __init__(self,credencial:dict):
        self.host = credencial['bdhost']
        self.name = credencial['bdname']
        self.user = credencial['bduser']
        self.password = credencial['bdpassword']
class Config:
 
    moneda : str  = None
    detracion : bool = False
    def __init__(self,credencial:object):
        self.credencial = credencial
        self.get_dates()
    def get_dates(self):
        sql = "SELECT par_moneda FROM t_parrametro"
        s,result = CAQ.request(self.credencial,sql,(),'get',0)
        if not s:
            raise
        self.moneda = result[0].strip()
