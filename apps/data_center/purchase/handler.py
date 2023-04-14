import json

from WHERP.handler import RedisHandler
from apps.utils.mxform_decorators import authenticated_async
from apps.product.product_handler.models import Product, ProductClassify
from apps.order.models.models import OrderIndex, OrderDetail, OrderDetailAccount
from apps.inventory_management.inventory_distribution_cost.models import StorehouseManagement
from apps.customer.customer_handler.models import Customer, CustomerClassify
from peewee import JOIN, fn, Case
from apps.utils.util_func import json_serial
from apps.utils.query_conditional import Conditional


# 产品进货查询
class ProductPurchaseQueryHandler(RedisHandler):
    @authenticated_async
    async def post(self, *args, **kwargs):
        re_data = {}
        data_list = []
        param = self.request.body.decode()
        param = json.loads(param)

        query_sort, expressions = await Conditional(param=param, order_type=[3, 4])

        node_id = param['params']['node_id'][0]
        classic = await self.application.objects.execute(ProductClassify.select()
                                                         .where(ProductClassify.parent_id == node_id))
        # 判断分类是否存在子节点
        if classic:
            base = (OrderDetailAccount.select(fn.SUM(OrderDetailAccount.qty).alias('qty'),
                                              fn.AVG(OrderDetailAccount.discount_price).alias('avg_price'),
                                              fn.SUM(OrderDetailAccount.discount_total).alias('discount_total'),
                                              fn.AVG(OrderDetailAccount.cost_price).alias('cost_price'),
                                              fn.SUM(OrderDetailAccount.cost_total).alias('cost_total'),
                                              ProductClassify.parent_path)
                    .join(Product, join_type=JOIN.LEFT_OUTER, on=(Product.barcode == OrderDetailAccount.barcode))
                    .join(ProductClassify, join_type=JOIN.LEFT_OUTER,
                          on=(Product.product_classify_id == ProductClassify.id))
                    .join(Customer, join_type=JOIN.LEFT_OUTER, on=(Customer.id == OrderDetailAccount.customer_id))
                    .join(CustomerClassify, join_type=JOIN.LEFT_OUTER,
                          on=(Customer.customer_classify == CustomerClassify.id))
                    .where(*expressions)
                    .group_by(ProductClassify.classify_no)
                    .cte('order_detail_account'))

            sql = (ProductClassify.select(ProductClassify.id,
                                          ProductClassify.classify_no.alias("no"),
                                          ProductClassify.classify_name.alias("name"),
                                          fn.SUM(base.c.qty).alias('qty'),
                                          fn.AVG(base.c.avg_price).alias('avg_price'),
                                          fn.SUM(base.c.discount_total).alias('discount_total'),
                                          fn.AVG(base.c.cost_price).alias('cost_price'),
                                          fn.SUM(base.c.cost_total).alias('cost_total'), )
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
            base = (last.select(last.product_no,
                                fn.SUM(OrderDetailAccount.qty).alias('qty'),
                                fn.AVG(OrderDetailAccount.discount_price).alias('avg_price'),
                                fn.SUM(OrderDetailAccount.discount_total).alias('discount_total'),
                                fn.SUM(OrderDetailAccount.cost_price).alias('cost_price'),
                                fn.SUM(OrderDetailAccount.cost_total).alias('cost_total'),
                                )
                    .join(OrderDetailAccount, join_type=JOIN.RIGHT_OUTER,
                          on=(last.barcode == OrderDetailAccount.barcode))
                    .join(Customer, join_type=JOIN.LEFT_OUTER, on=(Customer.id == OrderDetailAccount.customer_id))
                    .join(CustomerClassify, join_type=JOIN.LEFT_OUTER,
                          on=(Customer.customer_classify == CustomerClassify.id))
                    .group_by(last.product_no)
                    .where(*expressions))

            sql2 = Product.select(Product.name.alias("name"),
                                  Product.product_no.alias("no"),
                                  Product.barcode.alias("barcode"),
                                  base.c.qty,
                                  base.c.avg_price,
                                  base.c.discount_total,
                                  base.c.cost_price,
                                  base.c.cost_total, ) \
                .join(base, join_type=JOIN.LEFT_OUTER, on=(base.c.product_no == Product.product_no)) \
                .where(Product.product_classify_id == node_id) \
                .order_by(query_sort).dicts()

            data = await self.application.objects.execute(sql2)

        for item in data:
            data_list.append(item)

        re_data['data'] = data_list
        re_data["success"] = True
        await self.finish(json.dumps(re_data, default=json_serial))


# 客户进货查询
class CustomerPurchaseQueryHandler(RedisHandler):
    @authenticated_async
    async def post(self, *args, **kwargs):
        re_data = {}
        data_list = []
        param = self.request.body.decode()
        param = json.loads(param)

        query_sort, expressions = await Conditional(param=param, order_type=[3,4])

        node_id = param['params']['node_id'][0]
        classic = await self.application.objects.execute(CustomerClassify.select()
                                                         .where(CustomerClassify.parent_id == node_id))
        # 判断分类是否存在子节点
        if classic:
            base = (OrderDetailAccount.select(fn.SUM(OrderDetailAccount.qty).alias('qty'),
                                              fn.AVG(OrderDetailAccount.discount_price).alias('avg_price'),
                                              fn.SUM(OrderDetailAccount.discount_total).alias('discount_total'),
                                              fn.AVG(OrderDetailAccount.cost_price).alias('cost_price'),
                                              fn.SUM(OrderDetailAccount.cost_total).alias('cost_total'),
                                              CustomerClassify.parent_path)
                    .join(Customer, join_type=JOIN.LEFT_OUTER, on=(Customer.id == OrderDetailAccount.customer_id))
                    .join(CustomerClassify, join_type=JOIN.LEFT_OUTER,
                          on=(Customer.customer_classify == CustomerClassify.id))
                    .join(Product, join_type=JOIN.LEFT_OUTER, on=(Product.barcode == OrderDetailAccount.barcode))
                    .join(ProductClassify, join_type=JOIN.LEFT_OUTER,
                          on=(Product.product_classify_id == ProductClassify.id))
                    .where(*expressions)
                    .group_by(CustomerClassify.id)
                    .cte('order_detail_account'))

            sql = (CustomerClassify.select(CustomerClassify.id,
                                           CustomerClassify.classify_no.alias("no"),
                                           CustomerClassify.classify_name.alias("name"),
                                           fn.SUM(base.c.qty).alias('qty'),
                                           fn.AVG(base.c.avg_price).alias('avg_price'),
                                           fn.SUM(base.c.discount_total).alias('discount_total'),
                                           fn.AVG(base.c.cost_price).alias('cost_price'),
                                           fn.SUM(base.c.cost_total).alias('cost_total'), )
                   .join(base, join_type=JOIN.LEFT_OUTER,
                         on=(base.c.parent_path.contains(CustomerClassify.parent_path)))
                   .where(CustomerClassify.parent_id == node_id)
                   .group_by(CustomerClassify.id)
                   .order_by(query_sort)
                   .dicts()
                   .with_cte(base))
            data = await self.application.objects.execute(sql)

        else:
            last = Customer.alias()
            base = (last.select(last.uk_customer_no,
                                fn.SUM(OrderDetailAccount.qty).alias('qty'),
                                fn.AVG(OrderDetailAccount.discount_price).alias('avg_price'),
                                fn.SUM(OrderDetailAccount.discount_total).alias('discount_total'),
                                fn.SUM(OrderDetailAccount.cost_price).alias('cost_price'),
                                fn.SUM(OrderDetailAccount.cost_total).alias('cost_total'),
                                )
                    .join(OrderDetailAccount, join_type=JOIN.RIGHT_OUTER,
                          on=(last.id == OrderDetailAccount.customer_id))
                    .join(Product, join_type=JOIN.LEFT_OUTER, on=(Product.barcode == OrderDetailAccount.barcode))
                    .join(ProductClassify, join_type=JOIN.LEFT_OUTER,
                          on=(Product.product_classify_id == ProductClassify.id))
                    .group_by(last.uk_customer_no)
                    .where(*expressions))

            sql2 = Customer.select(Customer.name.alias("name"),
                                   Customer.uk_customer_no.alias("no"),
                                   Customer.id.alias("customer_id"),
                                   base.c.qty,
                                   base.c.avg_price,
                                   base.c.discount_total,
                                   base.c.cost_price,
                                   base.c.cost_total, ) \
                .join(base, join_type=JOIN.LEFT_OUTER, on=(base.c.uk_customer_no == Customer.uk_customer_no)) \
                .where(Customer.customer_classify == node_id) \
                .order_by(query_sort).dicts()

            data = await self.application.objects.execute(sql2)

        for item in data:
            data_list.append(item)

        re_data['data'] = data_list
        re_data["success"] = True
        await self.finish(json.dumps(re_data, default=json_serial))


# 进货明细账本
class PurchaseDataDetailHandler(RedisHandler):
    @authenticated_async
    async def post(self, *args, **kwargs):
        re_data = {}
        data_list = []
        param = self.request.body.decode()
        param = json.loads(param)

        query_sort, expressions = await Conditional(param=param, order_type=[3, 4])
        sql = (OrderDetailAccount.select(OrderDetailAccount.signed_data,
                                         OrderDetailAccount.order_type,
                                         OrderDetailAccount.order_no.alias('order_no'),
                                         OrderDetailAccount.barcode.alias('product_barcode'),
                                         Product.name.alias('product_name'),
                                         ProductClassify.classify_no.alias('classify_no'),
                                         ProductClassify.classify_name.alias('classify_name'),
                                         StorehouseManagement.storehouse_no.alias('storehouse_no'),
                                         StorehouseManagement.storehouse_name.alias('storehouse_name'),
                                         Customer.uk_customer_no.alias('customer_no'),
                                         Customer.name.alias('customer_name'),
                                         Case(None, [((OrderDetailAccount.qty > 0), OrderDetailAccount.qty)], )
                                         .alias('add_qty'),
                                         Case(None, [((OrderDetailAccount.qty < 0), OrderDetailAccount.qty)], )
                                         .alias('reduce_qty'),
                                         OrderDetailAccount.discount_price,
                                         OrderDetailAccount.discount_total,
                                         OrderDetailAccount.cost_price,
                                         OrderDetailAccount.cost_total, )
               .join(OrderIndex, join_type=JOIN.LEFT_OUTER, on=(OrderIndex.order_no == OrderDetailAccount.order_no))
               .join(Product, join_type=JOIN.LEFT_OUTER, on=(Product.barcode == OrderDetailAccount.barcode))
               .join(ProductClassify, join_type=JOIN.LEFT_OUTER, on=(ProductClassify.id == Product.product_classify_id))
               .join(StorehouseManagement, join_type=JOIN.LEFT_OUTER,
                     on=(StorehouseManagement.id == OrderIndex.storehouse_id))
               .join(Customer, join_type=JOIN.LEFT_OUTER, on=(Customer.id == OrderDetailAccount.customer_id))
               .join(CustomerClassify, join_type=JOIN.LEFT_OUTER, on=(Customer.customer_classify ==
                                                                      CustomerClassify.id))
               .where(*expressions)
               .order_by(query_sort).dicts())
        data = await self.application.objects.execute(sql)
        for item in data:
            data_list.append(item)

        re_data['data'] = data_list
        re_data["success"] = True
        await self.finish(json.dumps(re_data, default=json_serial))
