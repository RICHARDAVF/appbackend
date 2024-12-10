import random
import string

def gen_id(longitud=10):
    caracteres = string.ascii_letters + string.digits
    clave = ''.join(random.choice(caracteres) for _ in range(longitud))
    return clave