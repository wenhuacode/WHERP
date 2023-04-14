import json
from datetime import datetime

from playhouse.shortcuts import model_to_dict

from wherp.handler import RedisHandler
from wherp.settings import database
from apps.utils.mxform_decorators import authenticated_async
from apps.finance.accounting_subject.models import *
from apps.finance.accounting_subject.forms import *
from apps.finance.subsidiary_ledger.models import *
from apps.utils.FindMenu import find_menu, find_menu_child
from apps.utils.util_func import json_serial


class CostStatisticsHandler(RedisHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        re_data = {}
        datas = []

        order_as = AccountingSubject.alias()
        cte = (order_as
               .select(order_as, fn.SUM((SubsidiaryLedger.add_amount - SubsidiaryLedger.sub_amount)).alias('total'))
               .join(SubsidiaryLedger, join_type=JOIN.LEFT_OUTER, on=(order_as.id == SubsidiaryLedger.as_id))
               .group_by(order_as.name).cte('order_as'))

        order_as2 = AccountingSubject.alias()
        cte2 = (order_as2
                .select(order_as2, fn.SUM(order_as2.initial_balance + cte.c.total)
                        .alias('actual_amount'))
                .join(cte, join_type=JOIN.LEFT_OUTER, on=(order_as2.id == cte.c.id))
                .group_by(order_as2.id, order_as2.name).cte('as_tree_amount'))

        query = await self.application.objects.execute(AccountingSubject
                                                       .select(AccountingSubject,
                                                               cte2.select(fn.SUM(cte2.c.actual_amount))
                                                               .where(cte2.c.parent_path
                                                                      .contains(AccountingSubject.parent_path))
                                                               .alias('actual_amount'))
                                                       .where(AccountingSubject.parent_path.contains('1/5/15/'))
                                                       .join(cte2, join_type=JOIN.LEFT_OUTER,
                                                             on=(AccountingSubject.id == cte2.c.id))
                                                       .with_cte(cte, cte2))
        for item in query:
            data = model_to_dict(item)
            data['actual_amount'] = item.actual_amount
            datas.append(data)
        datas = await find_menu_child(datas, 5)

        re_data["data"] = datas
        re_data["success"] = True
        await self.finish(json.dumps(re_data, default=json_serial))


class CashBankHandler(RedisHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        re_data = {}
        datas = []

        order_as = AccountingSubject.alias()
        cte = (order_as
               .select(order_as, fn.SUM((SubsidiaryLedger.add_amount - SubsidiaryLedger.sub_amount)).alias('total'))
               .join(SubsidiaryLedger, join_type=JOIN.LEFT_OUTER, on=(order_as.id == SubsidiaryLedger.as_id))
               .group_by(order_as.name).cte('order_as'))

        order_as2 = AccountingSubject.alias()
        cte2 = (order_as2
                .select(order_as2, fn.SUM(order_as2.initial_balance + cte.c.total)
                        .alias('actual_amount'))
                .join(cte, join_type=JOIN.LEFT_OUTER, on=(order_as2.id == cte.c.id))
                .group_by(order_as2.id, order_as2.name).cte('as_tree_amount'))

        query = await self.application.objects.execute(AccountingSubject
                                                       .select(AccountingSubject,
                                                               cte2.select(fn.SUM(cte2.c.actual_amount))
                                                               .where(cte2.c.parent_path
                                                                      .contains(AccountingSubject.parent_path))
                                                               .alias('actual_amount'))
                                                       .where(AccountingSubject.parent_path.contains('1/2/'))
                                                       .join(cte2, join_type=JOIN.LEFT_OUTER,
                                                             on=(AccountingSubject.id == cte2.c.id))
                                                       .with_cte(cte, cte2))
        for item in query:
            data = model_to_dict(item)
            data['actual_amount'] = item.actual_amount
            datas.append(data)
        datas = await find_menu_child(datas, 1)

        re_data["data"] = datas
        re_data["success"] = True
        await self.finish(json.dumps(re_data, default=json_serial))


class AccountingSubjectHandler(RedisHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        re_data = {}
        data = []
        accounting_subjects = await self.application.objects.execute(AccountingSubject.select())
        for item in accounting_subjects:
            data.append(model_to_dict(item))
        data = await find_menu(data)

        re_data["data"] = data
        re_data["success"] = True
        await self.finish(json.dumps(re_data, default=json_serial))

    @authenticated_async
    async def post(self, *args, **kwargs):
        re_data = {}
        param = self.request.body.decode("utf8")
        param = json.loads(param)
        form = CreateAccountingSubjectForm.from_json(param)
        if form.validate():
            try:
                await self.application.objects.get(AccountingSubject, as_no=str(form.as_no.data))
                re_data["success"] = False
                re_data["errorMessage"] = '科目编号重复'
            except AccountingSubject.DoesNotExist as e:
                if form.parent_id.data != 0:
                    try:
                        pi_path = await self.application.objects.get(AccountingSubject, id=form.parent_id.data)
                        async with database.atomic_async():
                            accounting_subject = await self.application.objects.create(AccountingSubject,
                                                                                       as_no=form.as_no.data,
                                                                                       name=form.name.data,
                                                                                       parent_id=form.parent_id.data,
                                                                                       level=form.level.data,
                                                                                       status=form.status.data,
                                                                                       order_num=form.order_num.data,
                                                                                       initial_balance=form.initial_balance.data,
                                                                                       create_user_id=self.current_user.id,
                                                                                       create_user=self.current_user.name)
                            accounting_subject.parent_path = str(pi_path.parent_path) + str(accounting_subject.id) + '/'
                            await self.application.objects.update(accounting_subject)
                    except AccountingSubject.DoesNotExist as e:
                        re_data["success"] = False
                        re_data["errorMessage"] = '上级目录不存在'
                else:
                    async with database.atomic_async():
                        accounting_subject = await self.application.objects.create(AccountingSubject,
                                                                                   as_no=form.as_no.data,
                                                                                   name=form.name.data,
                                                                                   parent_id=form.parent_id.data,
                                                                                   level=form.level.data,
                                                                                   status=form.status.data,
                                                                                   order_num=form.order_num.data,
                                                                                   initial_balance=form.initial_balance.data,
                                                                                   create_user_id=self.current_user.id,
                                                                                   create_user=self.current_user.name)
                        accounting_subject.parent_path = str(accounting_subject.id) + '/'
                        await self.application.objects.update(accounting_subject)
                re_data["success"] = True
                re_data["errorMessage"] = '科目新建成功'
        else:
            for field in form.errors:
                re_data["errorMessage"] = form.errors[field][0]
        await self.finish(re_data)

    @authenticated_async
    async def patch(self, *args, **kwargs):
        re_data = {}
        param = self.request.body.decode("utf8")
        param = json.loads(param)
        form = UpdateAccountingSubjectForm.from_json(param)
        if form.validate():
            try:
                accounting_subject = await self.application.objects.get(AccountingSubject, id=int(form.id.data))
                accounting_subject.as_no = form.as_no.data
                accounting_subject.name = form.name.data
                accounting_subject.status = form.status.data
                accounting_subject.order_num = form.order_num.data
                accounting_subject.initial_balance = form.initial_balance.data

                await self.application.objects.update(accounting_subject)
                re_data["success"] = True
                re_data["errorMessage"] = '科目更新成功'

            except AccountingSubject.DoesNotExist as e:
                re_data["success"] = False
                re_data["errorMessage"] = '科目不存在'
        else:
            for field in form.errors:
                re_data["errorMessage"] = form.errors[field][0]
        await self.finish(re_data)
