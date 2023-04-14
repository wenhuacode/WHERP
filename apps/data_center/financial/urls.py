from tornado.web import url
from apps.data_center.financial.handler import *


urlpattern = (
    url("/api/data_center/financial/cash_bank/", CashBankHandler),
    url("/api/data_center/financial/cash_bank_detail/", CashBankDetailHandler),

    url("/api/data_center/financial/cost_total_statistics/", CostTotalStatistics),
)