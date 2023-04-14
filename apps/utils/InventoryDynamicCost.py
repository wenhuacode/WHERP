from apps.utils.round_dec import round_dec


# 动态成本计算 order_type
async def inventory_dynamic_cost(order_data, products):
    # 算出该种实时库存数量和实时库存金额
    total_qty = 0
    total_amount = 0.00
    for item in products:
        total_qty += int(item.qty)
        total_amount += float(item.total)
    # 算出最新成本单价 [(移动加权成本 * 实时库存数量) + (本次入库单价 * 本次入库数量)] ÷ (实时库存数量 + 本次入库数量)
    new_cost_price = round_dec((float(total_amount) + float(abs(order_data.discount_total))) /
                               (int(total_qty) + int(abs(order_data.qty))), 4)
    return new_cost_price


# 动态成本计算 成本调价单 order_type=1 是审核 order_type=2 是撤销
async def inventory_dynamic_cost_just(order_data, product, order_type):
    # 算出该种实时库存数量和实时库存金额
    total_amount = product.total
    if order_type == 1:
        # 如果库存为0
        if product.qty != 0:
            new_cost_price = round_dec((float(total_amount) - float(order_data.total) + float(order_data.discount_total)) /
                                       (int(product.qty)), 4)
        else:
            new_cost_price = order_data.discount_price
    else:
        if product.qty != 0:
            new_cost_price = round_dec((float(total_amount) + float(order_data.total) - float(order_data.discount_total)) /
                                       (int(product.qty)), 4)
        else:
            new_cost_price = product.cost_price
    return new_cost_price


# 单据撤销动态成本计算 order_type=1 为入库类单据撤销 order_type=2 = 出库类单据撤销
async def un_inventory_dynamic_cost(order_data,  product, products, order_type):
    # 算出退仓成本价格
    total_qty = 0
    total_amount = 0.00
    for item in products:
        total_qty += int(item.qty)
        total_amount += float(item.total)
    if order_type == 1:
        # 判断库存是否为0， 避免除0操作
        if int(total_qty) - int(order_data.qty) == 0:
            new_cost_price = product.cost_price
        else:
            new_cost_price = round_dec((float(total_amount) - float(order_data.discount_total)) /
                                       (int(total_qty) - int(order_data.qty)), 4)
    # order_type == 2
    else:
        # 如果库存为0
        if total_qty == 0:
            new_cost_price = order_data.cost_price
        else:
            # new_cost_price = product.cost_price
            new_cost_price = round_dec((float(total_amount) + float(order_data.cost_total)) /
                                       (int(total_qty) + int(order_data.qty)), 4)
    return new_cost_price
