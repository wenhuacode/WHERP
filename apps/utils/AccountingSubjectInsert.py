from datetime import datetime

from apps.utils.round_dec import round_dec
from apps.order.models.models import SubsidiaryLedger
from WHERP.settings import objects
from playhouse.shortcuts import model_to_dict


class AccountingSubjectInsert:
    """
    订单审核科目相关调整
    """

    def __init__(self, order=None, order_cost_total=None, current_user_id=None):
        self.order = order
        self.order_cost_total = order_cost_total
        self.current_user_id = current_user_id

    async def sale_order_check(self, txn=None, re_data=None):
        """
        销售订单
        :return:
        """
        try:
            # 【库存商品】类目减少
            await objects.create(SubsidiaryLedger,
                                 order_type=self.order.order_type,
                                 order_no=self.order.order_no,
                                 employee_id=self.order.employee_id,
                                 customer_id=self.order.customer_id,
                                 as_id=str('0103'),
                                 storehouse_id=self.order.storehouse_id,
                                 amount=-round_dec(self.order_cost_total, 2),
                                 create_user_id=self.current_user_id)
            # 【销售收入】类目增加(销售金额)
            await objects.create(SubsidiaryLedger,
                                 order_type=self.order.order_type,
                                 order_no=self.order.order_no,
                                 employee_id=self.order.employee_id,
                                 customer_id=self.order.customer_id,
                                 as_id=str('0301'),
                                 storehouse_id=self.order.storehouse_id,
                                 amount=round_dec(self.order.order_amount, 2),
                                 create_user_id=self.current_user_id)

            # 【销售成本】类目增加
            await objects.create(SubsidiaryLedger,
                                 order_type=self.order.order_type,
                                 order_no=self.order.order_no,
                                 employee_id=self.order.employee_id,
                                 customer_id=self.order.customer_id,
                                 as_id=str('0401'),
                                 storehouse_id=self.order.storehouse_id,
                                 amount=round_dec(self.order_cost_total, 2),
                                 create_user_id=self.current_user_id)
            # 【应收款合计】类目增加(销售金额)
            await objects.create(SubsidiaryLedger,
                                 order_type=self.order.order_type,
                                 order_no=self.order.order_no,
                                 employee_id=self.order.employee_id,
                                 customer_id=self.order.customer_id,
                                 as_id=str('0105'),
                                 storehouse_id=self.order.storehouse_id,
                                 amount=round_dec(self.order.order_amount, 2),
                                 create_user_id=self.current_user_id)
            # 【优惠金额】如果存在则插入
            if self.order.discount_amount > 0 or self.order.discount_amount < 0:
                await objects.create(SubsidiaryLedger,
                                     order_type=self.order.order_type,
                                     order_no=self.order.order_no,
                                     employee_id=self.order.employee_id,
                                     customer_id=self.order.customer_id,
                                     as_id=str('040814'),
                                     storehouse_id=self.order.storehouse_id,
                                     amount=round_dec(self.order.discount_amount, 2),
                                     create_user_id=self.current_user_id)
            # 【快递费】 如果存在则插入
            if self.order.express_fee > 0 or self.order.express_fee < 0:
                await objects.create(SubsidiaryLedger,
                                     order_type=self.order.order_type,
                                     order_no=self.order.order_no,
                                     employee_id=self.order.employee_id,
                                     customer_id=self.order.customer_id,
                                     as_id=str('040829'),
                                     storehouse_id=self.order.storehouse_id,
                                     amount=round_dec(self.order.express_fee, 2),
                                     create_user_id=self.current_user_id)
            re_data["success"] = True
            re_data["errorMessage"] = '订单审核成功'
        except Exception as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = f'发生其他错误: {e}'

        return re_data

    async def un_sale_order_check(self, txn=None, re_data=None):
        """
        销售订单撤销
        :return:
        """
        sl_detail = await objects.execute(SubsidiaryLedger
                                          .select().where(SubsidiaryLedger.order_no == self.order.order_no))
        try:
            sl = SubsidiaryLedger()
            sl_list = []
            for data in sl_detail:
                sl.order_type = data.order_type
                sl.date = data.date
                sl.order_no = data.order_no
                sl.employee_id = data.employee_id
                sl.as_id = data.as_id
                sl.customer_id = data.customer_id
                sl.amount = -data.amount
                sl.note = data.note
                sl.create_user_id = self.order.create_user_id

                sl_list.append(model_to_dict(sl))

            await objects.execute(SubsidiaryLedger.insert_many(sl_list))
            re_data["success"] = True
            re_data["errorMessage"] = '订单红冲成功'

        except Exception as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = f'发生其他错误: {e}'
        return re_data

    async def sale_return_check(self, txn=None, re_data=None):
        """
        销售退货单
        :return:
        """
        try:
            # 【库存商品】类目增加
            await objects.create(SubsidiaryLedger,
                                 order_type=self.order.order_type,
                                 order_no=self.order.order_no,
                                 employee_id=self.order.employee_id,
                                 customer_id=self.order.customer_id,
                                 as_id=str('0103'),
                                 storehouse_id=self.order.storehouse_id,
                                 amount=round_dec(self.order_cost_total, 2),
                                 create_user_id=self.current_user_id)
            # 【销售收入】类目减少(销售金额)
            await objects.create(SubsidiaryLedger,
                                 order_type=self.order.order_type,
                                 order_no=self.order.order_no,
                                 employee_id=self.order.employee_id,
                                 customer_id=self.order.customer_id,
                                 as_id=str('0301'),
                                 storehouse_id=self.order.storehouse_id,
                                 amount=-round_dec(self.order.order_amount, 2),
                                 create_user_id=self.current_user_id)
            # 【销售成本】类目减少
            await objects.create(SubsidiaryLedger,
                                 order_type=self.order.order_type,
                                 order_no=self.order.order_no,
                                 employee_id=self.order.employee_id,
                                 customer_id=self.order.customer_id,
                                 as_id=str('0401'),
                                 storehouse_id=self.order.storehouse_id,
                                 amount=-round_dec(self.order_cost_total, 2),
                                 create_user_id=self.current_user_id)
            # 【应收款合计】类目减少(销售金额)
            await objects.create(SubsidiaryLedger,
                                 order_type=self.order.order_type,
                                 order_no=self.order.order_no,
                                 employee_id=self.order.employee_id,
                                 customer_id=self.order.customer_id,
                                 as_id=str('0105'),
                                 storehouse_id=self.order.storehouse_id,
                                 amount=-round_dec(self.order.order_amount, 2),
                                 create_user_id=self.current_user_id)
            # 【优惠金额】如果存在则插入
            if self.order.discount_amount > 0 or self.order.discount_amount < 0:
                await objects.create(SubsidiaryLedger,
                                     order_type=self.order.order_type,
                                     order_no=self.order.order_no,
                                     employee_id=self.order.employee_id,
                                     customer_id=self.order.customer_id,
                                     as_id=str('040814'),
                                     storehouse_id=self.order.storehouse_id,
                                     amount=-round_dec(self.order.discount_amount, 2),
                                     create_user_id=self.current_user_id)
            # 【快递费】 如果存在则插入
            if self.order.express_fee > 0 or self.order.express_fee < 0:
                await objects.create(SubsidiaryLedger,
                                     order_type=self.order.order_type,
                                     order_no=self.order.order_no,
                                     employee_id=self.order.employee_id,
                                     customer_id=self.order.customer_id,
                                     as_id=str('040829'),
                                     storehouse_id=self.order.storehouse_id,
                                     amount=-round_dec(self.order.express_fee, 2),
                                     create_user_id=self.current_user_id)

            re_data["success"] = True
            re_data["errorMessage"] = '订单审核成功'

        except Exception as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = f'发生其他错误: {e}'

        return re_data

    async def purchase_order(self, txn=None, re_data=None):
        """
        采购订单
        :return:
        """
        try:
            # 【应付款合计】类目增加
            await objects.create(SubsidiaryLedger,
                                 order_type=self.order.order_type,
                                 order_no=self.order.order_no,
                                 employee_id=self.order.employee_id,
                                 as_id=str('0201'),
                                 customer_id=self.order.customer_id,
                                 storehouse_id=self.order.storehouse_id,
                                 amount=self.order.order_amount,
                                 create_user_id=self.current_user_id)
            # 【库存商品】类目增加
            await objects.create(SubsidiaryLedger,
                                 order_type=self.order.order_type,
                                 order_no=self.order.order_no,
                                 employee_id=self.order.employee_id,
                                 as_id=str('0103'),
                                 customer_id=self.order.customer_id,
                                 storehouse_id=self.order.storehouse_id,
                                 amount=self.order.order_amount,
                                 create_user_id=self.current_user_id)

            re_data["success"] = True
            re_data["errorMessage"] = '订单审核成功'

        except Exception as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = f'发生其他错误: {e}'

        return re_data

    async def purchase_return(self, txn=None, re_data=None):
        """
        采购退货
        :return:
        """
        try:
            # 【应付款合计】类目减少
            await objects.create(SubsidiaryLedger,
                                 order_type=self.order.order_type,
                                 order_no=self.order.order_no,
                                 employee_id=self.order.employee_id,
                                 as_id=str('0201'),
                                 customer_id=self.order.customer_id,
                                 storehouse_id=self.order.storehouse_id,
                                 amount=-self.order.order_amount,
                                 create_user_id=self.current_user_id)
            # 【库存商品】类目减少
            await objects.create(SubsidiaryLedger,
                                 order_type=self.order.order_type,
                                 order_no=self.order.order_no,
                                 employee_id=self.order.employee_id,
                                 as_id=str('0103'),
                                 customer_id=self.order.customer_id,
                                 storehouse_id=self.order.storehouse_id,
                                 amount=-self.order.order_amount,
                                 create_user_id=self.current_user_id)
            # 判断采购退货差价增加还是减少
            return_price_difference = (float(self.order.order_amount) - float(self.order_cost_total))
            if return_price_difference > 0:
                # 【采购退货差价】类目增加
                await objects.create(SubsidiaryLedger,
                                     order_type=self.order.order_type,
                                     date=datetime.today(),
                                     order_no=self.order.order_no,
                                     employee_id=self.order.employee_id,
                                     as_id=str('030204'),
                                     customer_id=self.order.customer_id,
                                     storehouse_id=self.order.storehouse_id,
                                     amount=round_dec(
                                         return_price_difference, 2),
                                     create_user_id=self.current_user_id)
            if return_price_difference < 0:
                # 【采购退货差价】类目减少
                await objects.create(SubsidiaryLedger,
                                     order_type=self.order.order_type,
                                     date=datetime.today(),
                                     order_no=self.order.order_no,
                                     employee_id=self.order.employee_id,
                                     as_id=str('030204'),
                                     customer_id=self.order.customer_id,
                                     storehouse_id=self.order.storehouse_id,
                                     amount=-round_dec(
                                         return_price_difference, 2),
                                     create_user_id=self.current_user_id)

            re_data["success"] = True
            re_data["errorMessage"] = '订单审核成功'

        except Exception as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = f'发生其他错误: {e}'

        return re_data

    async def good_loss(self, txn=None, re_data=None):
        """
        报损
        :return:
        """
        # 【商品报损】类目增加
        try:
            await objects.create(SubsidiaryLedger,
                                 order_type=self.order.order_type,
                                 order_no=self.order.order_no,
                                 employee_id=self.order.employee_id,
                                 as_id=str('040201'),
                                 storehouse_id=self.order.storehouse_id,
                                 amount=round_dec(self.order_cost_total, 2),
                                 create_user_id=self.current_user_id)
            # 【库存商品】类目减少
            await objects.create(SubsidiaryLedger,
                                 order_type=self.order.order_type,
                                 order_no=self.order.order_no,
                                 employee_id=self.order.employee_id,
                                 as_id=str('0103'),
                                 as_name='库存商品',
                                 storehouse_id=self.order.storehouse_id,
                                 amount=-round_dec(self.order_cost_total, 2),
                                 create_user_id=self.current_user_id)
            re_data["success"] = True
            re_data["errorMessage"] = '订单审核成功'

        except Exception as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = f'发生其他错误: {e}'

        return re_data

    async def goods_overflow(self, txn=None, re_data=None):
        # 【商品报溢收入】类目增加
        try:
            await objects.create(SubsidiaryLedger,
                                 order_type=self.order.order_type,
                                 order_no=self.order.order_no,
                                 employee_id=self.order.employee_id,
                                 as_id=str('030201'),
                                 storehouse_id=self.order.storehouse_id,
                                 amount=round_dec(self.order_cost_total, 2),
                                 create_user_id=self.current_user_id)
            # 【库存商品】类目增加
            await objects.create(SubsidiaryLedger,
                                 order_type=self.order.order_type,
                                 order_no=self.order.order_no,
                                 employee_id=self.order.employee_id,
                                 as_id=str('0103'),
                                 storehouse_id=self.order.storehouse_id,
                                 amount=round_dec(self.order_cost_total, 2),
                                 create_user_id=self.current_user_id)
            re_data["success"] = True
            re_data["errorMessage"] = '订单审核成功'

        except Exception as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = f'发生其他错误: {e}'

        return re_data

    async def other_out_bound(self, txn=None, re_data=None):
        """
        其他出库
        :return:
        """
        try:
            # 【其它出库费用】类目增加
            await objects.create(SubsidiaryLedger,
                                 order_type=self.order.order_type,
                                 order_no=self.order.order_no,
                                 employee_id=self.order.employee_id,
                                 as_id=str('040202'),
                                 storehouse_id=self.order.storehouse_id,
                                 amount=round_dec(self.order_cost_total, 2),
                                 create_user_id=self.current_user_id)
            # 【库存商品】类目减少
            await objects.create(SubsidiaryLedger,
                                 order_type=self.order.order_type,
                                 order_no=self.order.order_no,
                                 employee_id=self.order.employee_id,
                                 as_id=str('0103'),
                                 storehouse_id=self.order.storehouse_id,
                                 amount=-round_dec(self.order_cost_total, 2),
                                 create_user_id=self.current_user_id)
            re_data["success"] = True
            re_data["errorMessage"] = '订单审核成功'

        except Exception as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = f'发生其他错误: {e}'

        return re_data

    async def out_put_storage(self, txn=None, re_data=None):
        """
        其他入库
        :return:
        """
        try:
            # 【其他入库收入】类目增加
            await objects.create(SubsidiaryLedger,
                                 order_type=self.order.order_type,
                                 order_no=self.order.order_no,
                                 employee_id=self.order.employee_id,
                                 as_id=str('030202'),
                                 storehouse_id=self.order.storehouse_id,
                                 amount=round_dec(self.order_cost_total, 2),
                                 create_user_id=self.current_user_id)
            # 【库存商品】类目增加
            await objects.create(SubsidiaryLedger,
                                 order_type=self.order.order_type,
                                 order_no=self.order.order_no,
                                 employee_id=self.order.employee_id,
                                 as_id=str('0103'),
                                 storehouse_id=self.order.storehouse_id,
                                 amount=round_dec(self.order_cost_total, 2),
                                 create_user_id=self.current_user_id)
            re_data["success"] = True
            re_data["errorMessage"] = '订单审核成功'

        except Exception as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = f'发生其他错误: {e}'

        return re_data

    async def inventory_transfers(self, txn=None, re_data=None):
        """
        调拨
        :return:
        """
        try:
            # 【库存商品】类目减少
            await objects.create(SubsidiaryLedger,
                                 order_type=self.order.order_type,
                                 order_no=self.order.order_no,
                                 employee_id=self.order.employee_id,
                                 as_id=str('0103'),
                                 storehouse_id=self.order.storehouse_id,
                                 amount=-round_dec(self.order_cost_total, 2),
                                 create_user_id=self.current_user_id)
            # 【库存商品】类目增加
            await objects.create(SubsidiaryLedger,
                                 order_type=self.order.order_type,
                                 order_no=self.order.order_no,
                                 employee_id=self.order.employee_id,
                                 as_id=str('0103'),
                                 storehouse_id=self.order.rs_storehouse,
                                 amount=round_dec(self.order_cost_total, 2),
                                 create_user_id=self.current_user_id)
            re_data["success"] = True
            re_data["errorMessage"] = '订单审核成功'

        except Exception as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = f'发生其他错误: {e}'

        return re_data

    async def cost_adjustment(self, txn=None, re_data=None, after_cost_amount=None):
        """
        成本调价
        :param after_cost_amount:
        :return:
        """
        try:
            if (self.order_cost_total - after_cost_amount) > 0:
                # 【成本调价收入】类目增加
                await objects.create(SubsidiaryLedger,
                                     order_type=self.order.order_type,
                                     order_no=self.order.order_no,
                                     employee_id=self.order.employee_id,
                                     as_id=str('030203'),
                                     storehouse_id=self.order.storehouse_id,
                                     amount=round_dec((self.order_cost_total -
                                                       after_cost_amount), 2),
                                     create_user_id=self.current_user_id)
            if (self.order_cost_total - after_cost_amount) < 0:
                # 【成本调价收入】类目减少
                await objects.create(SubsidiaryLedger,
                                     order_type=self.order.order_type,
                                     order_no=self.order.order_no,
                                     employee_id=self.order.employee_id,
                                     as_id=str('030203'),
                                     storehouse_id=self.order.storehouse_id,
                                     amount=-round_dec((self.order_cost_total -
                                                        after_cost_amount), 2),
                                     create_user_id=self.current_user_id)
            # 【库存商品】类目减少
            await objects.create(SubsidiaryLedger,
                                 order_type=self.order.order_type,
                                 order_no=self.order.order_no,
                                 employee_id=self.order.employee_id,
                                 as_id=str('0103'),
                                 storehouse_id=self.order.storehouse_id,
                                 amount=-round_dec(self.order_cost_total, 2),
                                 create_user_id=self.current_user_id)
            # 【库存商品】类目增加
            await objects.create(SubsidiaryLedger,
                                 order_type=self.order.order_type,
                                 order_no=self.order.order_no,
                                 employee_id=self.order.employee_id,
                                 as_id=str('0103'),
                                 storehouse_id=self.order.storehouse_id,
                                 amount=round_dec(after_cost_amount, 2),
                                 create_user_id=self.current_user_id)
            re_data["success"] = True
            re_data["errorMessage"] = '订单审核成功'

        except Exception as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = f'发生其他错误: {e}'

        return re_data
