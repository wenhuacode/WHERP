from tornado.web import url
from apps.data_center.inventory.handler import *


urlpattern = (
    url("/api/data_center/inventory/inventory_query/", InventoryQueryHandler),
    url("/api/data_center/inventory/inventory_query_detail/", InventoryQueryDetailHandler),
)