from tornado.web import url
from apps.finance.accounting_subject.handler import *

urlpattern = (
    url("/api/finance/accounting_subject/list/", AccountingSubjectHandler),
    url("/api/finance/accounting_subject/create/", AccountingSubjectHandler),
    url("/api/finance/accounting_subject/update/", AccountingSubjectHandler),

    url("/api/finance/accounting_subject/cash_bank/", CashBankHandler),
    url("/api/finance/accounting_subject/cost_statistics/", CostStatisticsHandler),
)