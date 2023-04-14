import json

from WHERP.handler import RedisHandler
from WHERP.settings import database
from apps.utils.mxform_decorators import authenticated_async
from apps.order.sale_order.forms import CreateOrderForm
from playhouse.shortcuts import model_to_dict
from apps.utils.util_func import json_serial
from apps.product.product_handler.models import Product
from apps.customer.customer_handler.models import Customer
from apps.utils.OutInventoryCheck import OutInventoryCheck
from apps.utils.AccountingSubjectInsert import AccountingSubjectInsert
from apps.order.models.models import OrderIndex, OrderDetail, OrderDetailAccount
from peewee import JOIN


class GetBusinessHistoryHandler(RedisHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        re_data = {}
        data = []
        current = self.get_argument("current", None)
        pageSize = self.get_argument("pageSize", None)

        from apps.utils.FilterParams import Filter

        expressions = await Filter(self.request.arguments).order_filter(model=OrderIndex,
                                                                        model2=Customer, business_type=2)
        items = await self.application.objects.execute(
            OrderIndex.extend().where(*expressions).order_by(OrderIndex.add_time.desc()).paginate(int(current),
                                                                                                  int(pageSize)))
        total = await self.application.objects.count(OrderIndex.extend().where(*expressions))

        for item in items:
            obj_data = model_to_dict(item)
            if 'storehouse' in dir(item):
                obj_data['storehouse_name_id'] = item.storehouse.storehouse_name
            if 'Customer' in dir(item):
                obj_data['customer_id'] = item.Customer.id
                obj_data['customer_name'] = item.Customer.name
            obj_data['create_user_id'] = item.create_user.name
            # obj_data['order_type'] = item.order_type.name
            data.append(obj_data)
        re_data["data"] = data
        re_data["total"] = total
        re_data["page"] = current
        re_data["success"] = True

        await self.finish(json.dumps(re_data, default=json_serial))


class GetOrderDetailHandler(RedisHandler):
    @authenticated_async
    async def get(self, order_no, *args, **kwargs):
        # 获取订单商品信息
        re_data = {}
        data = {}
        table = []
        order = await self.application.objects.execute(OrderIndex.extend()
                                                       .where(OrderIndex.order_no == str(order_no)))
        if order:
            for temp in order:
                if temp.order_type in {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}:
                    order_detail = await self.application.objects.execute(OrderDetail.extend()
                                                                          .where(OrderDetail.order_no == str(order_no)))
                else:
                    order_detail = await self.application.objects.execute(OrderDetail.extend_other()
                                                                          .where(OrderDetail.order_no == str(order_no)))
                for item in order_detail:
                    product = (model_to_dict(item))
                    if 'product' in dir(item):
                        product['product_name'] = item.product.name
                    if 'accounting_subject' in dir(item):
                        product['product_name'] = item.accounting_subject.name
                    table.append(product)

                for o in order:
                    data.update(model_to_dict(o))
                    if 'storehouse_name' in dir(o):
                        data['storehouse_name_id'] = o.storehouse.storehouse_name
                    if 'Customer' in dir(o):
                        data['customer_id'] = o.Customer.id
                        data['customer_name'] = o.Customer.name
                    data['create_user_id'] = o.create_user.name
                    # data['order_type'] = o.order_type.name
                    data['area'] = [o.province_id, o.city_id, o.district_id]
                data["table"] = table

                re_data["data"] = data
                re_data["success"] = True
                re_data["errorMessage"] = '订单详情获取成功'
        else:
            re_data["success"] = False
            re_data["errorMessage"] = '单据不存在'
        await self.finish(json.dumps(re_data, default=json_serial))


class OrderHandler(RedisHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        re_data = {}
        data = []
        current = self.get_argument("current", None)
        pageSize = self.get_argument("pageSize", None)

        from apps.utils.FilterParams import Filter

        expressions = await Filter(self.request.arguments).order_filter(model=OrderIndex, model2=Customer)
        items = await self.application.objects.execute(
            OrderIndex.extend().where(*expressions).order_by(OrderIndex.add_time.desc()).paginate(int(current),
                                                                                                  int(pageSize)))
        total = await self.application.objects.count(OrderIndex.extend().where(*expressions))

        for item in items:
            obj_data = model_to_dict(item)
            if 'storehouse' in dir(item):
                obj_data['storehouse_name_id'] = item.storehouse.storehouse_name
            if 'Customer' in dir(item):
                obj_data['customer_id'] = item.Customer.id
                obj_data['customer_name'] = item.Customer.name
            obj_data['create_user_id'] = item.create_user.name
            # obj_data['order_type'] = item.order_type.name
            data.append(obj_data)
        re_data["data"] = data
        re_data["total"] = total
        re_data["page"] = current
        re_data["success"] = True

        await self.finish(json.dumps(re_data, default=json_serial))

    @authenticated_async
    async def post(self, *args, **kwargs):
        re_data = {}
        param = self.request.body.decode('utf-8')
        param = json.loads(param)
        form = CreateOrderForm.from_json(param)
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
                                                          storehouse_id=form.storehouse_id.data,
                                                          employee_id=form.employee_id.data,
                                                          signed_data=form.signed_data.data,
                                                          order_qty=form.order_qty.data,
                                                          total_sales_amount=form.total_sales_amount.data,
                                                          order_discount=form.order_discount.data,
                                                          express_fee=form.express_fee.data,
                                                          discount_amount=form.discount_amount.data,
                                                          order_amount=form.order_amount.data,
                                                          note=form.note.data,
                                                          contact_person=form.contact_person.data,
                                                          phone_number=form.phone_number.data,
                                                          province_id=form.area.data[0],
                                                          city_id=form.area.data[1],
                                                          district_id=form.area.data[2],
                                                          address=form.address.data,
                                                          courier_company=form.courier_company.data,
                                                          courier_number=form.courier_number.data,
                                                          create_user_id=self.current_user.id)
                    await self.application.objects.execute(OrderDetail.insert_many(form.table.data))
                re_data["success"] = True
                re_data["errorMessage"] = '创建成功'

        else:
            for field in form.errors:
                re_data["errorMessage"] = form.errors[field][0]
        await self.finish(re_data)

    @authenticated_async
    async def patch(self, order_no, *args, **kwargs):
        # 修改订单
        re_data = {}
        param = self.request.body.decode('utf-8')
        param = json.loads(param)
        form = CreateOrderForm.from_json(param)
        if form.validate():
            try:
                order = await self.application.objects.get(OrderIndex, order_no=str(order_no))
                if order.order_state == 1 or order.order_state == 4:
                    order.order_no = form.order_no.data
                    order.order_state = 1
                    order.customer_id = form.customer_id.data
                    order.employee_id = form.employee_id.data
                    order.storehouse_id = form.storehouse_id.data
                    order.signed_data = form.signed_data.data
                    order.order_qty = form.order_qty.data
                    order.total_sales_amount = float(form.total_sales_amount.data)
                    order.order_discount = float(form.order_discount.data)
                    order.express_fee = float(form.express_fee.data)
                    order.discount_amount = float(form.discount_amount.data)
                    order.order_amount = float(form.order_amount.data)
                    order.note = form.note.data
                    order.contact_person = form.contact_person.data
                    order.phone_number = form.phone_number.data
                    order.province_id = form.area.data[0]
                    order.city_id = form.area.data[1]
                    order.district_id = form.area.data[2]
                    order.address = form.address.data
                    order.courier_company = form.courier_company.data
                    order.courier_number = form.courier_number.data
                    order.create_user_id = self.current_user.id

                    async with database.atomic_async():
                        await self.application.objects.execute(OrderDetail.delete()
                                                               .where(OrderDetail.order_no == str(order_no)))
                        await self.application.objects.update(order)

                        await self.application.objects.execute(OrderDetail.insert_many(form.table.data))

                    re_data["success"] = True
                    re_data["errorMessage"] = '创建成功'
                else:
                    re_data["success"] = False
                    re_data["errorMessage"] = '订单状态不是待审核或已拒绝状态'
            except OrderIndex.DoesNotExist as e:
                re_data["success"] = False
                re_data["errorMessage"] = '订单不存在，请检查订单数据'
        else:
            for field in form.errors:
                re_data["errorMessage"] = form.errors[field][0]
        await self.finish(re_data)


class UnSaleOrderHandler(RedisHandler):
    @authenticated_async
    async def get(self, order_no, *args, **kwargs):
        # 撤销订单
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
            else:
                re_data["success"] = False
                re_data["errorMessage"] = '订单不是已审核状态'
        except OrderIndex.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '订单不存在'

        await self.finish(re_data)


class CheckSaleOrderHandler(RedisHandler):
    @authenticated_async
    async def get(self, order_no, *args, **kwargs):
        # 审核订单
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
                            order, order_cost_total, self.current_user.id).sale_order_check(txn, re_data)
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


class UnSaleOrderReturnHandler(RedisHandler):
    @authenticated_async
    async def get(self, order_no, *args, **kwargs):
        # 红冲销售退货订单
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
                re_data["errorMessage"] = '订单撤销成功'
            else:
                re_data["success"] = False
                re_data["errorMessage"] = '订单不是已审核状态'
        except OrderIndex.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '订单不存在'

        await self.finish(re_data)


class CheckSaleOrderReturnHandler(RedisHandler):
    @authenticated_async
    async def get(self, order_no, *args, **kwargs):
        # 审核销售退货订单
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
                            order, order_cost_total, self.current_user.id).sale_return_check(txn, re_data)
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
