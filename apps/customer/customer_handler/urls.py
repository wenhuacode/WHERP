from tornado.web import url
from apps.customer.customer_handler.handler import *

urlpattern = (
    url("/api/customerclassify/list/", CustomerClassifyHandler),
    url("/api/customerclassify/create/", CustomerClassifyHandler),
    url("/api/customerclassify/update/", CustomerClassifyHandler),
    url("/api/customerclassify/delete/([0-9]+)/", CustomerClassifyHandler),

    url("/api/addressclassify/list/", AddressClassifyHandler),
    url("/api/addressclassify/create/", AddressClassifyHandler),
    url("/api/addressclassify/update/([0-9]+)/", AddressClassifyHandler),
    url("/api/addressclassify/delete/([0-9]+)/", AddressClassifyHandler),

    url("/api/customer/", CustomerHandler),
    url("/api/customer/create/", CustomerHandler),
    url("/api/customer/update/([0-9]+)/", CustomerHandler),
    url("/api/customer/delete/([0-9]+)/", CustomerHandler),
    url("/api/customer/import/", ImportAndExportCustomerHandler),
    url("/api/customer/export/", ImportAndExportCustomerHandler),

    # 应收表
    url("/api/customer/account_receivable/", ARHandler),
    url("/api/customer/account_receivable/detail_list/", GETARDetailListHandler),

    # 客户查询选择
    url("/api/customer/query_customer/", queryCustomerHandler),

    # 批量修改客户信息
    url("/api/customer/batch/customerclassify/", BatchUpdateEditCustomerHandler),
)
