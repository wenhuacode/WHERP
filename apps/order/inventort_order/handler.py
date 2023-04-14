import json

from wherp.handler import RedisHandler
from wherp.settings import database
from apps.utils.mxform_decorators import authenticated_async
from apps.order.models.models import OrderIndex, OrderDetail, OrderDetailAccount
from apps.order.inventort_order.forms import CreateInventoryOrderForm
from apps.utils.OutInventoryCheck import OutInventoryCheck
from apps.utils.AccountingSubjectInsert import AccountingSubjectInsert



# 新建库存操作类订单
class InventoryOrderHandler(RedisHandler):
    @authenticated_async
    async def post(self, *args, **kwargs):
        re_data = {}
        param = self.request.body.decode('utf-8')
        param = json.loads(param)
        form = CreateInventoryOrderForm.from_json(param)
        if form.validate():
            try:
                await self.application.objects.get(OrderIndex, order_no=form.order_no.data)
                re_data["success"] = False
                re_data["errorMessage"] = '订单编号重复'
            except OrderIndex.DoesNotExist as e:
                # 事务 批量保存订单详情
                async with database.atomic_async() as txn:
                    await self.application.objects.create(OrderIndex,
                                                          order_no=form.order_no.data,
                                                          order_type=form.order_type.data,
                                                          storehouse_id=form.storehouse_id.data,
                                                          rs_storehouse=form.rs_storehouse.data,
                                                          employee_id=form.employee_id.data,
                                                          signed_data=form.signed_data.data,
                                                          is_push_jst=form.is_push_jst.data,
                                                          order_qty=form.order_qty.data,
                                                          total_sales_amount=form.total_sales_amount.data,
                                                          order_discount=form.order_discount.data,
                                                          express_fee=form.express_fee.data,
                                                          discount_amount=form.discount_amount.data,
                                                          order_amount=form.order_amount.data,
                                                          note=form.note.data,
                                                          create_user_id=self.current_user.id)
                    await self.application.objects.execute(OrderDetail.insert_many(form.table.data))
                re_data["success"] = True
                re_data["errorMessage"] = '创建成功'

        else:
            for field in form.errors:
                re_data["errorMessage"] = form.errors[field][0]
        await self.finish(re_data)


# 红冲报溢单
class UnGoodsOverflowOrderHandler(RedisHandler):
    @authenticated_async
    async def get(self, order_no, *args, **kwargs):
        # 红冲采购订单
        re_data = {}
        try:
            order = await self.application.objects.get(OrderIndex, order_no=str(order_no))
            order_detail = await self.application.objects.execute(OrderDetailAccount.select()
                                                                  .where(OrderDetailAccount.order_no == str(order_no)))
            if order.order_state == 2:
                async with database.transaction_async() as txn:
                    # 处理库存及成本
                    re_data = await OutInventoryCheck(
                        order, order_detail, self.current_user.id).un_in_check_order(
                        txn=txn, re_data=re_data)
                    if re_data["success"]:
                        # 插入科目账本
                        await AccountingSubjectInsert(
                            order=order, current_user_id=self.current_user.id).un_sale_order_check(
                            txn=txn, re_data=re_data)
                        re_data["success"] = True
                        re_data["errorMessage"] = '订单红冲成功'
            else:
                re_data["success"] = False
                re_data["errorMessage"] = '订单不是已审核状态'
        except OrderIndex.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '订单不存在'

        await self.finish(re_data)


# 审核报溢单
class CheckGoodsOverflowOrderHandler(RedisHandler):
    @authenticated_async
    async def get(self, order_no, *args, **kwargs):
        re_data = {}
        try:
            order = await self.application.objects.get(OrderIndex, order_no=str(order_no))
            order_detail = await self.application.objects.execute(OrderDetail.select()
                                                                  .where(OrderDetail.order_no == str(order_no)))
            if order.order_state == 1:
                async with database.transaction_async() as txn:
                    # 处理库存及成本
                    order_cost_total, re_data = await OutInventoryCheck(
                        order, order_detail,
                        self.current_user.id).in_check_order(txn=txn, re_data=re_data)
                    if re_data["success"]:
                        # 插入科目账本
                        re_data = await AccountingSubjectInsert(
                            order, order_cost_total, self.current_user.id).goods_overflow(txn, re_data)
            else:
                re_data["success"] = False
                re_data["errorMessage"] = '订单不是待审核状态，请检查'
        except OrderIndex.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '订单不存在'

        await self.finish(re_data)


# 红冲报损单
class UnGoodsLossOrderHandler(RedisHandler):
    @authenticated_async
    async def get(self, order_no, *args, **kwargs):
        re_data = {}
        try:
            order = await self.application.objects.get(OrderIndex, order_no=str(order_no))
            order_detail = await self.application.objects.execute(OrderDetailAccount.select()
                                                                  .where(OrderDetailAccount.order_no == str(order_no)))
            if order.order_state == 2:
                async with database.transaction_async() as txn:
                    # 处理库存及成本
                    re_data = await OutInventoryCheck(
                        order, order_detail, self.current_user.id).un_out_check_order(
                        txn=txn, re_data=re_data)
                    if re_data["success"]:
                        # 插入科目账本
                        await AccountingSubjectInsert(
                            order=order, current_user_id=self.current_user.id).un_sale_order_check(
                            txn=txn, re_data=re_data)
                        re_data["success"] = True
                        re_data["errorMessage"] = '订单撤销成功'
            else:
                re_data["success"] = False
                re_data["errorMessage"] = '订单不是已审核状态'
        except OrderIndex.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '订单不存在'

        await self.finish(re_data)


# 审核报损单
class CheckGoodsLossOrderHandler(RedisHandler):
    @authenticated_async
    async def get(self, order_no, *args, **kwargs):
        re_data = {}
        try:
            order = await self.application.objects.get(OrderIndex, order_no=str(order_no))
            order_detail = await self.application.objects.execute(OrderDetail.select(OrderDetail)
                                                                  .where(OrderDetail.order_no == str(order_no)))
            if order.order_state == 1:
                async with database.transaction_async() as txn:
                    # 处理库存及成本
                    order_cost_total, re_data = await OutInventoryCheck(
                        order, order_detail,
                        self.current_user.id).out_check_order(txn=txn, re_data=re_data)
                    if re_data["success"]:
                        # 插入科目账本
                        re_data = await AccountingSubjectInsert(
                            order, order_cost_total, self.current_user.id).good_loss(txn, re_data)
            else:
                re_data["success"] = False
                re_data["errorMessage"] = '订单不是待审核状态，请检查'
        except OrderIndex.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '订单不存在'

        await self.finish(re_data)


# 红冲其他出库单
class UnOtherOutOrderHandler(RedisHandler):
    @authenticated_async
    async def get(self, order_no, *args, **kwargs):
        re_data = {}
        try:
            order = await self.application.objects.get(OrderIndex, order_no=str(order_no))
            order_detail = await self.application.objects.execute(OrderDetailAccount.select()
                                                                  .where(OrderDetailAccount.order_no == str(order_no)))
            if order.order_state == 2:
                async with database.transaction_async() as txn:
                    # 处理库存及成本
                    re_data = await OutInventoryCheck(
                        order, order_detail, self.current_user.id).un_out_check_order(
                        txn=txn, re_data=re_data)
                    if re_data["success"]:
                        # 插入科目账本
                        await AccountingSubjectInsert(
                            order=order, current_user_id=self.current_user.id).un_sale_order_check(
                            txn=txn, re_data=re_data)
                        re_data["success"] = True
                        re_data["errorMessage"] = '订单撤销成功'
            else:
                re_data["success"] = False
                re_data["errorMessage"] = '订单不是已审核状态'
        except OrderIndex.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '订单不存在'

        await self.finish(re_data)


# 审核其他出库单
class CheckOtherOutOrderHandler(RedisHandler):
    @authenticated_async
    async def get(self, order_no, *args, **kwargs):
        re_data = {}
        try:
            order = await self.application.objects.get(OrderIndex, order_no=str(order_no))
            order_detail = await self.application.objects.execute(OrderDetail.select(OrderDetail)
                                                                  .where(OrderDetail.order_no == str(order_no)))
            if order.order_state == 1:
                async with database.transaction_async() as txn:
                    # 处理库存及成本
                    order_cost_total, re_data = await OutInventoryCheck(
                        order, order_detail,
                        self.current_user.id).out_check_order(txn=txn, re_data=re_data)
                    if re_data["success"]:
                        # 插入科目账本
                        re_data = await AccountingSubjectInsert(
                            order, order_cost_total, self.current_user.id).other_out_bound(txn, re_data)
                        if re_data["success"]:
                            re_data["success"] = True
                            re_data["errorMessage"] = '订单审核成功'
            else:
                re_data["success"] = False
                re_data["errorMessage"] = '订单不是待审核状态，请检查'
        except OrderIndex.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '订单不存在'

        await self.finish(re_data)


# 红冲其他入库单
class UnOtherPutInOrderHandler(RedisHandler):
    @authenticated_async
    async def get(self, order_no, *args, **kwargs):
        # 红冲采购订单
        re_data = {}
        try:
            order = await self.application.objects.get(OrderIndex, order_no=str(order_no))
            order_detail = await self.application.objects.execute(OrderDetailAccount.select()
                                                                  .where(OrderDetailAccount.order_no == str(order_no)))
            if order.order_state == 2:
                async with database.transaction_async() as txn:
                    # 处理库存及成本
                    re_data = await OutInventoryCheck(
                        order, order_detail, self.current_user.id).un_in_check_order(
                        txn=txn, re_data=re_data)
                    if re_data["success"]:
                        # 插入科目账本
                        await AccountingSubjectInsert(
                            order=order, current_user_id=self.current_user.id).un_sale_order_check(
                            txn=txn, re_data=re_data)
                        re_data["success"] = True
                        re_data["errorMessage"] = '订单红冲成功'
            else:
                re_data["success"] = False
                re_data["errorMessage"] = '订单不是已审核状态'
        except OrderIndex.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '订单不存在'

        await self.finish(re_data)


# 审核其他入库单
class CheckOtherPutInOrderHandler(RedisHandler):
    @authenticated_async
    async def get(self, order_no, *args, **kwargs):
        re_data = {}
        try:
            order = await self.application.objects.get(OrderIndex, order_no=str(order_no))
            order_detail = await self.application.objects.execute(OrderDetail.select(OrderDetail)
                                                                  .where(OrderDetail.order_no == str(order_no)))
            if order.order_state == 1:
                async with database.transaction_async() as txn:
                    # 处理库存及成本
                    order_cost_total, re_data = await OutInventoryCheck(
                        order, order_detail,
                        self.current_user.id).in_check_order(txn=txn, re_data=re_data)
                    if re_data["success"]:
                        # 插入科目账本
                        re_data = await AccountingSubjectInsert(
                            order, order_cost_total, self.current_user.id).out_put_storage(txn, re_data)
                        if re_data["success"]:
                            re_data["success"] = True
                            re_data["errorMessage"] = '订单审核成功'
            else:
                re_data["success"] = False
                re_data["errorMessage"] = '订单不是待审核状态，请检查'
        except OrderIndex.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '订单不存在'

        await self.finish(re_data)


# 红冲调拨单
class UnTransfersOrderHandler(RedisHandler):
    @authenticated_async
    async def get(self, order_no, *args, **kwargs):
        re_data = {}
        try:
            order = await self.application.objects.get(OrderIndex, order_no=str(order_no))
            order_detail = await self.application.objects.execute(OrderDetailAccount.select()
                                                                  .where(OrderDetailAccount.order_no == str(order_no)))
            if order.order_state == 2:
                async with database.transaction_async() as txn:
                    # 撤销入库
                    re_data = await OutInventoryCheck(
                        order, order_detail, self.current_user.id).un_in_check_order(
                        txn=txn, re_data=re_data, rs_storehouse=order.rs_storehouse)
                    # 撤销出库
                    re_data = await OutInventoryCheck(
                        order, order_detail,
                        self.current_user.id).un_out_check_order(txn=txn, re_data=re_data)
                    if re_data["success"]:
                        # 插入科目账本
                        await AccountingSubjectInsert(
                            order=order, current_user_id=self.current_user.id).un_sale_order_check(
                            txn=txn, re_data=re_data)
                        re_data["success"] = True
                        re_data["errorMessage"] = '订单红冲成功'
            else:
                re_data["success"] = False
                re_data["errorMessage"] = '订单不是已审核状态'
        except OrderIndex.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '订单不存在'

        await self.finish(re_data)


# 审核调拨单
class CheckTransfersOrderHandler(RedisHandler):
    @authenticated_async
    async def get(self, order_no, *args, **kwargs):
        re_data = {}
        try:
            order = await self.application.objects.get(OrderIndex, order_no=str(order_no))
            order_detail = await self.application.objects.execute(OrderDetail.select(OrderDetail)
                                                                  .where(OrderDetail.order_no == str(order_no)))
            if order.order_state == 1:
                async with database.transaction_async() as txn:
                    # 出库
                    order_cost_total, re_data = await OutInventoryCheck(
                        order, order_detail,
                        self.current_user.id).out_check_order(txn=txn, re_data=re_data)
                    # 入库
                    order_cost_total2, re_data = await OutInventoryCheck(
                        order, order_detail,
                        self.current_user.id).in_check_order(txn=txn, re_data=re_data, rs_storehouse=order.rs_storehouse)
                    if re_data["success"]:
                        # 插入科目账本
                        re_data = await AccountingSubjectInsert(
                            order, order_cost_total, self.current_user.id).inventory_transfers(txn, re_data)
                        if re_data["success"]:
                            re_data["success"] = True
                            re_data["errorMessage"] = '订单审核成功'
            else:
                re_data["success"] = False
                re_data["errorMessage"] = '订单不是待审核状态，请检查'
        except OrderIndex.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '订单不存在'

        await self.finish(re_data)


# 红冲成本调整单
class unCostAdjustOrderHandler(RedisHandler):
    @authenticated_async
    async def get(self, order_no, *args, **kwargs):
        re_data = {}
        try:
            order = await self.application.objects.get(OrderIndex, order_no=str(order_no))
            order_detail = await self.application.objects.execute(OrderDetail.select(OrderDetail)
                                                                  .where(OrderDetail.order_no == str(order_no)))
            if order.order_state == 2:
                async with database.transaction_async() as txn:
                    # 处理库存及成本
                    order_cost_total, re_data = await OutInventoryCheck(
                        order, order_detail, self.current_user.id).un_check_cost_order(txn=txn, re_data=re_data)
                    if re_data["success"]:
                        # 插入科目账本
                        re_data = await AccountingSubjectInsert(
                            order, order_cost_total, self.current_user.id).un_sale_order_check(
                            txn=txn, re_data=re_data)
            else:
                re_data["success"] = False
                re_data["errorMessage"] = '订单不是已审核状态'
        except OrderIndex.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '订单不存在'

        await self.finish(re_data)


# 审核成本调整单
class CheckCostAdjustOrderHandler(RedisHandler):
    @authenticated_async
    async def get(self, order_no, *args, **kwargs):
        re_data = {}
        try:
            order = await self.application.objects.get(OrderIndex, order_no=str(order_no))
            order_detail = await self.application.objects.execute(OrderDetail.select(OrderDetail)
                                                                  .where(OrderDetail.order_no == str(order_no)))
            if order.order_state == 1:
                async with database.transaction_async() as txn:
                    # 处理库存及成本
                    order_cost_total, after_cost_amount, re_data = await OutInventoryCheck(
                        order, order_detail, self.current_user.id).check_cost_order(txn=txn, re_data=re_data)
                    if re_data["success"]:
                        # 插入科目账本
                        re_data = await AccountingSubjectInsert(
                            order, order_cost_total, self.current_user.id).cost_adjustment(
                            txn=txn, re_data=re_data, after_cost_amount=after_cost_amount)
            else:
                re_data["success"] = False
                re_data["errorMessage"] = '订单不是待审核状态，请检查'
        except OrderIndex.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '订单不存在'

        await self.finish(re_data)