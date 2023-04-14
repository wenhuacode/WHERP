import json

from WHERP.handler import RedisHandler
from apps.utils.mxform_decorators import authenticated_async
from apps.order.models.models import OrderIndex
from apps.customer.customer_handler.models import Customer, CustomerClassify
from apps.finance.subsidiary_ledger.models import SubsidiaryLedger
from peewee import JOIN, fn, Case, SQL
from apps.utils.util_func import json_serial
from apps.utils.query_conditional import Conditional


# 客户应收查询
class CustomerARAPQueryHandler(RedisHandler):
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
        if 'customer_name' in param['params']:
            if param['params']['customer_name'][1]['type'] == "customer_classify":
                pid_list = []
                data = await self.application.objects.execute(
                    CustomerClassify.select().where(
                        CustomerClassify.parent_path.contains(
                            param['params']['customer_name'][1]['customer_classify_id'])))
                for item in data:
                    pid_list.append(item.id)
                expressions.append(CustomerClassify.id.in_(pid_list))
            if param['params']['customer_name'][1]['type'] == "customer":
                expressions.append(SubsidiaryLedger.customer_id == param['params']['customer_name'][1]['customer_id'])

        node_id = param['params']['node_id'][0]
        classic = await self.application.objects.execute(CustomerClassify.select()
                                                         .where(CustomerClassify.parent_id == node_id))
        # 判断分类是否存在子节点
        if classic:
            expressions.append(SubsidiaryLedger.as_id.in_([38, 47]))
            base = (SubsidiaryLedger.select(fn.SUM(Case(None, [((SubsidiaryLedger.as_id == 38),
                                                                SubsidiaryLedger.amount)], 0)).alias('ar'),
                                            fn.SUM(Case(None, [((SubsidiaryLedger.as_id == 47),
                                                                SubsidiaryLedger.amount)], 0)).alias('ap'),
                                            CustomerClassify.parent_path.alias('parent_path'))
                    .join(Customer, join_type=JOIN.LEFT_OUTER, on=(Customer.id == SubsidiaryLedger.customer_id))
                    .join(CustomerClassify, join_type=JOIN.LEFT_OUTER,
                          on=(CustomerClassify.id == Customer.customer_classify))
                    .where(*expressions)
                    .group_by(Customer.id)
                    .cte('sl_account'))

            sql = (CustomerClassify.select(CustomerClassify.id,
                                           CustomerClassify.classify_no.alias("no"),
                                           CustomerClassify.classify_name.alias("name"),
                                           fn.SUM(Case(None, [(((base.c.ar - base.c.ap) > 0),
                                                               (base.c.ar - base.c.ap))], )).alias('ar'),
                                           fn.ABS(fn.SUM(Case(None, [(((base.c.ar - base.c.ap) < 0),
                                                                      (base.c.ar - base.c.ap))], ))).alias('ap'), )
                   .join(base, join_type=JOIN.LEFT_OUTER,
                         on=(base.c.parent_path.contains(CustomerClassify.parent_path)))
                   .where(CustomerClassify.parent_id == node_id)
                   .group_by(CustomerClassify.id)
                   .order_by(query_sort)
                   .dicts()
                   .with_cte(base))

            data = await self.application.objects.execute(sql)

        else:
            expressions.append(SubsidiaryLedger.as_id.in_([38, 47]))
            base = (Customer.select(Customer.uk_customer_no,
                                    fn.SUM(Case(None, [((SubsidiaryLedger.as_id == 38),
                                                        SubsidiaryLedger.amount)], 0)).alias('ar'),
                                    fn.SUM(Case(None, [((SubsidiaryLedger.as_id == 47),
                                                        SubsidiaryLedger.amount)], 0)).alias('ap'), )
                    .join(SubsidiaryLedger, join_type=JOIN.RIGHT_OUTER,
                          on=(Customer.id == SubsidiaryLedger.customer_id))
                    .join(CustomerClassify, join_type=JOIN.LEFT_OUTER,
                          on=(CustomerClassify.id == Customer.customer_classify))
                    .group_by(Customer.uk_customer_no)
                    .where(*expressions)
                    .cte('sl_account'))

            sql = (Customer.select(Customer.name.alias("name"),
                                   Customer.uk_customer_no.alias("no"),
                                   Customer.id.alias("customer_id"),
                                   fn.SUM(Case(None, [(((base.c.ar - base.c.ap) > 0), (base.c.ar - base.c.ap))],
                                               )).alias('ar'),
                                   fn.ABS(fn.SUM(Case(None, [(((base.c.ar - base.c.ap) < 0), (base.c.ar - base.c.ap))],
                                                      ))).alias('ap'), )
                   .join(base, join_type=JOIN.LEFT_OUTER, on=(Customer.uk_customer_no == base.c.uk_customer_no))
                   .group_by(Customer.id)
                   .where(Customer.customer_classify == node_id)
                   .order_by(query_sort)
                   .dicts()
                   .with_cte(base))

            data = await self.application.objects.execute(sql)

        for item in data:
            data_list.append(item)

        re_data['data'] = data_list
        re_data["success"] = True
        await self.finish(json.dumps(re_data, default=json_serial))


class CustomerARAPDetailHandler(RedisHandler):
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

        expressions = [SubsidiaryLedger.as_id.in_([38, 47]),
                       SubsidiaryLedger.amount > 0,
                       OrderIndex.signed_data.between(param['params']['startTime'],
                                                      param['params']['endTime'])]
        if 'customer_id' in param['params']:
            expressions.append(SubsidiaryLedger.customer_id == param['params']['customer_id'])

        base = (SubsidiaryLedger
                .select(SubsidiaryLedger.id.alias("id"),
                        SubsidiaryLedger.order_type.alias("order_type"),
                        SubsidiaryLedger.order_no.alias("order_no"),
                        Case(None, [((SubsidiaryLedger.as_id == 38), SubsidiaryLedger.amount)], 0).alias('ar_amount'),
                        Case(None, [((SubsidiaryLedger.as_id == 47), SubsidiaryLedger.amount)], 0).alias('ap_amount'),
                        )
                .where(*expressions)
                .join(OrderIndex, join_type=JOIN.LEFT_OUTER, on=(SubsidiaryLedger.order_no == OrderIndex.order_no))
                .cte('sl_account'))
        if param['params']['check_list'] == 1:
            sql = (SubsidiaryLedger
                   .select(SubsidiaryLedger.id,
                           SubsidiaryLedger.order_type.alias("order_type"),
                           OrderIndex.signed_data.alias("signed_data"),
                           OrderIndex.note.alias("note"),
                           base.c.order_no,
                           base.c.ar_amount.alias("add_amount"),
                           base.c.ap_amount.alias("sub_amount"),
                           fn.SUM(base.c.ar_amount - base.c.ap_amount).over(order_by=[SubsidiaryLedger.id]).alias(
                               'amount'),)
                   .join(base, join_type=JOIN.LEFT_OUTER, on=(base.c.id == SubsidiaryLedger.id))
                   .join(OrderIndex, join_type=JOIN.LEFT_OUTER, on=(SubsidiaryLedger.order_no == OrderIndex.order_no))
                   .where(*expressions)
                   .group_by(SubsidiaryLedger.id)
                   .order_by(query_sort)
                   .dicts()
                   .with_cte(base))
        else:
            sql = (SubsidiaryLedger
                   .select(SubsidiaryLedger.id,
                           SubsidiaryLedger.order_type.alias("order_type"),
                           OrderIndex.signed_data.alias("signed_data"),
                           OrderIndex.note.alias("note"),
                           base.c.order_no,
                           base.c.ar_amount.alias("sub_amount"),
                           base.c.ap_amount.alias("add_amount"),
                           fn.SUM(base.c.ap_amount - base.c.ar_amount).over(order_by=[SubsidiaryLedger.id]).alias(
                               'amount'), )
                   .join(base, join_type=JOIN.LEFT_OUTER, on=(base.c.id == SubsidiaryLedger.id))
                   .join(OrderIndex, join_type=JOIN.LEFT_OUTER, on=(SubsidiaryLedger.order_no == OrderIndex.order_no))
                   .where(*expressions)
                   .group_by(SubsidiaryLedger.id)
                   .order_by(query_sort)
                   .dicts()
                   .with_cte(base))

        data = await self.application.objects.execute(sql)
        for item in data:
            data_list.append(item)

        re_data['data'] = data_list
        re_data["success"] = True
        await self.finish(json.dumps(re_data, default=json_serial))
