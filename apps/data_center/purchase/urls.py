from tornado.web import url
from apps.data_center.purchase.handler import *


urlpattern = (
    url("/api/data_center/purchase/product_purchase_query/", ProductPurchaseQueryHandler),
    url("/api/data_center/purchase/customer_purchase_query/", CustomerPurchaseQueryHandler),
    url("/api/data_center/purchase/product_purchase_query_detail/", PurchaseDataDetailHandler),
)