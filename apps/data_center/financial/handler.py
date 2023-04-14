import json

from wherp.handler import RedisHandler
from apps.utils.mxform_decorators import authenticated_async
from apps.utils.util_func import json_serial
from apps.finance.accounting_subject.models import *
from apps.finance.subsidiary_ledger.models import *
from apps.utils.FindMenu import find_child
from apps.utils.date_func import getFirstAndLastDay
from apps.customer.customer_handler.models import Customer


# 现金银行
class CashBankHandler(RedisHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        re_data = {}
        data = []

        # 获取时间
        firstDay, lastDay = await getFirstAndLastDay()

        base = AccountingSubject.alias()
        cte = (base
               .select(base,
                       SubsidiaryLedger.date,
                       fn.SUM(Case(None, [((SubsidiaryLedger.date.between(firstDay, lastDay)),
                                           SubsidiaryLedger.amount)], 0)).alias('this_month_total'),
                       (fn.IFNULL(fn.SUM(SubsidiaryLedger.amount), 0) + base.initial_balance).alias('actual_amount'), )
               .join(SubsidiaryLedger, join_type=JOIN.LEFT_OUTER, on=(base.as_no == SubsidiaryLedger.as_id))
               .group_by(base.name)
               .cte('order_as'))

        query = await self.application.objects.execute(AccountingSubject
                                                       .select(AccountingSubject.id,
                                                               AccountingSubject.as_no.alias("no"),
                                                               AccountingSubject.parent_id,
                                                               AccountingSubject.name.alias("as_name"),
                                                               cte.select(fn.SUM(cte.c.this_month_total))
                                                               .where(cte.c.parent_path
                                                                      .contains(AccountingSubject.parent_path))
                                                               .alias('this_month_total'),
                                                               cte.select(fn.SUM(cte.c.actual_amount))
                                                               .where(cte.c.parent_path
                                                                      .contains(AccountingSubject.parent_path))
                                                               .alias('actual_amount'), )
                                                       .where((AccountingSubject.parent_path.contains('1/2/8/')) |
                                                              (AccountingSubject.parent_path.contains('1/2/9/')))
                                                       .join(cte, join_type=JOIN.LEFT_OUTER,
                                                             on=(AccountingSubject.as_no == cte.c.as_no))
                                                       .dicts()
                                                       .with_cte(cte))
        for item in query:
            data.append(item)
        data = await find_child(data, 2)

        re_data["data"] = data
        re_data["success"] = True
        await self.finish(json.dumps(re_data, default=json_serial))


class CashBankDetailHandler(RedisHandler):
    @authenticated_async
    async def post(self, *args, **kwargs):
        re_data = {}
        data_list = []
        param = self.request.body.decode()
        param = json.loads(param)
        expressions = []

        try:
            as_id = await self.application.objects.get(AccountingSubject, as_no=param['params']['as_no'])
            classic = await self.application.objects.execute(
                AccountingSubject.select().where(AccountingSubject.parent_path.contains(as_id.parent_path))
                    .having(AccountingSubject.id != as_id.id))
            if classic:
                pid_list = []
                for item in classic:
                    pid_list.append(item.as_no)
                expressions.append(SubsidiaryLedger.as_id.in_(pid_list))
            else:
                expressions.append(SubsidiaryLedger.as_id == as_id.as_no)

            expressions.append(SubsidiaryLedger.date.between(param['params']['startTime'],
                                                             param['params']['endTime']))

            base = (SubsidiaryLedger
                    .select(SubsidiaryLedger.id,
                            Case(None, [((SubsidiaryLedger.amount > 0), SubsidiaryLedger.amount)], 0).alias('add_amount'),
                            Case(None, [((SubsidiaryLedger.amount < 0), SubsidiaryLedger.amount)], 0).alias('sub_amount'))
                    .where(*expressions)
                    .cte('sl_account'))

            sql = (SubsidiaryLedger
                   .select(SubsidiaryLedger.order_type,
                           SubsidiaryLedger.date.alias('signed_data'),
                           SubsidiaryLedger.order_no.alias("order_no"),
                           AccountingSubject.as_no.alias("as_no"),
                           AccountingSubject.name.alias("as_name"),
                           Customer.uk_customer_no.alias("customer_no"),
                           Customer.name.alias("customer_name"),
                           base.c.add_amount.alias("add_amount"),
                           base.c.sub_amount.alias("sub_amount"),
                           fn.SUM(base.c.add_amount + base.c.sub_amount).over(order_by=[SubsidiaryLedger.id]).alias(
                               'amount'))
                   .join(base, join_type=JOIN.LEFT_OUTER, on=(base.c.id == SubsidiaryLedger.id))
                   .join(AccountingSubject, join_type=JOIN.LEFT_OUTER,
                         on=(AccountingSubject.as_no == SubsidiaryLedger.as_id))
                   .join(Customer, join_type=JOIN.LEFT_OUTER,
                         on=(Customer.id == SubsidiaryLedger.customer_id))
                   .where(*expressions)
                   .group_by(SubsidiaryLedger.id)
                   .dicts()
                   .with_cte(base))

            data = await self.application.objects.execute(sql)
            for item in data:
                data_list.append(item)

            re_data['data'] = data_list
            re_data["success"] = True

        except AccountingSubject.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '账户不存在'

        await self.finish(json.dumps(re_data, default=json_serial))


# 费用合计统计
class CostTotalStatistics(RedisHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        re_data = {}
        data = []

        # 获取时间
        firstDay, lastDay = await getFirstAndLastDay()

        base = AccountingSubject.alias()
        cte = (base
               .select(base,
                       SubsidiaryLedger.date,
                       fn.SUM(Case(None, [((SubsidiaryLedger.date.between(firstDay, lastDay)),
                                           SubsidiaryLedger.amount)], 0)).alias('this_month_total'),
                       (fn.IFNULL(fn.SUM(SubsidiaryLedger.amount), 0) + base.initial_balance).alias('actual_amount'), )
               .join(SubsidiaryLedger, join_type=JOIN.LEFT_OUTER, on=(base.as_no == SubsidiaryLedger.as_id))
               .group_by(base.name)
               .cte('order_as'))

        query = await self.application.objects.execute(AccountingSubject
                                                       .select(AccountingSubject.id,
                                                               AccountingSubject.as_no.alias("no"),
                                                               AccountingSubject.parent_id,
                                                               AccountingSubject.name.alias("as_name"),
                                                               cte.select(fn.SUM(cte.c.this_month_total))
                                                               .where(cte.c.parent_path
                                                                      .contains(AccountingSubject.parent_path))
                                                               .alias('this_month_total'),
                                                               cte.select(fn.SUM(cte.c.actual_amount))
                                                               .where(cte.c.parent_path
                                                                      .contains(AccountingSubject.parent_path))
                                                               .alias('actual_amount'), )
                                                       .where((AccountingSubject.parent_path.contains('1/5/15/')))
                                                       .join(cte, join_type=JOIN.LEFT_OUTER,
                                                             on=(AccountingSubject.as_no == cte.c.as_no))
                                                       .dicts()
                                                       .with_cte(cte))
        for item in query:
            data.append(item)
        data = await find_child(data, 5)

        re_data["data"] = data
        re_data["success"] = True
        await self.finish(json.dumps(re_data, default=json_serial))
