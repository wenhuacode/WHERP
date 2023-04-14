from tornado.web import url
from apps.data_center.transaction.customer_arap.handler import *


urlpattern = (
    url("/api/data_center/transaction/customer_arap/", CustomerARAPQueryHandler),
    url("/api/data_center/transaction/customer_arap_detail/", CustomerARAPDetailHandler),
)