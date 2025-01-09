from django.urls import path

from core.apinoi_v2.view.pedidos.views import GuardarPedido,EditPedido,PrecioProduct
from core.apinoi_v2.view.pdf.views import PedidoPDF,PDFStock,PDFview1
from core.apinoi_v2.view.stock.views import ArticulosPromo,StockReview
from core.apinoi_v2.view.flete.views import FleteView1,FleteView2,POSView,ValeMonto
from core.apinoi_v2.view.cliente.views import ListadoClientes
urlpatterns = [
    path(route="v2/guardar/pedido/<str:ruc>/",view=GuardarPedido.as_view()),
    path(route="v2/editar/pedido/<str:ruc>/",view=EditPedido.as_view()),
    path(route="v2/pdf/pedido/<str:ruc>/",view=PedidoPDF.as_view()),
    path(route="v2/promo/articulo/list/<str:ruc>/",view=ArticulosPromo.as_view()),
    path(route="v2/promo/articulo/list/<str:ruc>/",view=ArticulosPromo.as_view()),
    path(route="v2/pdf/stock/<str:ruc>/",view=PDFStock.as_view()),
    path(route="v2/stock/view/<str:ruc>/",view=StockReview.as_view()),
    path(route="v2/articulo/precio/<str:ruc>/",view=PrecioProduct.as_view()),
    path(route="v2/client/list/<str:ruc>/",view=ListadoClientes.as_view()),
    path(route="v2/costo/flete-1/<str:ruc>/",view=FleteView1.as_view()),
    path(route="v2/costo/flete-2/<str:ruc>/",view=FleteView2.as_view()),
    path(route="v2/costo/pos/<str:ruc>/",view=POSView.as_view()),
    path(route="v2/monto/vale/<str:ruc>/",view=ValeMonto.as_view()),
    path(route="v2/pdf/stock/dm/<str:ruc>/",view=PDFview1.as_view())
]