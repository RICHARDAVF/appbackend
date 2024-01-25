from .guias.views import GuiasView,PDFFACTView,AnulacionGuiaView
from .pdf.views import SFPDFGenerate
from django.urls import path
urlpatterns = [
    path('v1/fact/',GuiasView.as_view()),
    path('v1/fact/pdf/<str:serie>/<str:num>/',PDFFACTView.as_view()),
    path('v1/guia/anulacion/<str:serie>/<str:numero>/',AnulacionGuiaView.as_view()),
    # path('v1/pdf/gre/<str:serie>/<str:numero>/',SFPDFGenerate.as_view())
]