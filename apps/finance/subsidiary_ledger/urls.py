from tornado.web import url
from apps.finance.subsidiary_ledger.handler import *

urlpattern = (
    url("/api/finance/subsidiary_ledger/list/", SubsidiaryLedgerHandler),
    url("/api/finance/subsidiary_ledger/cash_bank/list/", GETSubsidiaryLedgerHandler),
)