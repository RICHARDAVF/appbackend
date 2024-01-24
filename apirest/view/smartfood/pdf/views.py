from weasyprint import HTML,CSS
from django.template.loader import get_template
from django.http import HttpResponse
from rest_framework.generics import GenericAPIView
class SFPDFGenerate(GenericAPIView):
    def get(self,request,*args,**kwargs):
        html_template = get_template('smart_pdf.html')
        context = {
            'razon_social':'SMART FOOD CORPORATION S.A.C',
            'direccion':"AV. REDUCTO NRO 130 INT. 303 URB. LEURO MIRAFLORES - LIMA - LIMA",
            "telefono":'017515334',
            "email":'hola@ecoland.com.pe',
            'web':'www.ecoland.pe'
        }
        render_html = html_template.render(context)
        pdf_file = HTML(string=render_html,base_url=request.build_absolute_uri()).write_pdf()
        response = HttpResponse(pdf_file,content_type='application/pdf')
        response['Content_Disposition'] = 'filename="documento.pdf"'
        return  response