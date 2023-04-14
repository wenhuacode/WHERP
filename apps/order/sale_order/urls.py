from tornado.web import url
from apps.order.sale_order.handler import *

urlpattern = (
    url("/api/order/create/", OrderHandler),
    url("/api/order/update/([A-Za-z0-9]+)/", OrderHandler),
    url("/api/order/list/", OrderHandler),
    url("/api/order/detail/([A-Za-z0-9]+)/", GetOrderDetailHandler),
    url("/api/order/business_history/list/", GetBusinessHistoryHandler),
    # 销售订单
    url("/api/order/check_sale_order/([A-Za-z0-9]+)/", CheckSaleOrderHandler),
    url("/api/order/un_sale_order/([A-Za-z0-9]+)/", UnSaleOrderHandler),
    # 销售退货单
    url("/api/order/check_sale_order_return/([A-Za-z0-9]+)/", CheckSaleOrderReturnHandler),
    url("/api/order/un_sale_order_return/([A-Za-z0-9]+)/", UnSaleOrderReturnHandler),
)