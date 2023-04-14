import json
from datetime import datetime

from peewee import fn
from wherp.handler import RedisHandler
from apps.utils.mxform_decorators import authenticated_async
from apps.finance.accounting_subject.models import AccountingSubject

from apps.order.base.models import OrderType
from playhouse.shortcuts import model_to_dict
from apps.utils.util_func import json_serial
from apps.order.models.models import OrderIndex


class GETOrderNOHandler(RedisHandler):
    # 获取订单编号
    @authenticated_async
    async def get(self, order_no, *args, **kwargs):
        re_data = {}
        data = datetime.now().strftime('%Y%m%d')
        data_today = datetime.now().strftime('%Y-%m-%d 00:00:00')
        try:
            order_type = await self.application.objects.get(OrderType, id=int(order_no))
            order_no = await self.application.objects.execute(OrderIndex
                                                              .select(fn.Count(OrderIndex.id))
                                                              .where((OrderIndex.add_time >= data_today) &
                                                                     (OrderIndex.order_type == order_type.id)))
            for orderno in order_no:
                if orderno.id is None:
                    re_data['id'] = f"{order_type.num_ber_head}{self.current_user.id}{data}00001"
                    break
                re_data['id'] = f"{order_type.num_ber_head}{self.current_user.id}{data}0000{str(orderno.id + 1)}"
            re_data["success"] = True
        except OrderIndex.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '编码不存在'
        await self.finish(re_data)


class GetOrderType(RedisHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        re_data = {}
        data = []
        order_type = await self.application.objects.execute(OrderType.select())
        for item in order_type:
            data.append(model_to_dict(item))

        re_data["data"] = data
        re_data["success"] = True

        await self.finish(json.dumps(re_data, default=json_serial))


class GetBankNoList(RedisHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        re_data = {}
        data = []
        bank = await self.application.objects.execute(
            AccountingSubject.select().where((AccountingSubject.parent_id == 8) |
                                             (AccountingSubject.parent_id == 9)))

        for item in bank:
            data.append(model_to_dict(item))
        re_data["data"] = data
        re_data["success"] = True

        await self.finish(json.dumps(re_data, default=json_serial))


class GetGcCostList(RedisHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        re_data = {}
        data = []
        bank = await self.application.objects.execute(
            AccountingSubject.select().where(AccountingSubject.parent_id == 15))

        for item in bank:
            data.append(model_to_dict(item))
        re_data["data"] = data
        re_data["success"] = True

        await self.finish(json.dumps(re_data, default=json_serial))


class GetIcCostList(RedisHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        re_data = {}
        data = []
        bank = await self.application.objects.execute(
            AccountingSubject.select().where(AccountingSubject.parent_id == 29))

        for item in bank:
            data.append(model_to_dict(item))

        re_data["data"] = data
        re_data["success"] = True

        await self.finish(json.dumps(re_data, default=json_serial))


# 拒绝订单
class RefuseOrderHandler(RedisHandler):
    @authenticated_async
    async def get(self, order_no, *args, **kwargs):
        re_data = {}
        try:
            order = await self.application.objects.get(OrderIndex, order_no=str(order_no))
            if order.order_state == 1:
                order.order_state = 4
                await self.application.objects.update(order)
                re_data["success"] = True
                re_data["errorMessage"] = '订单拒绝成功'
            else:
                re_data["success"] = False
                re_data["errorMessage"] = '订单不是未审核状态'
        except OrderIndex.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '订单不存在'
        await self.finish(re_data)


class CancelOrderHandler(RedisHandler):
    @authenticated_async
    async def get(self, order_no, *args, **kwargs):
        # 取消订单
        re_data = {}
        try:
            order = await self.application.objects.get(OrderIndex, order_no=str(order_no))
            if order.order_state == 1 or order.order_state == 4:
                order.order_state = 0
                await self.application.objects.update(order)
                re_data["success"] = True
                re_data["errorMessage"] = '订单取消成功'
            else:
                re_data["success"] = False
                re_data["errorMessage"] = '订单不是未审核状态'
        except OrderIndex.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '订单不存在'
        await self.finish(re_data)


