from tornado.web import url
from apps.data_center.sale.handler import *


urlpattern = (
    url("/api/data_center/sale/product_sale_query/", ProductSaleQueryHandler),
    url("/api/data_center/sale/customer_sale_query/", CustomerSaleQueryHandler),
    url("/api/data_center/sale/product_sale_query_detail/", SaleDataDetailHandler),

    url("/api/data_center/sale/product_sale_discount/", SalesDiscountHandler),
    url("/api/data_center/sale/product_sale_discount_detail/", SalesDiscountDetailHandler),
    url("/api/data_center/sale/product_sale_detail_count/", ProductSaleDetailCountHandler),
)