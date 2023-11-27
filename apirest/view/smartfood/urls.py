from .guias.views import GuiasView,PDFFACTView,AnulacionGuiaView
from django.urls import path
urlpatterns = [
    path('v1/fact/',GuiasView.as_view()),
    path('v1/pdf/<str:serie>/<str:num>/',PDFFACTView.as_view()),
    path('v1/guia/anulacion/<str:serie>/<str:numero>/',AnulacionGuiaView.as_view())

]