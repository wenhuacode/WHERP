from wherp.handler import RedisHandler
from wherp.settings import database
from apps.utils.mxform_decorators import authenticated_async
from apps.product.product_handler.models import Product
from apps.utils.OutInventoryCheck import OutInventoryCheck
from apps.utils.AccountingSubjectInsert import AccountingSubjectInsert
from apps.order.models.models import OrderIndex, OrderDetail, OrderDetailAccount
from peewee import JOIN


# 红冲采购单
class UnPurchaseOrderHandler(RedisHandler):
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


# 审核采购单
class CheckPurchaseOrderHandler(RedisHandler):
    @authenticated_async
    async def get(self, order_no, *args, **kwargs):
        # 审核采购订单
        re_data = {}
        try:
            order = await self.application.objects.get(OrderIndex, order_no=str(order_no))
            order_detail = await self.application.objects.execute(OrderDetail.select(OrderDetail, Product.name)
                                                                  .join(Product, join_type=JOIN.LEFT_OUTER,
                                                                        on=(OrderDetail.barcode == Product.barcode),
                                                                        attr="product")
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
                            order, order_cost_total, self.current_user.id).purchase_order(txn, re_data)
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


# 红冲采购退货单
class UnPurchaseOrderReturnHandler(RedisHandler):
    @authenticated_async
    async def get(self, order_no, *args, **kwargs):
        # 红冲采购退货订单
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


# 审核采购退货单
class CheckPurchaseOrderReturnHandler(RedisHandler):
    @authenticated_async
    async def get(self, order_no, *args, **kwargs):
        # 审核采购退货订单
        re_data = {}
        try:
            order = await self.application.objects.get(OrderIndex, order_no=str(order_no))
            order_detail = await self.application.objects.execute(OrderDetail.select(OrderDetail, Product.name)
                                                                  .join(Product, join_type=JOIN.LEFT_OUTER,
                                                                        on=(OrderDetail.barcode == Product.barcode),
                                                                        attr="product")
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
                            order, order_cost_total, self.current_user.id).purchase_return(txn, re_data)
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
