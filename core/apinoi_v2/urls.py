from django.urls import path
from core.apinoi_v2.view.pedidos.views import GuardarPedido,EditPedido
from core.apinoi_v2.view.pdf.views import PedidoPDF,PDFStock
from core.apinoi_v2.view.stock.views import ArticulosPromo
urlpatterns = [
    path(route="v2/guardar/pedido/<str:ruc>/",view=GuardarPedido.as_view()),
    path(route="v2/editar/pedido/<str:ruc>/",view=EditPedido.as_view()),
    path(route="v2/pdf/pedido/<str:ruc>/",view=PedidoPDF.as_view()),
    path(route="v2/promo/articulo/list/<str:ruc>/",view=ArticulosPromo.as_view()),
    path(route="v2/promo/articulo/list/<str:ruc>/",view=ArticulosPromo.as_view()),
    path(route="v2/pdf/stock/<str:ruc>/",view=PDFStock.as_view()),
]