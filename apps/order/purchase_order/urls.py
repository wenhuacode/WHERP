from tornado.web import url
from apps.order.purchase_order.handler import *

urlpattern = (
    url("/api/order/check_purchase_order/([A-Za-z0-9]+)/", CheckPurchaseOrderHandler),
    url("/api/order/un_purchase_order/([A-Za-z0-9]+)/", UnPurchaseOrderHandler),

    url("/api/order/check_purchase_order_return/([A-Za-z0-9]+)/", CheckPurchaseOrderReturnHandler),
    url("/api/order/un_purchase_order_return/([A-Za-z0-9]+)/", UnPurchaseOrderReturnHandler),
)