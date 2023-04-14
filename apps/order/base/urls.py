from tornado.web import url
from apps.order.base.handler import *


urlpattern = (
    url("/api/base/order_type/list/", GetOrderType),
    url("/api/base/finance/bank_no/list/", GetBankNoList),
    url("/api/base/finance/gc_as/list/", GetGcCostList),
    url("/api/base/finance/ic_as/list/", GetIcCostList),

    url("/api/order/order_no/([0-9]+)/", GETOrderNOHandler),
    url("/api/order/refuse/([A-Za-z0-9]+)/", RefuseOrderHandler),
    url("/api/order/cancel/([A-Za-z0-9]+)/", CancelOrderHandler),
)
