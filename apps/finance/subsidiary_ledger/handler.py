import copy
import json
from datetime import datetime

from playhouse.shortcuts import model_to_dict

from wherp.handler import RedisHandler
from apps.utils.mxform_decorators import authenticated_async
from apps.finance.subsidiary_ledger.models import *
from apps.finance.accounting_subject.models import *
from apps.utils.FindMenu import find_menu
from apps.utils.util_func import json_serial


class GETSubsidiaryLedgerHandler(RedisHandler):
    @authenticated_async
    async def get(self,  *args, **kwargs):
        re_data = {}
        datas = []
        start_amount = 0

        as_id = self.get_argument('id', None)
        startDate = self.get_argument('startDate', None)
        endDate = self.get_argument('endDate', None)

        initial_amount = await self.application.objects.get(AccountingSubject, id=int(as_id))
        start_date_amount = await self.application.objects.execute(SubsidiaryLedger
                                                                   .select(SubsidiaryLedger,
                                                                           fn.SUM(SubsidiaryLedger.add_amount -
                                                                                  SubsidiaryLedger.sub_amount
                                                                                  ).alias('total'))
                                                                   .group_by(SubsidiaryLedger.as_id)
                                                                   .where(SubsidiaryLedger.as_id == int(as_id),
                                                                          SubsidiaryLedger.date < startDate))
        for item in start_date_amount:
            start_amount = item.total

        Latest = SubsidiaryLedger.alias()
        cte = (Latest
               .select(Latest, fn.SUM(Latest.add_amount - Latest.sub_amount)
                       .over(order_by=[Latest.id])
                       .alias('initial_total'))
               .where(Latest.as_id == int(as_id), (Latest.date >= startDate) & (Latest.date <= endDate))
               .cte('latest'))

        query = (SubsidiaryLedger
                 .select(SubsidiaryLedger.id,
                         SubsidiaryLedger.order_type,
                         SubsidiaryLedger.order_no,
                         SubsidiaryLedger.as_name,
                         SubsidiaryLedger.date,
                         SubsidiaryLedger.add_amount,
                         SubsidiaryLedger.sub_amount,
                         SubsidiaryLedger.create_user,
                         cte.c.initial_total,
                         (cte.c.initial_total + initial_amount.initial_balance + start_amount).alias('total'))
                 .join(cte, join_type=JOIN.RIGHT_OUTER, on=(SubsidiaryLedger.id == cte.c.id))
                 .order_by(SubsidiaryLedger.add_time)
                 .with_cte(cte))

        subsidiary_ledger = await self.application.objects.execute(query)
        for item in subsidiary_ledger:
            data = model_to_dict(item)
            data['total'] = item.total
            datas.append(copy.deepcopy(data))

        re_data["before_balance"] = start_amount
        re_data["data"] = datas
        re_data["success"] = True

        await self.finish(json.dumps(re_data, default=json_serial))


class SubsidiaryLedgerHandler(RedisHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        re_data = {}
        datas = []
        query = SubsidiaryLedger.select(SubsidiaryLedger,
                                        fn.SUM(SubsidiaryLedger.amount)
                                        .over(order_by=[SubsidiaryLedger.id]).alias('total'))

        subsidiary_ledger = await self.application.objects.execute(query)
        for item in subsidiary_ledger:
            data = model_to_dict(item)
            data['total'] = item.total
            datas.append(copy.deepcopy(data))

        re_data["data"] = datas
        re_data["success"] = True
        await self.finish(json.dumps(re_data, default=json_serial))
