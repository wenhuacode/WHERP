import json

from WHERP.handler import RedisHandler
from apps.utils.mxform_decorators import authenticated_async
from apps.product.product_handler.models import Product, ProductClassify
from apps.order.models.models import OrderIndex, OrderDetail, OrderDetailAccount
from apps.inventory_management.inventory_distribution_cost.models import StorehouseManagement, IrProperty
from apps.customer.customer_handler.models import Customer, CustomerClassify
from peewee import JOIN, fn, Case, SQL
from apps.utils.util_func import json_serial
from apps.utils.query_conditional import Conditional
from WHERP.settings import objects


# 库存查询
class InventoryQueryHandler(RedisHandler):
    @authenticated_async
    async def post(self, *args, **kwargs):
        re_data = {}
        data_list = []
        param = self.request.body.decode()
        param = json.loads(param)

        # 处理排序
        query_sort = None
        for key, value in param['sort'].items():
            if value == 'descend':
                query_sort = SQL(key).desc()
            else:
                query_sort = SQL(key).asc()

        expressions = []
        if 'storehouse' in param['params']:
            expressions.append(IrProperty.storehouse_id == param['params']['storehouse'])

        node_id = param['params']['node_id'][0]
        classic = await self.application.objects.execute(ProductClassify.select()
                                                         .where(ProductClassify.parent_id == node_id))
        # 判断分类是否存在子节点
        if classic:
            base = (IrProperty.select(fn.SUM(IrProperty.qty).alias('qty'),
                                      fn.SUM(IrProperty.total).alias('total'),
                                      ProductClassify.parent_path)
                    .join(Product, join_type=JOIN.LEFT_OUTER, on=(Product.barcode == IrProperty.barcode))
                    .join(ProductClassify, join_type=JOIN.LEFT_OUTER,
                          on=(Product.product_classify_id == ProductClassify.id))
                    .where(*expressions)
                    .group_by(ProductClassify.classify_no)
                    .cte('inventory_account'))

            sql = (ProductClassify.select(ProductClassify.id,
                                          ProductClassify.classify_no.alias("no"),
                                          ProductClassify.classify_name.alias("name"),
                                          fn.SUM(base.c.qty).alias('qty'),
                                          fn.SUM(base.c.total).alias('total'))
                   .join(base, join_type=JOIN.LEFT_OUTER,
                         on=(base.c.parent_path.contains(ProductClassify.parent_path)))
                   .where(ProductClassify.parent_id == node_id)
                   .group_by(ProductClassify.classify_no)
                   .order_by(query_sort)
                   .dicts()
                   .with_cte(base))

            data = await self.application.objects.execute(sql)

        else:
            last = Product.alias()
            expressions.append(last.product_classify_id == node_id)

            base = (last.select(last.product_no,
                                fn.SUM(IrProperty.qty).alias('qty'),
                                fn.SUM(IrProperty.total).alias('total'))
                    .join(IrProperty, join_type=JOIN.RIGHT_OUTER, on=(last.barcode == IrProperty.barcode))
                    .where(*expressions)
                    .group_by(last.product_no))

            sql2 = (Product.select(Product.name.alias("name"),
                                   Product.product_no.alias("no"),
                                   Product.barcode.alias("barcode"),
                                   base.c.qty,
                                   base.c.total, )
                    .join(base, join_type=JOIN.LEFT_OUTER, on=(base.c.product_no == Product.product_no))
                    .where(Product.product_classify_id == node_id)
                    .order_by(query_sort).dicts())

            data = await self.application.objects.execute(sql2)

        for item in data:
            data_list.append(item)

        re_data['data'] = data_list
        re_data["success"] = True
        await self.finish(json.dumps(re_data, default=json_serial))


# 库存详情查询
class InventoryQueryDetailHandler(RedisHandler):
    @authenticated_async
    async def post(self, *args, **kwargs):
        re_data = {}
        data_list = []
        param = self.request.body.decode()
        param = json.loads(param)

        # 处理排序
        query_sort = None
        for key, value in param['sort'].items():
            if value == 'descend':
                query_sort = SQL(key).desc()
            else:
                query_sort = SQL(key).asc()

        expressions = []
        expressions.append(OrderDetailAccount.order_type.in_([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]), )
        expressions.append(OrderDetailAccount.signed_data.between(param['params']['startTime'],
                                                                  param['params']['endTime']))
        expressions.append(OrderDetailAccount.barcode == param['params']['barcode'])
        if 'storehouse' in param['params']:
            expressions.append(OrderDetailAccount.storehouse_id == param['params']['storehouse'])

        base = (OrderDetailAccount
                .select(OrderDetailAccount.id,
                        Case(None, [((OrderDetailAccount.qty > 0), OrderDetailAccount.qty)], 0).alias('in_qty'),
                        Case(None, [((OrderDetailAccount.qty < 0), OrderDetailAccount.qty)], 0).alias('out_qty'),
                        )
                .where(*expressions)
                .cte('ol_account'))

        sql = (OrderDetailAccount
               .select(OrderDetailAccount.order_type,
                       OrderDetailAccount.signed_data,
                       OrderDetailAccount.order_no,
                       OrderDetailAccount.barcode,
                       Product.name.alias("product_name"),
                       ProductClassify.classify_name.alias("classify_name"),
                       Customer.uk_customer_no.alias("customer_no"),
                       Customer.name.alias("customer_name"),
                       StorehouseManagement.storehouse_no.alias("storehouse_no"),
                       StorehouseManagement.storehouse_name.alias("storehouse_name"),
                       base.c.in_qty.alias("in_qty"),
                       base.c.out_qty.alias("out_qty"),
                       fn.SUM(base.c.in_qty + base.c.out_qty).over(order_by=[OrderDetailAccount.id]).alias(
                           'qty'))
               .join(base, join_type=JOIN.LEFT_OUTER, on=(base.c.id == OrderDetailAccount.id))
               .join(Product, join_type=JOIN.LEFT_OUTER, on=(Product.barcode == OrderDetailAccount.barcode))
               .join(ProductClassify, join_type=JOIN.LEFT_OUTER,
                     on=(Product.product_classify_id == ProductClassify.id))
               .join(Customer, join_type=JOIN.LEFT_OUTER, on=(Customer.id == OrderDetailAccount.customer_id))
               .join(StorehouseManagement, join_type=JOIN.LEFT_OUTER,
                     on=(StorehouseManagement.id == OrderDetailAccount.storehouse_id))
               .where(*expressions)
               .group_by(OrderDetailAccount.id)
               .order_by(query_sort)
               .dicts()
               .with_cte(base)
               )

        data = await self.application.objects.execute(sql)
        for item in data:
            data_list.append(item)

        re_data['data'] = data_list
        re_data["success"] = True
        await self.finish(json.dumps(re_data, default=json_serial))
