from apps.utils.value_dispatch import value_dispatch

queryList = []


@value_dispatch
def get_query_param(param, model):
    return model


@get_query_param.register("order_type")
def param_order_type(param, model):
    queryList.append(model.order_type == str(param))


def query_params(param_datas: dict, model):

    for k, v in param_datas.items():
        discount = get_query_param(k)
        queryList.append(discount)

    query = queryList[0]
    for data in queryList[1:]:
        query = query & data
    query = model.select().where(query)
    return query
