from tornado.web import url
from apps.order.finance_order.handler import *


urlpattern = (
    url("/api/order/finance_order/create/", CreateFinanceOrderHandler),

    # 审核 收款单 11
    url("/api/order/check_receipt_order/([A-Za-z0-9]+)/", CheckReceiptOrderHandler),
    url("/api/order/un_finance_order/([A-Za-z0-9]+)/", UnFinanceOrderHandler),

    # 审核 付款单 12
    url("/api/order/check_payment_order/([A-Za-z0-9]+)/", CheckPaymentOrderHandler),

    # 审核 一般费用单 13
    url("/api/order/check_general_cost_order/([A-Za-z0-9]+)/", CheckGeneralCostOrderHandler),

    # 审核 应收增加单 14
    url("/api/order/check_arad_increase_order/([A-Za-z0-9]+)/", CheckARAdIncreaseOrderHandler),

    # 审核 应收减少单 15
    url("/api/order/check_arad_decrease_order/([A-Za-z0-9]+)/", CheckARAdDecreaseOrderHandler),

    # 审核 应付增加单 16
    url("/api/order/check_apad_increase_order/([A-Za-z0-9]+)/", CheckAPAdIncreaseOrderHandler),

    # 审核 应付减少单 17
    url("/api/order/check_apad_decrease_order/([A-Za-z0-9]+)/", CheckAPAdDecreaseOrderHandler),

    # 审核 资金调整单 18
    url("/api/order/check_capital_adjust_order/([A-Za-z0-9]+)/", CheckCapitalAdjustOrderHandler),
)
