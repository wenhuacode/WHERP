from datetime import datetime

from apps.utils.round_dec import round_dec
from apps.utils.InventoryDynamicCost import inventory_dynamic_cost, un_inventory_dynamic_cost, inventory_dynamic_cost_just
from peewee import *
from apps.utils.Error import InventoryError
from apps.order.models.models import OrderDetailAccount, OrderDetail, SubsidiaryLedger
from apps.inventory_management.inventory_distribution_cost.models import IrProperty, StorehouseManagement
from wherp.settings import objects
from playhouse.shortcuts import model_to_dict

class OutInventoryCheck:
    def __init__(self, order=None, order_detail=None, current_user_id=None):
        self.order = order
        self.order_detail = order_detail
        self.current_user_id = current_user_id

    # 出库单据审核
    async def out_check_order(self, txn=None, re_data=None, rs_storehouse=None):
        """
        出库订单审核
        :return:
        """
        # 更改订单状态, 初始化总成本
        self.order.order_state = 2
        order_cost_total = 0.00
        order_detail_list = []
        if rs_storehouse:
            self.order.storehouse_id = rs_storehouse
        try:
            # 检查仓库是否存在
            await objects.get(StorehouseManagement, id=self.order.storehouse_id)
            for data in self.order_detail:
                # 查询商品库存数量
                goods_inventory = await objects.get(IrProperty, barcode=data.barcode, storehouse_id=self.order.storehouse_id)
                # 判断商品库存数量
                if (goods_inventory.qty - data.qty) < 0:
                    await txn.rollback()
                    raise InventoryError(f"{goods_inventory.barcode}:库存不足")
                # 更新库存数量
                await objects.execute(IrProperty
                                      .update(qty=goods_inventory.qty - int(data.qty))
                                      .where((IrProperty.barcode == data.barcode) &
                                             (IrProperty.storehouse_id == self.order.storehouse_id)))
                # 更新其余仓库同种商品成本数据
                await objects.execute(IrProperty
                                      .update(cost_price=goods_inventory.cost_price,
                                              total=fn.ROUND(goods_inventory.cost_price * IrProperty.qty, 2))
                                      .where(IrProperty.barcode == data.barcode))
                # 预先处理订单正式表数据
                order_detail = OrderDetailAccount()
                order_detail.order_no = data.order_no
                order_detail.order_type = data.order_type
                order_detail.storehouse_id = self.order.storehouse_id
                order_detail.customer_id = self.order.customer_id
                order_detail.employee_id = self.order.employee_id
                order_detail.signed_data = datetime.now().strftime("%Y%m%d")
                order_detail.order_state = self.order.order_state
                order_detail.barcode = data.barcode
                order_detail.qty = -data.qty
                order_detail.box_qty = -data.box_qty
                order_detail.box_rules = data.box_rules
                order_detail.discount = data.discount
                order_detail.discount_price = data.discount_price
                order_detail.discount_total = -data.discount_total
                order_detail.cost_price = goods_inventory.cost_price
                order_detail.cost_total = -round_dec((float(goods_inventory.cost_price) * int(data.qty)), 2)
                order_detail.price = data.price
                order_detail.total = -data.total
                order_detail.is_free_gift = data.is_free_gift
                order_detail.note = data.note
                order_detail.checked_user_id = self.current_user_id

                order_detail_list.append(model_to_dict(order_detail))

                # 计算订单出库成本金额 存入账本数据
                order_cost_total = order_cost_total + (float(data.qty) * float(goods_inventory.cost_price))
            # 批量插入账本数据
            await objects.execute(OrderDetailAccount.insert_many(order_detail_list))
            # 更新原有单据状态
            await objects.update(self.order)

            re_data["success"] = True
            re_data["errorMessage"] = '订单审核成功'
        except StorehouseManagement.DoesNotExist as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = '仓库不存在, 请检查仓库信息'
        except InventoryError as e:
            re_data["success"] = False
            re_data["errorMessage"] = f'审核失败: {e}'
        except IrProperty.DoesNotExist as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = '当前仓库无此商品, 请检查订单'
        except Exception as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = f'发生其他错误: {e}'

        return order_cost_total, re_data

    # 出库单据红冲
    async def un_out_check_order(self, txn=None, re_data=None, rs_storehouse=None):
        """
        出库订单撤销
        """
        # 更改订单状态
        self.order.order_state = 3
        ir_property_list = []
        order_detail_list = []
        if rs_storehouse:
            self.order.storehouse_id = rs_storehouse
        try:
            # 检查仓库是否存在
            await objects.get(StorehouseManagement, id=self.order.storehouse_id)
            for data in self.order_detail:
                # 获取该种商品在仓库内所有库存信息
                Inventory = await objects.execute(IrProperty.select().where(IrProperty.barcode == data.barcode))
                if Inventory:
                    # 入库有库存, 算出最新成本金额
                    cost_price = await inventory_dynamic_cost(data, Inventory)
                    # 将商品库存存入字典
                    inventory = {}
                    for item in Inventory:
                        inventory[item.storehouse_id] = {item.barcode: item.qty}
                    # 判断当前仓库是否存在商品
                    if data.barcode in inventory[data.storehouse_id]:
                        # 更新库存
                        await objects.execute(IrProperty
                                              .update(qty=inventory[data.storehouse_id][data.barcode] + int(-data.qty))
                                              .where((IrProperty.barcode == data.barcode) &
                                                     (IrProperty.storehouse_id == data.storehouse_id)))
                    else:
                        # 创建最新成本表商品数据
                        ir_property = IrProperty()
                        ir_property.barcode = data.barcode
                        ir_property.storehouse_id = data.storehouse_id
                        ir_property.qty = -data.qty
                        ir_property.cost_price = data.cost_price
                        ir_property.total = round_dec(float(cost_price) * int(-data.qty), 2)

                        ir_property_list.append(model_to_dict(ir_property))

                    # 更新其余仓库同种商品成本数据
                    await objects.execute(IrProperty
                                          .update(cost_price=cost_price, total=fn.ROUND(cost_price * IrProperty.qty, 2))
                                          .where(IrProperty.barcode == data.barcode))

                else:
                    # 设置初始成本为库存
                    cost_price = data.discount_price
                    # 如果不存在就以初次入库单价为成本
                    ir_property = IrProperty()
                    ir_property.barcode = data.barcode
                    ir_property.storehouse_id = data.storehouse_id
                    ir_property.qty = -data.qty
                    ir_property.cost_price = data.discount_price
                    ir_property.total = (int(-data.qty) * float(data.discount_price))

                    ir_property_list.append(model_to_dict(ir_property))

                # 插入销售订单正式表
                order_detail = OrderDetailAccount()
                order_detail.order_no = data.order_no
                order_detail.order_type = data.order_type
                order_detail.storehouse_id = self.order.storehouse_id
                order_detail.customer_id = self.order.customer_id
                order_detail.employee_id = self.order.employee_id
                order_detail.signed_data = datetime.now().strftime("%Y%m%d")
                order_detail.order_state = self.order.order_state
                order_detail.barcode = data.barcode
                order_detail.qty = -data.qty
                order_detail.box_qty = -data.box_qty
                order_detail.box_rules = data.box_rules
                order_detail.discount = data.discount
                order_detail.discount_price = data.discount_price
                order_detail.discount_total = -data.discount_total
                order_detail.cost_price = data.cost_price
                order_detail.cost_total = -round_dec((float(cost_price) * int(data.qty)), 2)
                order_detail.price = data.price
                order_detail.total = -data.total
                order_detail.is_free_gift = data.is_free_gift
                order_detail.note = data.note
                order_detail.checked_user_id = self.current_user_id

                order_detail_list.append(model_to_dict(order_detail))

            # 存入库存
            if ir_property_list:
                await objects.execute(IrProperty.insert_many(ir_property_list))
            # 存入账本
            await objects.execute(OrderDetailAccount.insert_many(order_detail_list))
            # 更新原有单据状态
            await objects.update(self.order)

            re_data["success"] = True
            re_data["errorMessage"] = '审核成功'
        except StorehouseManagement.DoesNotExist as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = '仓库不存在, 请检查仓库信息'
        except Exception as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = f'发生其他错误: {e}'

        return re_data

    # 入库单据审核
    async def in_check_order(self, txn=None, re_data=None, rs_storehouse=None):
        """
        入库订单审核  包含出库撤销
        :return:
        """
        # 更改订单状态
        self.order.order_state = 2
        order_cost_total = 0.00
        ir_property_list = []
        order_detail_list = []
        if rs_storehouse:
            self.order.storehouse_id = rs_storehouse
        try:
            # 检查仓库是否存在
            await objects.get(StorehouseManagement, id=self.order.storehouse_id)
            for data in self.order_detail:
                # 获取该种商品在仓库内所有库存信息
                Inventory = await objects.execute(IrProperty.select().where(IrProperty.barcode == data.barcode))
                if Inventory:
                    # 入库有库存, 算出最新成本金额
                    cost_price = await inventory_dynamic_cost(data, Inventory)
                    # 将商品库存存入字典
                    inventory = {}
                    for item in Inventory:
                        inventory[item.storehouse_id] = {item.barcode: item.qty}
                    # 判断当前仓库是否存在商品
                    if self.order.storehouse_id in inventory:
                        # 更新库存 注意运算符优先顺序
                        await objects.execute(IrProperty
                                              .update(qty=inventory[self.order.storehouse_id][data.barcode] + int(data.qty))
                                              .where((IrProperty.barcode == data.barcode) &
                                                     (IrProperty.storehouse_id == self.order.storehouse_id)))
                    else:
                        # 创建最新成本表商品数据
                        ir_property = IrProperty()
                        ir_property.barcode = data.barcode
                        ir_property.storehouse_id = self.order.storehouse_id
                        ir_property.qty = data.qty
                        ir_property.cost_price = cost_price
                        ir_property.total = round_dec(float(cost_price) * int(data.qty), 2)

                        ir_property_list.append(model_to_dict(ir_property))

                    # 更新其余仓库同种商品成本数据
                    await objects.execute(IrProperty
                                          .update(cost_price=cost_price, total=fn.ROUND(cost_price * IrProperty.qty, 2))
                                          .where(IrProperty.barcode == data.barcode))

                    # 计算订单出库成本金额 存入账本数据
                    order_cost_total = order_cost_total + (float(data.qty) * float(cost_price))
                else:
                    # 设置初始成本为库存
                    cost_price = data.discount_price
                    # 如果不存在就以初次入库单价为成本
                    ir_property = IrProperty()
                    ir_property.barcode = data.barcode
                    ir_property.storehouse_id = self.order.storehouse_id
                    ir_property.qty = data.qty
                    ir_property.cost_price = data.discount_price
                    ir_property.total = (float(data.qty) * float(data.discount_price))

                    ir_property_list.append(model_to_dict(ir_property))

                    # 计算订单出库成本金额 存入账本数据
                    order_cost_total = order_cost_total + (float(data.qty) * float(cost_price))
                # 插入销售订单正式表
                order_detail = OrderDetailAccount()
                order_detail.order_no = data.order_no
                order_detail.order_type = data.order_type
                order_detail.storehouse_id = self.order.storehouse_id
                order_detail.customer_id = self.order.customer_id
                order_detail.employee_id = self.order.employee_id
                order_detail.signed_data = datetime.now().strftime("%Y%m%d")
                order_detail.order_state = self.order.order_state
                order_detail.barcode = data.barcode
                order_detail.qty = data.qty
                order_detail.box_qty = data.box_qty
                order_detail.box_rules = data.box_rules
                order_detail.discount = data.discount
                order_detail.discount_price = data.discount_price
                order_detail.discount_total = data.discount_total
                order_detail.cost_price = cost_price
                order_detail.cost_total = round_dec((float(cost_price) * int(data.qty)), 2)
                order_detail.price = data.price
                order_detail.total = data.total
                order_detail.is_free_gift = data.is_free_gift
                order_detail.note = data.note
                order_detail.checked_user_id = self.current_user_id

                order_detail_list.append(model_to_dict(order_detail))

            # 存入库存
            if ir_property_list:
                await objects.execute(IrProperty.insert_many(ir_property_list))
            # 存入账本
            await objects.execute(OrderDetailAccount.insert_many(order_detail_list))
            # 更新原有单据状态
            await objects.update(self.order)

            re_data["success"] = True
            re_data["errorMessage"] = '审核成功'
        except StorehouseManagement.DoesNotExist as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = '仓库不存在, 请检查仓库信息'
        except Exception as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = f'发生其他错误: {e}'

        return order_cost_total, re_data

    # 入库单据红冲
    async def un_in_check_order(self, txn=None, re_data=None, rs_storehouse=None):
        """
        入库订单红冲
        """
        # 更改订单状态, 初始化总成本
        self.order.order_state = 3
        order_detail_list = []
        if rs_storehouse:
            self.order.storehouse_id = rs_storehouse
        try:
            # 检查仓库是否存在
            await objects.get(StorehouseManagement, id=self.order.storehouse_id)
            for data in self.order_detail:
                # 查询商品库存数量
                goods_inventory = await objects.get(IrProperty, barcode=data.barcode,
                                                    storehouse_id=self.order.storehouse_id)
                # 判断商品库存数量
                if (goods_inventory.qty - data.qty) < 0:
                    await txn.rollback()
                    raise InventoryError(f"{goods_inventory.barcode}:库存不足")
                # 更新库存数量
                await objects.execute(IrProperty
                                      .update(qty=goods_inventory.qty - int(data.qty))
                                      .where((IrProperty.barcode == data.barcode) &
                                             (IrProperty.storehouse_id == self.order.storehouse_id)))
                # 更新其余仓库同种商品成本数据
                await objects.execute(IrProperty
                                      .update(cost_price=goods_inventory.cost_price,
                                              total=fn.ROUND(goods_inventory.cost_price * IrProperty.qty, 2))
                                      .where(IrProperty.barcode == data.barcode))
                # 预先处理订单正式表数据
                order_detail = OrderDetailAccount()
                order_detail.order_no = data.order_no
                order_detail.order_type = data.order_type
                order_detail.storehouse_id = self.order.storehouse_id
                order_detail.customer_id = self.order.customer_id
                order_detail.employee_id = self.order.employee_id
                order_detail.signed_data = datetime.now().strftime("%Y%m%d")
                order_detail.order_state = self.order.order_state
                order_detail.barcode = data.barcode
                order_detail.qty = -data.qty
                order_detail.box_qty = -data.box_qty
                order_detail.box_rules = data.box_rules
                order_detail.discount = data.discount
                order_detail.discount_price = data.discount_price
                order_detail.discount_total = -data.discount_total
                order_detail.cost_price = goods_inventory.cost_price
                order_detail.cost_total = -round_dec((float(goods_inventory.cost_price) * int(data.qty)), 2)
                order_detail.price = data.price
                order_detail.total = -data.total
                order_detail.is_free_gift = data.is_free_gift
                order_detail.note = data.note
                order_detail.checked_user_id = self.current_user_id

                order_detail_list.append(model_to_dict(order_detail))

            # 批量插入账本数据
            await objects.execute(OrderDetailAccount.insert_many(order_detail_list))
            # 更新原有单据状态
            await objects.update(self.order)

            re_data["success"] = True
            re_data["errorMessage"] = '订单审核成功'
        except StorehouseManagement.DoesNotExist as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = '仓库不存在, 请检查仓库信息'
        except InventoryError as e:
            re_data["success"] = False
            re_data["errorMessage"] = f'审核失败: {e}'
        except IrProperty.DoesNotExist as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = '当前仓库无此商品, 请检查订单'
        except Exception as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = f'发生其他错误: {e}'

        return re_data

    # 成本调整单审核
    async def check_cost_order(self, txn=None, re_data=None):
        self.order.order_state = 2
        order_cost_total = 0.00
        after_cost_amount = 0.00
        try:
            for data in self.order_detail:
                # 检查当前订单商品库存
                goods_inventory = await objects.get(IrProperty, barcode=data.barcode, storehouse_id=self.order.storehouse_id)
                # 判断商品库存数量
                if (goods_inventory.qty - data.qty) < 0:
                    await txn.rollback()
                    raise InventoryError('调整商品库存不足, 请检查库存')
                # 成本金额
                order_cost_total = order_cost_total + (float(data.qty) * float(goods_inventory.cost_price))
                # 算出最新成本金额和数量, 总金额
                goods_inventory.cost_price = await inventory_dynamic_cost_just(data, goods_inventory, 1)
                # 计算之后成本金额
                after_cost_amount = after_cost_amount + float(data.discount_total)
                goods_inventory.total = round_dec(float(goods_inventory.cost_price) * (int(goods_inventory.qty)), 2)
                # 更新库存成本表
                await objects.update(goods_inventory)

            # 更新原有单据状态
            await objects.update(self.order)
            re_data["success"] = True
            re_data["errorMessage"] = '审核成功'
        except IrProperty.DoesNotExist as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = '当前仓库中无此商品'
        except InventoryError as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = e
        except Exception as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = f'发生其他错误: {e}'

        return order_cost_total, after_cost_amount, re_data

    # 成本调整单红冲
    async def un_check_cost_order(self, txn=None, re_data=None):
        self.order.order_state = 3
        order_cost_total = 0.00
        try:
            for data in self.order_detail:
                # 检查当前订单商品库存
                goods_inventory = await objects.get(IrProperty, barcode=data.barcode,
                                                    storehouse_id=self.order.storehouse_id)
                # 判断商品库存数量
                if (goods_inventory.qty - data.qty) < 0:
                    await txn.rollback()
                    raise InventoryError('调整商品库存不足, 请检查库存')
                # 算出最新成本金额和数量, 总金额
                goods_inventory.cost_price = await inventory_dynamic_cost_just(data, goods_inventory, 2)
                # 计算之后成本金额
                goods_inventory.total = round_dec(float(goods_inventory.cost_price) * (int(goods_inventory.qty)), 2)
                # 更新库存成本表
                await objects.update(goods_inventory)

            # 更新原有单据状态
            await objects.update(self.order)
            re_data["success"] = True
            re_data["errorMessage"] = '审核成功'
        except IrProperty.DoesNotExist as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = '当前仓库中无此商品'
        except InventoryError as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = e
        except Exception as e:
            await txn.rollback()
            re_data["success"] = False
            re_data["errorMessage"] = f'发生其他错误: {e}'

        return order_cost_total, re_data

