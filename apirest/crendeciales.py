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
   