from tornado.web import url
from apps.product.product_handler.handler import *

urlpattern = (
    # 产品分类
    url("/api/productclassify/list/", ProductClassifyHandler),
    url("/api/productclassify/create/", ProductClassifyHandler),
    url("/api/productclassify/update/", ProductClassifyHandler),
    url("/api/productclassify/delete/([0-9]+)/", ProductClassifyHandler),

    # 产品详情
    url("/api/product/list/", ProductHandler),
    url("/api/product/create/", ProductHandler),
    url("/api/product/update/([0-9]+)/", ProductHandler),
    url("/api/product/delete/([0-9]+)/", ProductHandler),
    url("/api/product/getproductimage/", GetProductImage),

    # 产品库存
    url("/api/product/query/", ProductQueryHandler),

    # 导入导出
    url("/api/product/import/", ImportAndExportProductHandler),
    url("/api/product/export/", ImportAndExportProductHandler),

    # 批量更新产品分类
    url("/api/product/batch/productclassify/", BatchUpdateEditProductHandler),
)
