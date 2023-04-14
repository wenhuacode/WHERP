from tornado.web import url
from tornado.web import StaticFileHandler

from apps.users import urls as user_urls
from apps.customer.customer_handler import urls as customer_urls
from apps.admin.role import urls as role_urls
from apps.admin.menu import urls as menu_urls
from apps.product.product_handler import urls as product_urls
from apps.order.sale_order import urls as sale_order_urls
from apps.purchase.supplier import urls as purchase_urls
from apps.finance.subsidiary_ledger import urls as subsidiary_ledger_urls
from apps.finance.accounting_subject import urls as accounting_subject_urls
from apps.inventory_management.inventory_distribution_cost import urls as inventory_management_urls
from apps.order.inventort_order import urls as inventory_order_urls
from apps.order.finance_order import urls as finance_order_urls
from apps.order.purchase_order import urls as purchase_order_urls
from apps.admin.page_permissions import urls as page_permissions_urls
from apps.order.base import urls as base_urls
from apps.data_center.purchase import urls as purchase_data_urls
from apps.data_center.sale import urls as sale_data_urls
from apps.data_center.inventory import urls as inventory_data_urls
from apps.data_center.transaction.customer_arap import urls as customer_arap_urls
from apps.data_center.financial import urls as financial_urls
from wherp.settings import settings

urlpattern = [
    (url("/media/(.*)", StaticFileHandler, {'path': settings["MEDIA_ROOT"]}))
]

urlpattern += user_urls.urlpattern
urlpattern += customer_urls.urlpattern
urlpattern += role_urls.urlpattern
urlpattern += menu_urls.urlpattern
urlpattern += product_urls.urlpattern
urlpattern += sale_order_urls.urlpattern
urlpattern += purchase_urls.urlpattern
urlpattern += subsidiary_ledger_urls.urlpattern
urlpattern += accounting_subject_urls.urlpattern
urlpattern += inventory_management_urls.urlpattern
urlpattern += inventory_order_urls.urlpattern
urlpattern += page_permissions_urls.urlpattern
urlpattern += base_urls.urlpattern
urlpattern += finance_order_urls.urlpattern
urlpattern += purchase_order_urls.urlpattern
urlpattern += purchase_data_urls.urlpattern
urlpattern += sale_data_urls.urlpattern
urlpattern += inventory_data_urls.urlpattern
urlpattern += customer_arap_urls.urlpattern
urlpattern += financial_urls.urlpattern