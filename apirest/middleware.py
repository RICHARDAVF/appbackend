# middleware.py

import datetime

class RegistroPeticionesMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Antes de pasar la solicitud a las vistas, registra la información
        self.registrar_peticion(request)

        # Continúa con el procesamiento de la solicitud
        response = self.get_response(request)

        return response

    def registrar_peticion(self, request):
        metodo = request.method
        ruta = request.path
        fecha_hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mensaje = f"{fecha_hora} - {metodo} {ruta}\n"

        # Ruta al archivo de registro
        ruta_archivo = "peticiones.log"

        # Abre el archivo en modo "a" (append) y escribe el mensaje
        with open(ruta_archivo, "a") as archivo:
            archivo.write(mensaje)
