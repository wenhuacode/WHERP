from peewee import SQL
from apps.order.models.models import OrderDetailAccount
from apps.customer.customer_handler.models import CustomerClassify
from apps.product.product_handler.models import ProductClassify
from WHERP.settings import objects


async def Conditional(param, order_type: list):
    # 处理排序
    query_sort = None
    for key, value in param['sort'].items():
        if value == 'descend':
            query_sort = SQL(key).desc()
        else:
            query_sort = SQL(key).asc()
    # 处理条件查询
    expressions = [OrderDetailAccount.order_type.in_(order_type),
                   OrderDetailAccount.signed_data.between(param['params']['startTime'],
                                                          param['params']['endTime'])]
    if 'employee' in param['params']:
        expressions.append(OrderDetailAccount.employee_id == param['params']['employee'])
    if 'storehouse' in param['params']:
        expressions.append(OrderDetailAccount.storehouse_id == param['params']['storehouse'])
    if 'barcode' in param['params']:
        expressions.append(OrderDetailAccount.barcode == param['params']['barcode'])
    if 'customer_name' in param['params']:
        if param['params']['customer_name'][1]['type'] == "customer_classify":
            pid_list = []
            data = await objects.execute(
                CustomerClassify.select().where(
                    CustomerClassify.parent_path.contains(param['params']['customer_name'][1]['customer_classify_id'])))
            for item in data:
                pid_list.append(item.id)
            expressions.append(CustomerClassify.id.in_(pid_list))
        if param['params']['customer_name'][1]['type'] == "customer":
            expressions.append(OrderDetailAccount.customer_id == param['params']['customer_name'][1]['customer_id'])
    if 'customer_classify_id' in param['params']:
        pid_list = []
        data = await objects.execute(
            CustomerClassify.select().where(
                CustomerClassify.parent_path.contains(param['params']['customer_classify_id'])))
        for item in data:
            pid_list.append(item.id)
        expressions.append(CustomerClassify.id.in_(pid_list))
    if 'customer_id' in param['params']:
        expressions.append(OrderDetailAccount.customer_id == param['params']['customer_id'])
    if 'product_name' in param['params']:
        if param['params']['product_name'][1]['type'] == "product_classify":
            pid_list = []
            data = await objects.execute(
                ProductClassify.select().where(
                    ProductClassify.parent_path.contains(param['params']['product_name'][1]['product_classify_id'])))
            for item in data:
                pid_list.append(item.id)
            expressions.append(ProductClassify.id.in_(pid_list))
        if param['params']['product_name'][1]['type'] == "product":
            expressions.append(OrderDetailAccount.barcode == param['params']['product_name'][1]['product_id'])
    if 'product_id' in param['params']:
        pid_list = []
        data = await objects.execute(
            ProductClassify.select().where(
                ProductClassify.parent_path.contains(param['params']['product_id'])))
        for item in data:
            pid_list.append(item.id)
        expressions.append(ProductClassify.id.in_(pid_list))
    if 'product_id' in param['params']:
        expressions.append(OrderDetailAccount.barcode == param['params']['product_id'])

    return query_sort, expressions
