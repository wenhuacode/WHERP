from tornado.web import url
from apps.purchase.supplier.handler import *

urlpattern = (
    url("/api/supplier/list/", PurchaseHandler),
    url("/api/supplier/create/", PurchaseHandler),
    url("/api/supplier/update/([0-9]+)/", PurchaseHandler),
    url("/api/supplier/delete/([0-9]+)/", PurchaseHandler),
    url("/api/supplier/get_supplier/", getSupplierHandler),
    # url("/api/customer/import/", ImportAndExportPurchaseHandler),
    # url("/api/customer/export/", ImportAndExportPurchaseHandler),
    url("/api/supplier/account_current_list/", SupplierAccountCurrentHandler),

    # 应付表
    url("/api/supplier/account_payable/detail_list/", GETAPDetailListHandler),
)