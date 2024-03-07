# from weasyprint import HTML,CSS
from django.template.loader import get_template
from django.http import HttpResponse
from rest_framework.generics import GenericAPIView
from apirest.querys import Querys
def pdf_generate(request):
    html_template = get_template('mi_template_pdf.html')
    sql = "select art_codigo from t_articulo_imagen"
    images = Querys({'host':'192.168.1.40','db':'siia_demo_denim_art','user':'sa','password':'Noi2011'}).querys(sql,(),'get',1)
    data = [{'img':f"{img[0].strip()}A.JPG"} for img in images]
    context = {}
    context['images'] = data
    render_html = html_template.render(context)
    # pdf_file = HTML(string=render_html,base_url=request.build_absolute_uri()).write_pdf()
    # response = HttpResponse(pdf_file,content_type='application/pdf')
    # response['Content_Disposition'] = 'filename="home.pdf"'
    # return response
class GeneratedPDF(GenericAPIView):
    def get(self,request,*args,**kwargs):
        lista_ubicaciones = request.GET.getlist('arreglo[]',[])
        almacen = request.GET.get('almacen')
        linea = request.GET.get('linea')
        genero = request.GET.get('genero')
        modelo = request.GET.get('modelo')
        color = request.GET.get('color')
        temporada = request.GET.get('temporada')
        talla = request.GET.get('talla')
        html_template = get_template('mi_template_pdf.html')
        sql = "select top 100 art_codigo from t_articulo_imagen"
        images = Querys(kwargs).querys(sql,(),'get',1)
        data = [{'img':f"{img[0].strip()}A.JPG"} for img in images]
        context = {}
        context['images'] = data
        render_html = html_template.render(context)
        # pdf_file = HTML(string=render_html,base_url=request.build_absolute_uri()).write_pdf()
        # response = HttpResponse(pdf_file,content_type='application/pdf')
        # response['Content_Disposition'] = 'filename="home.pdf"'
        # return response