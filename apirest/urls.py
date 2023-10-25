from rest_framework import routers
from django.urls import path,include

from .views import (UserView,ProductoView,ClienteView,ProducAddView,PedidosView,EstadoPedido,
                    EditPedidoView,AgenciaView,SucursalView,UbigeoView,LugarEntregaView)
from apirest.view.cuentas.views import CuentasView,ReadCuentasView,ReadDocumentoView
from apirest.view.ordenC.views import ListOCview,DetalleViewOR
from apirest.view.stock.views import StockView,StockReview
from apirest.view.inventario.views import InventarioView,ValidateView
from apirest.view.productos.views import ProductSeleView
from apirest.view.liqui_regalos.views import LiquiRegaView
from apirest.view.traslado.views import TrasladoView,ProducTrasladoView,StockViewProduct
from apirest.view.ordenR.views import OrdenView,OrdenFormView,OrdenListView,OrdenDetalleView,AprobacionORView,EditOrdenView
from apirest.view.reporte.views import PDFView,PDFview1
from apirest.view.apis.views import SearchDNIRUC
from apirest.view.fact.views import Facturacion,PDFFACTView
from apirest.view.clientes.views import FamiliaView,FuenteView,TypeClienteView,ClienteCreateView
router = routers.DefaultRouter()
urlpatterns = [
    #DOCUMENTACION
   
    #LOGIN
    path('login/<str:ruc>/<str:usuario>/<str:password>/',UserView.as_view()),
    #PRODUCTOS
    path('product/<str:host>/<str:db>/<str:user>/<str:password>/<int:p>/<str:m>/<str:u>/<str:l>/<int:tallas>/<int:lote>/',ProductoView.as_view()),
    path('product/<str:host>/<str:db>/<str:user>/<str:password>/<str:codigo>/',ProductSeleView.as_view()),
    path('product/venta/add/',ProducAddView.as_view()),
    #CLIENTES
    path('client/<str:host>/<str:db>/<str:user>/<str:password>/',ClienteView.as_view()),
    path('client/new/<str:host>/<str:db>/<str:user>/<str:password>/',ClienteCreateView.as_view()),
    path('client/type/<str:host>/<str:db>/<str:user>/<str:password>/',TypeClienteView.as_view()),
    
    #FAMILIA
    path('familia/<str:host>/<str:db>/<str:user>/<str:password>/',FamiliaView.as_view()),
    #FUENTE
    path('fuente/<str:host>/<str:db>/<str:user>/<str:password>/',FuenteView.as_view()),
    #PEDIDOS
    path('pedidos/<str:host>/<str:db>/<str:user>/<str:password>/<int:all>/',PedidosView.as_view()),
    path('pedidos/edit/<str:host>/<str:db>/<str:user>/<str:password>/<str:codigo>/',EditPedidoView.as_view()),
    path('pedidos/state/<str:host>/<str:db>/<str:user>/<str:password>/',EstadoPedido.as_view()),
    path('pedidos/agencias/<str:host>/<str:db>/<str:user>/<str:password>/',AgenciaView.as_view()),
    path('pedidos/sucursal/<str:host>/<str:db>/<str:user>/<str:password>/<str:codigo>/',SucursalView.as_view()),
   #LUGAR DE ENTREGA
    path('lugar/entrega/<str:host>/<str:db>/<str:user>/<str:password>/<str:codigo>/<str:cliente>/',LugarEntregaView.as_view()),

    #CUENTAS
    path('cuentas/<str:host>/<str:db>/<str:user>/<str:password>/<int:filter>/',CuentasView.as_view()),
    path('cuentas/read/<str:host>/<str:db>/<str:user>/<str:password>/<str:codigo>/<int:filter>/',ReadCuentasView.as_view()),
    path('cuentas/read/doc/<str:host>/<str:db>/<str:user>/<str:password>/<str:codigo>/<str:year>/',ReadDocumentoView.as_view()),
    #ORDEN REQUERIMIENTO
    path('orden/<str:host>/<str:db>/<str:user>/<str:password>/',OrdenView.as_view()),
    path('orden/form/<str:host>/<str:db>/<str:user>/<str:password>/',OrdenFormView.as_view()),
    path('orden/list/<str:host>/<str:db>/<str:user>/<str:password>/',OrdenListView.as_view()),
    path('orden/list/detalle/<str:host>/<str:db>/<str:user>/<str:password>/<str:numero>/',OrdenDetalleView.as_view()),
    path('orden/edit/<str:host>/<str:db>/<str:user>/<str:password>/<str:numero>/',EditOrdenView.as_view()),
    path('orden/apro/<str:host>/<str:db>/<str:user>/<str:password>/',AprobacionORView.as_view()),
    #ORDEN DE COMPRA
    path('compra/<str:host>/<str:db>/<str:user>/<str:password>/',ListOCview.as_view()),
    path('compra/detalle/<str:host>/<str:db>/<str:user>/<str:password>/<str:numero>/',DetalleViewOR.as_view()),
    #STOCK
    path('stock/<str:host>/<str:db>/<str:user>/<str:password>/<str:alm>/<str:ubi>/<int:talla>/',StockView.as_view()),
    path('stock/view/<str:host>/<str:db>/<str:user>/<str:password>/<str:alm>/<str:ubi>/<str:codigo>/<str:pedido>/<str:talla>/',StockReview.as_view()),
    #INVENTARIO
    path('inv/<str:host>/<str:db>/<str:user>/<str:password>/',InventarioView.as_view()),
    path('val/<str:host>/<str:db>/<str:user>/<str:password>/<str:codigo>/<str:serie>/',ValidateView.as_view()),
    #LIQUIDACION DE REGALOS
    path('li-re/<str:host>/<str:db>/<str:user>/<str:password>/',LiquiRegaView.as_view()),
    #TRASLADO VIEW
    path('traslado/<str:host>/<str:db>/<str:user>/<str:password>/',TrasladoView.as_view()),
    path('traslado/products/<str:host>/<str:db>/<str:user>/<str:password>/<str:ubi>/<str:local>/',ProducTrasladoView.as_view()),
    path('traslado/stock/<str:host>/<str:db>/<str:user>/<str:password>/<str:codigo>/',StockViewProduct.as_view()),
    #UBIGEO
    path('ubigeo/<str:host>/<str:db>/<str:user>/<str:password>/',UbigeoView.as_view()),
    #REPORTE
    path('reporte1/',PDFView.as_view()),
    path('reporte2/',PDFview1.as_view()),
    #FACTURACION ELECTRONICA
    path("fact/",Facturacion.as_view()),
    path('fact/pdf/<str:serie>/<str:num>/',PDFFACTView.as_view(),name='generate_pdf'),
    #VALIDACION DE DOCUMENTOS
    path('searchdoc/<str:doc>/<str:tipo>/',SearchDNIRUC.as_view(),name='search_doc')

]