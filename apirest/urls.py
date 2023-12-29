from rest_framework import routers
from django.urls import path,include

from .views import (UserView,ProductoView,ClienteView,ProducAddView,PedidosView,EstadoPedido,
                    EditPedidoView,AgenciaView,SucursalView,UbigeoView,LugarEntregaView,VersionAppView,TipoPago)
from apirest.view.cuentas.views import CuentasView,ReadCuentasView,ReadDocumentoView
from apirest.view.ordenC.views import ListOCview,DetalleViewOR
from apirest.view.stock.views import StockView,StockReview
from apirest.view.inventario.views import InventarioView,ValidateView,DeleteInventario,InventarioWithLote
from apirest.view.productos.views import ProductSeleView
from apirest.view.liqui_regalos.views import LiquiRegaView
from apirest.view.traslado.views import TrasladoView,ProducTrasladoView,StockViewProduct
from apirest.view.ordenR.views import OrdenView,OrdenFormView,OrdenListView,OrdenDetalleView,AprobacionORView,EditOrdenView
from apirest.view.reporte.views import PDFView,PDFview1,DownloadPDF,PDFGENERATEView
from apirest.view.apis.views import SearchDNIRUC
from apirest.view.guias.views import Facturacion,PDFFACTView,AnulacionGuiaView
from apirest.view.clientes.views import FamiliaView,FuenteView,TypeClienteView,ClienteCreateView,ClientList
from apirest.view.pedido.views import PdfPedidoView,PrecioProduct,NotaPedido,GuardarPedido,EditPedido
from apirest.view.apps.views import DownloadAppView,DownloadAppMapring
from apirest.view.permisos.views import PermisosView
from apirest.view.login.views import Login
from apirest.view.general.views import Almacenes,Operaciones,Proveedores,Articulos,Trabajador,Ubicaciones,Incidencia
from apirest.view.carga.views import Carga,RegistroPeso,ProcessData,ListadoCarga,JabaUbicacion
from apirest.view.incidencias.views import RegistroIncidecias
# from apirest.view.pdf.views import pdf_generate,GeneratedPDF
router = routers.DefaultRouter()
urlpatterns = [
    #DOCUMENTACION
   
    #LOGIN
    path('v1/login/<str:ruc>/<str:usuario>/<str:password>/',Login.as_view()),
    path('login/<str:ruc>/<str:usuario>/<str:password>/',UserView.as_view()),
    #ALMACENES
    path('v1/alm/<str:host>/<str:db>/<str:user>/<str:password>/',Almacenes.as_view()),
    #OPERACIONES
    path('v1/op/<str:host>/<str:db>/<str:user>/<str:password>/',Operaciones.as_view()),
    #PROVEEDORES
    path('v1/pro/<str:host>/<str:db>/<str:user>/<str:password>/',Proveedores.as_view()),
    #TRABAJADOR
    path('v1/tra/<str:host>/<str:db>/<str:user>/<str:password>/<str:codigo>/',Trabajador.as_view()),
    #UBICACIONES
    path('v1/ubi/<str:host>/<str:db>/<str:user>/<str:password>/',Ubicaciones.as_view()),
    #INCIDENCIAS
    path('v1/inc/<str:host>/<str:db>/<str:user>/<str:password>/',Incidencia.as_view()),
    path('v1/inc/add/<str:host>/<str:db>/<str:user>/<str:password>/',RegistroIncidecias.as_view()),
    path('v1/inc/list/<str:host>/<str:db>/<str:user>/<str:password>/',RegistroIncidecias.as_view()),

  
    #CARGA
    path('v1/carga/<str:host>/<str:db>/<str:user>/<str:password>/',Carga.as_view()),
    path('v1/peso/<str:host>/<str:db>/<str:user>/<str:password>/',RegistroPeso.as_view()),
    path('v1/process/data/<str:host>/<str:db>/<str:user>/<str:password>/',ProcessData.as_view()),
    path('v1/list/carga/<str:host>/<str:db>/<str:user>/<str:password>/',ListadoCarga.as_view()),
    path('v1/total/jabas/<str:host>/<str:db>/<str:user>/<str:password>/<str:ubi>/',JabaUbicacion.as_view()),

    #PERMISOS
    path('permisos/<str:host>/<str:db>/<str:user>/<str:password>/<str:usuario>/',PermisosView.as_view()),
    #ARTICULOS
    path('product/<str:host>/<str:db>/<str:user>/<str:password>/<int:p>/<str:m>/<str:u>/<str:l>/<int:tallas>/<int:lote>/',ProductoView.as_view()),
    path('product/<str:host>/<str:db>/<str:user>/<str:password>/<str:codigo>/',ProductSeleView.as_view()),
    path('product/venta/add/',ProducAddView.as_view()),
    path('v1/art/<str:host>/<str:db>/<str:user>/<str:password>/<str:alm>/',Articulos.as_view()),
    #PRECIO PRODUCTOS
    path('product/precio/<str:host>/<str:db>/<str:user>/<str:password>/<str:precio>/<str:moneda>/<str:codigo>/',PrecioProduct.as_view()),
    #NOTA DE PEDIDO
    path('nota/pedido/<str:host>/<str:db>/<str:user>/<str:password>/',NotaPedido.as_view()),
    #CLIENTES
    path('client/<str:host>/<str:db>/<str:user>/<str:password>/',ClienteView.as_view()),
    path('client/list/<str:host>/<str:db>/<str:user>/<str:password>/',ClientList.as_view()),
    path('client/new/<str:host>/<str:db>/<str:user>/<str:password>/',ClienteCreateView.as_view()),
    path('client/type/<str:host>/<str:db>/<str:user>/<str:password>/',TypeClienteView.as_view()),
    #TIPO DE PAGO
    path('tipo/pago/<str:host>/<str:db>/<str:user>/<str:password>/',TipoPago.as_view()),

    #FAMILIA
    path('familia/<str:host>/<str:db>/<str:user>/<str:password>/',FamiliaView.as_view()),
    #FUENTE
    path('fuente/<str:host>/<str:db>/<str:user>/<str:password>/',FuenteView.as_view()),
    #PEDIDOS
    path('pedidos/<str:host>/<str:db>/<str:user>/<str:password>/<int:all>/',PedidosView.as_view()),
    path('pedidos/edit/<str:host>/<str:db>/<str:user>/<str:password>/<str:codigo>/<str:action>/',EditPedidoView.as_view()),
    path('pedidos/state/<str:host>/<str:db>/<str:user>/<str:password>/',EstadoPedido.as_view()),
    path('pedidos/sucursal/<str:host>/<str:db>/<str:user>/<str:password>/<str:codigo>/',SucursalView.as_view()),
    path('pedidos/pdf/<str:host>/<str:db>/<str:user>/<str:password>/<str:codigo>/',PdfPedidoView.as_view()),
    path('guardar/pedido/<str:host>/<str:db>/<str:user>/<str:password>/',GuardarPedido.as_view()),
    path('editar/pedido/<str:host>/<str:db>/<str:user>/<str:password>/<str:codigo>/',EditPedido.as_view()),

    
    #AGENCIAS
    path('agencias/<str:host>/<str:db>/<str:user>/<str:password>/',AgenciaView.as_view()),
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
    path('val/<str:host>/<str:db>/<str:user>/<str:password>/<str:codigo>/',ValidateView.as_view()),
    path('del/<str:host>/<str:db>/<str:user>/<str:password>/<str:identi>/<str:mom_d_int>/',DeleteInventario.as_view()),
    path('val/lote/<str:host>/<str:db>/<str:user>/<str:password>/<str:codigo>/',InventarioWithLote.as_view()),


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
    path('download/pdf/<str:ruc>/<str:cod>/<str:codigo>/',DownloadPDF.as_view()),
    path('reporte3/',PDFGENERATEView.as_view()),

    #GUIA ELECTRONICA DE VENTA Y TRASLADO
    path("fact/",Facturacion.as_view()),
    path('fact/pdf/<str:serie>/<str:num>/',PDFFACTView.as_view(),name='generate_pdf'),
    path('guia/anulacion/<str:serie>/<str:numero>/',AnulacionGuiaView.as_view(),name='anulacion'),
    #VALIDACION DE DOCUMENTOS
    path('searchdoc/<str:doc>/<str:tipo>/',SearchDNIRUC.as_view(),name='search_doc'),
    #VERSION DE LA APLICACION MOVIL ANDROID
    path('check/version/app/',VersionAppView.as_view()),
    path('download/app/',DownloadAppView.as_view()),

    #APLICACION MAPRING 
    path('v1/download/app/',DownloadAppMapring.as_view()),
    #GENERACION DE PDF
    # path('generate/pdf/',pdf_generate),
    # path('pdf/<str:host>/<str:db>/<str:user>/<str:password>/',GeneratedPDF.as_view())

]
