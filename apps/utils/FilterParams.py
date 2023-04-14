import json

from wherp.settings import OP_MAP, pw
from wherp.settings import objects


class Filter:
    """
        整理分页， 查询参数， 以及排序
    """
    def __init__(self, args):
        self.args = args
        self.params = {}
        for key in self.args:
            if key == 'signed_data[]':
                self.params['signed_data'] = self.args[key]
            if key != "current" and key != "pageSize" and key != "signed_data[]":
                self.params[key] = self.args[key]

    async def order_filter(self, model=None, model2=None, business_type=None):
        expressions = []
        for key, value in self.params.items():
            if value is not None:
                if key == "address":
                    # 地址
                    data = {}
                    if len(value) >= 1:
                        data.update({"province_id": value[0]})
                    if len(value) >= 2:
                        data.update({"city_id": value[1]})
                    if len(value) == 3:
                        data.update({"district_id": value[2]})
                    for ad_key, ad_value in data.items():
                        expressions.append(pw.Expression(getattr(model, ad_key), OP_MAP[ad_key], ad_value))
                elif OP_MAP[key] == pw.OP.ILIKE:
                    if key == "customer_name":
                        # 解决客户
                        value = pw.Expression('%', pw.OP.CONCAT, pw.Expression(value, pw.OP.CONCAT, '%'))
                        expressions.append(pw.Expression(getattr(model2, "name"), OP_MAP[key], value))
                        break
                    # 解决近似查询
                    value = pw.Expression('%', pw.OP.CONCAT, pw.Expression(value, pw.OP.CONCAT, '%'))
                    expressions.append(pw.Expression(getattr(model, key), OP_MAP[key], value))
                elif key == "signed_data":
                    # 解决时间区间
                    expressions.append(pw.Expression(getattr(model, key),
                                                     OP_MAP[key], pw.NodeList((value[0], pw.SQL('AND'), value[1]))))
                else:
                    expressions.append(pw.Expression(getattr(model, key), OP_MAP[key], *value))
        if business_type == 2:
            expressions.append(pw.Expression(getattr(model, "order_state"), pw.OP.IN, [2, 3]))
        else:
            expressions.append(pw.Expression(getattr(model, "order_state"), pw.OP.IN, [0, 1, 4]))
        return expressions

    async def product_inventory_query(self, model=None, model2=None, model3=None):
        expressions = []
        for key, value in self.params.items():
            if value is not None:
                if key == "storehouse_id":
                    expressions.append(pw.Expression(getattr(model2, "id"), OP_MAP[key], *value))
                    # expressions.append(pw.Expression(getattr(model3, "qty"), pw.OP.GT, 0))
                elif OP_MAP[key] == pw.OP.ILIKE:
                    # 解决近似查询
                    value = pw.Expression('%', pw.OP.CONCAT, pw.Expression(value, pw.OP.CONCAT, '%'))
                    expressions.append(pw.Expression(getattr(model, key), OP_MAP[key], value))
                else:
                    expressions.append(pw.Expression(getattr(model, key), OP_MAP[key], *value))
        return expressions

    async def customer_filter(self, model=None, model2=None):
        expressions = []
        for key, value in self.params.items():
            if value is not None:
                if key == "customer_classify":
                    customers_id = []
                    data = await objects.get(model2, id=int(value[0]))
                    path = await objects.execute(model2.select().where(model2.parent_path.contains(data.parent_path)))
                    for item in path:
                        customers_id.append(item.id)
                    expressions.append(pw.Expression(getattr(model, "customer_classify"), OP_MAP[key], customers_id))
                elif key == "address":
                    # 地址
                    data = {}
                    if len(value) >= 1:
                        data.update({"province_id": value[0]})
                    if len(value) >= 2:
                        data.update({"city_id": value[1]})
                    if len(value) == 3:
                        data.update({"district_id": value[2]})
                    for ad_key, ad_value in data.items():
                        expressions.append(pw.Expression(getattr(model, ad_key), OP_MAP[ad_key], ad_value))
                elif OP_MAP[key] == pw.OP.ILIKE:
                    # 解决近似查询
                    value = pw.Expression('%', pw.OP.CONCAT, pw.Expression(value, pw.OP.CONCAT, '%'))
                    expressions.append(pw.Expression(getattr(model, key), OP_MAP[key], value))
                else:
                    expressions.append(pw.Expression(getattr(model, key), OP_MAP[key], *value))
        return expressions
