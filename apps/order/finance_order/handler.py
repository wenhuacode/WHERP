import json

from wherp.handler import RedisHandler
from apps.utils.mxform_decorators import authenticated_async
from apps.order.models.models import OrderIndex, OrderDetail, SubsidiaryLedger
from apps.order.finance_order.forms import FinanceOrderForms
from apps.finance.accounting_subject.models import AccountingSubject
from wherp.settings import database
from playhouse.shortcuts import model_to_dict


# 创建财务单
class CreateFinanceOrderHandler(RedisHandler):
    @authenticated_async
    async def post(self, *args, **kwargs):
        re_data = {}
        param = self.request.body.decode('utf-8')
        param = json.loads(param)
        form = FinanceOrderForms.from_json(param)
        if form.validate():
            try:
                await self.application.objects.get(OrderIndex, order_no=form.order_no.data)
                re_data["success"] = False
                re_data["errorMessage"] = '订单编号重复'
            except OrderIndex.DoesNotExist as e:
                # 事务 批量保存订单详情
                async with database.atomic_async():
                    await self.application.objects.create(OrderIndex,
                                                          order_no=form.order_no.data,
                                                          order_type=form.order_type.data,
                                                          customer_id=form.customer_id.data,
                                                          employee_id=form.employee_id.data,
                                                          signed_data=form.signed_data.data,
                                                          order_amount=form.order_amount.data,
                                                          note=form.note.data,
                                                          bank_account=form.bank_account.data,
                                                          rp_amount=form.rp_amount.data,
                                                          create_user_id=self.current_user.id)
                    await self.application.objects.execute(OrderDetail.insert_many(form.table.data))
                re_data["success"] = True
                re_data["errorMessage"] = '创建成功'

        else:
            for field in form.errors:
                re_data["errorMessage"] = form.errors[field][0]
        await self.finish(re_data)


# 红冲财务单
class UnFinanceOrderHandler(RedisHandler):
    @authenticated_async
    async def get(self, order_no, *args, **kwargs):
        re_data = {}
        try:
            order = await self.application.objects.get(OrderIndex, order_no=str(order_no))
            order_detail = await self.application.objects.execute(SubsidiaryLedger.select()
                                                                  .where(SubsidiaryLedger.order_no == str(order_no)))
            if order.order_state == 2:
                order.order_state = 3
                sl = SubsidiaryLedger()
                sl_list = []
                async with database.transaction_async() as txn:
                    for data in order_detail:
                        sl.order_type = order.order_type
                        sl.date = data.date
                        sl.order_no = data.order_no
                        sl.employee_id = data.employee_id
                        sl.as_id = data.as_id
                        sl.customer_id = data.customer_id
                        sl.amount = -data.amount
                        sl.note = data.note
                        sl.create_user_id = data.create_user_id

                        sl_list.append(model_to_dict(sl))
                    await self.application.objects.execute(SubsidiaryLedger.insert_many(sl_list))
                    # 更新原有单据状态
                    await self.application.objects.update(order)
                    re_data["success"] = True
                    re_data["errorMessage"] = '审核成功'

        except OrderIndex.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '订单不存在'
        except Exception as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = f'发生其他错误: {e}'

        await self.finish(re_data)


# 审核收款单
class CheckReceiptOrderHandler(RedisHandler):
    @authenticated_async
    async def get(self, order_no, *args, **kwargs):
        re_data = {}
        try:
            order = await self.application.objects.get(OrderIndex, order_no=str(order_no))
            order_detail = await self.application.objects.execute(OrderDetail.select()
                                                                  .where(OrderDetail.order_no == str(order_no)))
            if order.order_state == 1:
                async with database.transaction_async() as txn:
                    order.order_state = 2
                    order.checked_user = self.current_user.id
                    sl = SubsidiaryLedger()
                    sl_list = []
                    for data in order_detail:
                        sl.order_type = order.order_type
                        sl.date = order.signed_data
                        sl.order_no = order.order_no
                        sl.employee_id = order.employee_id
                        sl.as_id = data.barcode
                        sl.customer_id = order.customer_id
                        sl.amount = data.discount_total
                        sl.note = data.note
                        sl.create_user_id = order.create_user_id

                        sl_list.append(model_to_dict(sl))
                    # 应收减少
                    await self.application.objects.create(SubsidiaryLedger,
                                                          order_type=order.order_type,
                                                          date=order.signed_data,
                                                          order_no=order.order_no,
                                                          employee_id=order.employee_id,
                                                          as_id=str('0105'),
                                                          customer_id=order.customer_id,
                                                          amount=-order.order_amount,
                                                          note=order.note,
                                                          create_user_id=order.create_user_id)
                    await self.application.objects.execute(SubsidiaryLedger.insert_many(sl_list))
                    # 更新原有单据状态
                    await self.application.objects.update(order)
                    re_data["success"] = True
                    re_data["errorMessage"] = '审核成功'

        except OrderIndex.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '订单不存在'
        except Exception as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = f'发生其他错误: {e}'

        await self.finish(re_data)


# 审核付款单
class CheckPaymentOrderHandler(RedisHandler):
    @authenticated_async
    async def get(self, order_no, *args, **kwargs):
        re_data = {}
        try:
            order = await self.application.objects.get(OrderIndex, order_no=str(order_no))
            order_detail = await self.application.objects.execute(OrderDetail.select()
                                                                  .where(OrderDetail.order_no == str(order_no)))
            if order.order_state == 1:
                async with database.transaction_async() as txn:
                    order.order_state = 2
                    order.checked_user = self.current_user.id
                    sl = SubsidiaryLedger()
                    sl_list = []
                    for data in order_detail:
                        sl.order_type = order.order_type
                        sl.date = order.signed_data
                        sl.order_no = order.order_no
                        sl.employee_id = order.employee_id
                        sl.as_id = data.barcode
                        sl.customer_id = order.customer_id
                        sl.amount = -data.discount_total
                        sl.note = data.note
                        sl.create_user_id = order.create_user_id

                        sl_list.append(model_to_dict(sl))
                    # 应付款合计减少
                    await self.application.objects.create(SubsidiaryLedger,
                                                          order_type=order.order_type,
                                                          date=order.signed_data,
                                                          order_no=order.order_no,
                                                          employee_id=order.employee_id,
                                                          as_id=str('0201'),
                                                          customer_id=order.customer_id,
                                                          amount=-order.order_amount,
                                                          note=order.note,
                                                          create_user_id=order.create_user_id)
                    await self.application.objects.execute(SubsidiaryLedger.insert_many(sl_list))
                    # 更新原有单据状态
                    await self.application.objects.update(order)
                    re_data["success"] = True
                    re_data["errorMessage"] = '审核成功'

        except OrderIndex.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '订单不存在'
        except Exception as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = f'发生其他错误: {e}'

        await self.finish(re_data)


# 审核一般费用单
class CheckGeneralCostOrderHandler(RedisHandler):
    @authenticated_async
    async def get(self, order_no, *args, **kwargs):
        re_data = {}
        try:
            order = await self.application.objects.get(OrderIndex, order_no=str(order_no))
            order_detail = await self.application.objects.execute(OrderDetail.select()
                                                                  .where(OrderDetail.order_no == str(order_no)))
            # 银行科目减少, 查询银行科目
            as_bank_id = await self.application.objects.get(AccountingSubject, id=int(order.bank_account))
            if order.order_state == 1:
                async with database.transaction_async() as txn:
                    order.order_state = 2
                    order.checked_user = self.current_user.id
                    sl = SubsidiaryLedger()
                    sl_list = []
                    for data in order_detail:
                        sl.order_type = order.order_type
                        sl.date = order.signed_data
                        sl.order_no = order.order_no
                        sl.employee_id = order.employee_id
                        sl.as_id = data.barcode
                        sl.customer_id = order.customer_id
                        sl.amount = data.discount_total
                        sl.note = data.note
                        sl.create_user_id = order.create_user_id

                        sl_list.append(model_to_dict(sl))
                    await self.application.objects.create(SubsidiaryLedger,
                                                          order_type=order.order_type,
                                                          date=order.signed_data,
                                                          order_no=order.order_no,
                                                          customer_id=order.customer_id,
                                                          employee_id=order.employee_id,
                                                          as_id=as_bank_id.as_no,
                                                          amount=-order.rp_amount,
                                                          note=order.note,
                                                          create_user_id=order.create_user_id)

                    if order.customer_id is not None:
                        # 客户应付款金额减少
                        await self.application.objects.create(SubsidiaryLedger,
                                                              order_no=order.order_no,
                                                              date=order.signed_data,
                                                              order_type=order.order_type,
                                                              customer_id=order.customer_id,
                                                              employee_id=order.employee_id,
                                                              as_id=str('0201'),
                                                              amount=-order.order_amount,
                                                              note=order.note,
                                                              create_user_id=order.create_user_id)
                    await self.application.objects.execute(SubsidiaryLedger.insert_many(sl_list))
                    # 更新原有单据状态
                    await self.application.objects.update(order)
                    re_data["success"] = True
                    re_data["errorMessage"] = '审核成功'

        except OrderIndex.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '订单不存在'
        except AccountingSubject as e:
            re_data["success"] = False
            re_data["errorMessage"] = '银行科目不存在'
        except Exception as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = f'发生其他错误: {e}'

        await self.finish(re_data)


# 审核应收增加单
class CheckARAdIncreaseOrderHandler(RedisHandler):
    @authenticated_async
    async def get(self, order_no, *args, **kwargs):
        re_data = {}
        try:
            order = await self.application.objects.get(OrderIndex, order_no=str(order_no))
            order_detail = await self.application.objects.execute(OrderDetail.select()
                                                                  .where(OrderDetail.order_no == str(order_no)))
            if order.order_state == 1:
                async with database.transaction_async() as txn:
                    order.order_state = 2
                    order.checked_user = self.current_user.id
                    sl = SubsidiaryLedger()
                    sl_list = []
                    for data in order_detail:
                        sl.order_type = order.order_type
                        sl.date = order.signed_data
                        sl.order_no = order.order_no
                        sl.employee_id = order.employee_id
                        sl.as_id = data.barcode
                        sl.customer_id = order.customer_id
                        sl.amount = data.discount_total
                        sl.note = data.note
                        sl.create_user_id = order.create_user_id

                        sl_list.append(model_to_dict(sl))
                    # 应收增加
                    await self.application.objects.create(SubsidiaryLedger,
                                                          order_type=order.order_type,
                                                          date=order.signed_data,
                                                          order_no=order.order_no,
                                                          customer_id=order.customer_id,
                                                          employee_id=order.employee_id,
                                                          as_id=str('0105'),
                                                          amount=order.order_amount,
                                                          note=order.note,
                                                          create_user_id=order.create_user_id)
                    await self.application.objects.execute(SubsidiaryLedger.insert_many(sl_list))
                    # 更新原有单据状态
                    await self.application.objects.update(order)
                    re_data["success"] = True
                    re_data["errorMessage"] = '审核成功'

        except OrderIndex.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '订单不存在'
        except Exception as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = f'发生其他错误: {e}'

        await self.finish(re_data)


# 审核应收减少单
class CheckARAdDecreaseOrderHandler(RedisHandler):
    @authenticated_async
    async def get(self, order_no, *args, **kwargs):
        re_data = {}
        try:
            order = await self.application.objects.get(OrderIndex, order_no=str(order_no))
            order_detail = await self.application.objects.execute(OrderDetail.select()
                                                                  .where(OrderDetail.order_no == str(order_no)))
            if order.order_state == 1:
                async with database.transaction_async() as txn:
                    order.order_state = 2
                    order.checked_user = self.current_user.id
                    sl = SubsidiaryLedger()
                    sl_list = []
                    for data in order_detail:
                        sl.order_type = order.order_type
                        sl.date = order.signed_data
                        sl.order_no = order.order_no
                        sl.employee_id = order.employee_id
                        sl.as_id = data.barcode
                        sl.customer_id = order.customer_id
                        sl.amount = data.discount_total
                        sl.note = data.note
                        sl.create_user_id = order.create_user_id

                        sl_list.append(model_to_dict(sl))
                    # 应收减少
                    await self.application.objects.create(SubsidiaryLedger,
                                                          order_type=order.order_type,
                                                          date=order.signed_data,
                                                          order_no=order.order_no,
                                                          customer_id=order.customer_id,
                                                          employee_id=order.employee_id,
                                                          as_id=str('0105'),
                                                          amount=-order.order_amount,
                                                          note=order.note,
                                                          create_user_id=order.create_user_id)
                    await self.application.objects.execute(SubsidiaryLedger.insert_many(sl_list))
                    # 更新原有单据状态
                    await self.application.objects.update(order)
                    re_data["success"] = True
                    re_data["errorMessage"] = '审核成功'

        except OrderIndex.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '订单不存在'
        except Exception as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = f'发生其他错误: {e}'

        await self.finish(re_data)


# 审核应付增加单
class CheckAPAdIncreaseOrderHandler(RedisHandler):
    @authenticated_async
    async def get(self, order_no, *args, **kwargs):
        re_data = {}
        try:
            order = await self.application.objects.get(OrderIndex, order_no=str(order_no))
            order_detail = await self.application.objects.execute(OrderDetail.select()
                                                                  .where(OrderDetail.order_no == str(order_no)))
            if order.order_state == 1:
                async with database.transaction_async() as txn:
                    order.order_state = 2
                    order.checked_user = self.current_user.id
                    sl = SubsidiaryLedger()
                    sl_list = []
                    for data in order_detail:
                        sl.order_type = order.order_type
                        sl.date = order.signed_data
                        sl.order_no = order.order_no
                        sl.employee_id = order.employee_id
                        sl.as_id = data.barcode
                        sl.customer_id = order.customer_id
                        sl.amount = data.discount_total
                        sl.note = data.note
                        sl.create_user_id = order.create_user_id

                        sl_list.append(model_to_dict(sl))
                    # 应付增加
                    await self.application.objects.create(SubsidiaryLedger,
                                                          order_type=order.order_type,
                                                          date=order.signed_data,
                                                          order_no=order.order_no,
                                                          customer_id=order.customer_id,
                                                          employee_id=order.employee_id,
                                                          as_id=str('0201'),
                                                          amount=order.order_amount,
                                                          note=order.note,
                                                          create_user_id=order.create_user_id)
                    await self.application.objects.execute(SubsidiaryLedger.insert_many(sl_list))
                    # 更新原有单据状态
                    await self.application.objects.update(order)
                    re_data["success"] = True
                    re_data["errorMessage"] = '审核成功'

        except OrderIndex.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '订单不存在'
        except Exception as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = f'发生其他错误: {e}'

        await self.finish(re_data)


# 审核应付减少单
class CheckAPAdDecreaseOrderHandler(RedisHandler):
    @authenticated_async
    async def get(self, order_no, *args, **kwargs):
        re_data = {}
        try:
            order = await self.application.objects.get(OrderIndex, order_no=str(order_no))
            order_detail = await self.application.objects.execute(OrderDetail.select()
                                                                  .where(OrderDetail.order_no == str(order_no)))
            if order.order_state == 1:
                async with database.transaction_async() as txn:
                    order.order_state = 2
                    order.checked_user = self.current_user.id
                    sl = SubsidiaryLedger()
                    sl_list = []
                    for data in order_detail:
                        sl.order_type = order.order_type
                        sl.date = order.signed_data
                        sl.order_no = order.order_no
                        sl.employee_id = order.employee_id
                        sl.as_id = data.barcode
                        sl.customer_id = order.customer_id
                        sl.amount = data.discount_total
                        sl.note = data.note
                        sl.create_user_id = order.create_user_id

                        sl_list.append(model_to_dict(sl))
                    # 应付减少
                    await self.application.objects.create(SubsidiaryLedger,
                                                          order_type=order.order_type,
                                                          date=order.signed_data,
                                                          order_no=order.order_no,
                                                          customer_id=order.customer_id,
                                                          employee_id=order.employee_id,
                                                          as_id=str('0201'),
                                                          amount=-order.order_amount,
                                                          note=order.note,
                                                          create_user_id=order.create_user_id)
                    await self.application.objects.execute(SubsidiaryLedger.insert_many(sl_list))
                    # 更新原有单据状态
                    await self.application.objects.update(order)
                    re_data["success"] = True
                    re_data["errorMessage"] = '审核成功'

        except OrderIndex.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '订单不存在'
        except Exception as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = f'发生其他错误: {e}'

        await self.finish(re_data)


# 审核提现存现转账单
class CheckCapitalAdjustOrderHandler(RedisHandler):
    @authenticated_async
    async def get(self, order_no, *args, **kwargs):
        re_data = {}
        try:
            order = await self.application.objects.get(OrderIndex, order_no=str(order_no))
            order_detail = await self.application.objects.execute(OrderDetail.select()
                                                                  .where(OrderDetail.order_no == str(order_no)))
            # 银行科目减少, 查询银行科目
            as_bank_id = await self.application.objects.get(AccountingSubject, id=int(order.bank_account))
            if order.order_state == 1:

                async with database.transaction_async() as txn:
                    order.order_state = 2
                    order.checked_user = self.current_user.id
                    sl = SubsidiaryLedger()
                    sl_list = []
                    for data in order_detail:
                        sl.order_type = order.order_type
                        sl.date = order.signed_data
                        sl.order_no = order.order_no
                        sl.employee_id = order.employee_id
                        sl.as_id = data.barcode
                        sl.customer_id = order.customer_id
                        sl.amount = data.discount_total
                        sl.note = data.note
                        sl.create_user_id = order.create_user_id

                        sl_list.append(model_to_dict(sl))
                    # 账户资金减少
                    await self.application.objects.create(SubsidiaryLedger,
                                                          order_type=order.order_type,
                                                          date=order.signed_data,
                                                          order_no=order.order_no,
                                                          customer_id=order.customer_id,
                                                          employee_id=order.employee_id,
                                                          as_id=as_bank_id.as_no,
                                                          amount=-order.rp_amount,
                                                          note=order.note,
                                                          create_user_id=order.create_user_id)
                    await self.application.objects.execute(SubsidiaryLedger.insert_many(sl_list))
                    # 更新原有单据状态
                    await self.application.objects.update(order)
                    re_data["success"] = True
                    re_data["errorMessage"] = '审核成功'

        except OrderIndex.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '订单不存在'
        except Exception as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = f'发生其他错误: {e}'

        await self.finish(re_data)
