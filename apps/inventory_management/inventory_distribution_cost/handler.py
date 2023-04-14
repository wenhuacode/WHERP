import json
from datetime import datetime

from wherp.handler import RedisHandler
from apps.utils.mxform_decorators import authenticated_async
from apps.inventory_management.inventory_distribution_cost.models import *
from apps.inventory_management.inventory_distribution_cost.forms import *
from apps.product.product_handler.models import Product
from apps.utils.util_func import json_serial
from playhouse.shortcuts import model_to_dict
from loguru import logger


async def query_inventory_list(param_datas):
    queryList = []

    if (storehouse_name := param_datas.get("storehouse_name", None)) is not None:
        queryList.append(IrProperty.storehouse_id == (int(storehouse_name)))
    if (barcode := param_datas.get("barcode", None)) is not None:
        queryList.append(IrProperty.barcode.contains(str(barcode)))
    if (product_name := param_datas.get("product_name", None)) is not None:
        queryList.append(Product.name.contains(str(product_name)))

    query = queryList[0]
    for data in queryList[1:]:
        query = query & data
    query = (IrProperty
             .select(IrProperty, StorehouseManagement.storehouse_name, Product.name)
             .join(StorehouseManagement, join_type=JOIN.LEFT_OUTER,
                   on=(IrProperty.storehouse_id == StorehouseManagement.id), attr='sname')
             .switch(IrProperty)
             .join(Product, join_type=JOIN.LEFT_OUTER, on=(IrProperty.barcode == Product.barcode), attr='pname')
             .where(query, IrProperty.qty >= 0))
    return query


class JstInventoryQueryHandler(RedisHandler):
    @authenticated_async
    async def get(self, product_id, *args, **kwargs):
        re_data = {}


# 库存成本表
class InventoryQueryHandler(RedisHandler):
    @authenticated_async
    @logger.catch
    async def get(self, *args, **kwargs):
        re_data = {}
        datas = []

        current = self.get_argument("current", None)
        pageSize = self.get_argument("pageSize", None)
        add_time = self.get_argument("add_time", None)
        modified = self.get_argument("modified", None)

        param_data = {}
        param_datas = {}
        # 遍历参数
        for key in self.request.arguments:
            # 过滤基本参数
            if key != "current" and key != "pageSize" and key != "add_time":
                param_data[key] = self.get_argument(key)
        # 过滤空值
        for key, value in param_data.items():
            if len(value) != 0:
                param_datas.update({key: value})

        param = {'storehouse_name', 'barcode', 'product_name'}

        # 处理排序
        if add_time == 'ascend':
            query_sort = IrProperty.add_time.asc()
        elif add_time == 'descend':
            query_sort = IrProperty.add_time.desc()
        elif modified == 'ascend':
            query_sort = IrProperty.modified.asc()
        elif modified == 'descend':
            query_sort = IrProperty.modified.desc()
        else:
            query_sort = IrProperty.add_time.desc()
        # 没有参数就返回全部数据并分页
        if all(v not in param_datas for v in param):
            query = (IrProperty.select(IrProperty, StorehouseManagement.storehouse_name, Product.name)
                     .join(StorehouseManagement, join_type=JOIN.LEFT_OUTER,
                           on=(IrProperty.storehouse_id == StorehouseManagement.id), attr='sname')
                     .switch(IrProperty)
                     .join(Product, join_type=JOIN.LEFT_OUTER, on=(IrProperty.barcode == Product.barcode), attr='pname')
                     .where(IrProperty.qty >= 0))
            storehouse = await self.application.objects.execute(query
                                                                .order_by(query_sort)
                                                                .paginate(int(current), int(pageSize)))
            total = await self.application.objects.count(query)

            for item in storehouse:
                data = (model_to_dict(item))
                data['storehouse_name'] = item.sname.storehouse_name
                data['product_name'] = item.pname.name
                datas.append(data)
            re_data["total"] = total
            re_data["page"] = current
            re_data["data"] = datas
            re_data["success"] = True
        else:
            query = await query_inventory_list(param_datas)
            storehouse = await self.application.objects.execute(query
                                                                .order_by(query_sort)
                                                                .paginate(int(current), int(pageSize)))
            total = await self.application.objects.count(query)
            for item in storehouse:
                data = (model_to_dict(item))
                data['storehouse_name'] = item.sname.storehouse_name
                data['product_name'] = item.pname.name
                datas.append(data)
            re_data["total"] = total
            re_data["page"] = current
            re_data["data"] = datas
            re_data["success"] = True
        await self.finish(json.dumps(re_data, default=json_serial))


class StorehouseManagementHandler(RedisHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        # 查询仓库列表
        re_data = {}
        data = []
        storehouse = await self.application.objects.execute(StorehouseManagement.select())
        for item in storehouse:
            data.append(model_to_dict(item))

        re_data["data"] = data
        re_data["success"] = True
        await self.finish(json.dumps(re_data, default=json_serial))

    @authenticated_async
    async def post(self, *args, **kwargs):
        # 新增仓库
        re_data = {}
        param = self.request.body.decode("utf8")
        param = json.loads(param)
        form = CreateStorehouseManagement.from_json(param)
        if form.validate():
            try:
                await self.application.objects.get(StorehouseManagement, storehouse_no=form.storehouse_no.data)
                re_data["success"] = False
                re_data["errorMessage"] = '仓库编号重复'
            except StorehouseManagement.DoesNotExist as e:
                await self.application.objects.create(StorehouseManagement,
                                                      storehouse_no=form.storehouse_no.data,
                                                      storehouse_name=form.storehouse_name.data,
                                                      employee_id=form.employee_id.data,
                                                      employee=form.employee.data,
                                                      is_stop=form.is_stop.data,
                                                      note=form.note.data,
                                                      jst_storehouse_no=form.jst_storehouse_no.data,
                                                      create_user_id=self.current_user.id,
                                                      create_user=self.current_user.name)
                re_data["success"] = True
                re_data["errorMessage"] = '数据保存成功'
        else:
            for field in form.errors:
                re_data["errorMessage"] = form.errors[field][0]
        await self.finish(re_data)

    @authenticated_async
    async def patch(self, Storehouse_id, *args, **kwargs):
        # 更新仓库信息, 不修改仓库编号
        re_data = {}
        param = self.request.body.decode("utf8")
        param = json.loads(param)
        form = CreateStorehouseManagement.from_json(param)
        try:
            storehouse = await self.application.objects.get(StorehouseManagement, id=int(Storehouse_id))
            storehouse.storehouse_name = form.storehouse_name.data
            storehouse.employee_id = form.employee_id.data
            storehouse.employee = form.employee.data
            storehouse.is_stop = form.is_stop.data
            storehouse.note = form.note.data
            storehouse.jst_storehouse_no = form.jst_storehouse_no.data
            storehouse.modified_id = self.current_user.id
            storehouse.modified_name = self.current_user.name
            storehouse.modified = datetime.now()
            await self.application.objects.update(storehouse)
            re_data["success"] = True
            re_data["errorMessage"] = '仓库信息更新成功'
        except StorehouseManagement.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '仓库不存在'
        await self.finish(re_data)

    @authenticated_async
    async def delete(self, Storehouse_id, *args, **kwargs):
        # 删除仓库
        re_data = {}
        try:
            await self.application.objects.get(StorehouseManagement, id=int(Storehouse_id))
            await self.application.objects.execute(StorehouseManagement.delete().where(id=int(Storehouse_id)))

            re_data["success"] = False
            re_data["errorMessage"] = '仓库删除成功'
        except StorehouseManagement.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '仓库不存在'
        await self.finish(re_data)
