from tornado.web import url
from apps.order.inventort_order.handler import *

urlpattern = (
    url("/api/inventory_order/create/", InventoryOrderHandler),

    # 审核 红冲报损单
    url("/api/order/check_goods_loss_order/([A-Za-z0-9]+)/", CheckGoodsLossOrderHandler),
    url("/api/order/un_goods_loss_order/([A-Za-z0-9]+)/", UnGoodsLossOrderHandler),

    # 审核 红冲报溢单
    url("/api/order/check_goods_overflow_order/([A-Za-z0-9]+)/", CheckGoodsOverflowOrderHandler),
    url("/api/order/un_goods_overflow_order/([A-Za-z0-9]+)/", UnGoodsOverflowOrderHandler),

    # 审核 红冲其他出库单
    url("/api/order/check_other_out_order/([A-Za-z0-9]+)/", CheckOtherOutOrderHandler),
    url("/api/order/un_other_out_order/([A-Za-z0-9]+)/", UnOtherOutOrderHandler),

    # 审核 红冲其他入库单
    url("/api/order/check_other_put_in_order/([A-Za-z0-9]+)/", CheckOtherPutInOrderHandler),
    url("/api/order/un_other_put_in_order/([A-Za-z0-9]+)/", UnOtherPutInOrderHandler),

    # 审核 红冲调拨单
    url("/api/order/check_transfers_order/([A-Za-z0-9]+)/", CheckTransfersOrderHandler),
    url("/api/order/un_transfers_order/([A-Za-z0-9]+)/", UnTransfersOrderHandler),

    # 审核 成本调价单
    url("/api/order/check_cost_adjust_order/([A-Za-z0-9]+)/", CheckCostAdjustOrderHandler),
    url("/api/order/un_cost_adjust_order/([A-Za-z0-9]+)/", unCostAdjustOrderHandler),

)