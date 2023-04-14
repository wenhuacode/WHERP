from tornado.web import url
from apps.inventory_management.inventory_distribution_cost.handler import *

urlpattern = (
    # 仓库管理
    url("/api/storehouse_management/list/", StorehouseManagementHandler),
    url("/api/storehouse_management/create/", StorehouseManagementHandler),
    url("/api/storehouse_management/update/([0-9]+)/", StorehouseManagementHandler),
    url("/api/storehouse_management/delete/([0-9]+)/", StorehouseManagementHandler),

    # 库存查询
    url("/api/inventory_query/list/", InventoryQueryHandler),

    # 聚水潭库存查询
    url("/api/inventory_query/jst/([A-Za-z0-9]+)/", InventoryQueryHandler),
)
