import copy
import json
import os
import uuid
from datetime import datetime

import aiofiles

from wherp.handler import RedisHandler
from wherp.settings import database
from apps.utils.mxform_decorators import authenticated_async
from apps.utils.FindMenu import find_menu
from apps.product.product_handler.models import *
from apps.product.product_handler.forms import *
from apps.inventory_management.inventory_distribution_cost.models import IrProperty
from apps.utils.util_func import json_serial
from playhouse.shortcuts import model_to_dict


async def query_product_list(param_datas):
    queryList = []

    if (product_no := param_datas.get("product_no", None)) is not None:
        queryList.append(Product.product_no.contains(str(product_no)))
    if (name := param_datas.get("name", None)) is not None:
        queryList.append(Product.name.contains(str(name)))
    if (barcode := param_datas.get("barcode", None)) is not None:
        queryList.append(Product.barcode.contains(str(barcode)))
    if (product_classify_id := param_datas.get("product_classify_id", None)) is not None:
        queryList.append(Product.product_classify_path.contains(str(product_classify_id)))
    if (supplier_id := param_datas.get("supplier_id", None)) is not None:
        queryList.append(Product.supplier_id == str(supplier_id))
    if (is_stop := param_datas.get("is_stop", None)) is not None:
        queryList.append(Product.is_stop == str(is_stop))

    query = queryList[0]
    for data in queryList[1:]:
        query = query & data
    query = Product.select().where(query)
    return query


async def Conditional(param):
    # 处理排序
    query_sort = None
    for key, value in param['sort'].items():
        if value == 'descend':
            query_sort = SQL(key).desc()
        else:
            query_sort = SQL(key).asc()

    # 处理条件查询
    expressions = []
    if 'product_name' in param['params']:
        expressions.append(Product.name.contains(param['params']['product_name']))
    if 'barcode' in param['params']:
        expressions.append(Product.barcode.contains(param['params']['barcode']))
    if 'product_id' in param['params']:
        expressions.append(Product.id == param['params']['product_id'])
    if 'product_no' in param['params']:
        expressions.append(Product.product_no.contains(param['params']['product_no']))

    return query_sort, expressions


class BatchUpdateEditProductHandler(RedisHandler):
    @authenticated_async
    async def post(self, *args, **kwargs):
        re_data = {}
        param = self.request.body.decode()
        param = json.loads(param)
        form = BatchUpdateProductForm.from_json(param)
        if form.validate():
            try:
                await self.application.objects.get(ProductClassify, id=form.classify.data)
                data = await self.application.objects.execute(Product
                                                              .update(product_classify_id=form.classify.data)
                                                              .where(Product.id.in_(form.product_ids.data)))
                re_data["success"] = True
                re_data["errorMessage"] = '更新成功'
            except ProductClassify.DoesNotExist as e:
                re_data["success"] = False
                re_data["errorMessage"] = '分类不存在'
        else:
            for field in form.errors:
                re_data["errorMessage"] = form.errors[field][0]
        await self.finish(re_data)


class ImportAndExportProductHandler(RedisHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        pass

    @authenticated_async
    async def post(self, *args, **kwargs):
        re_data = {}
        param = self.request.body.decode("utf-8")
        param = json.loads(param)
        datas = []
        product_list = []
        try:
            for data in param:
                form = CreatProductForm.from_json(data)
                if form.validate():
                    datas.append({
                        'product_no': form.product_no.data,
                        'name': form.name.data,
                        'barcode': form.barcode.data,
                        'product_classify_id': form.product_classify_id.data,
                        'product_classify_path': form.product_classify_path.data,
                        'product_classify': form.product_classify.data,
                        'price': form.price.data,
                        'cost': form.cost.data,
                        'box_rules': form.box_rules.data,
                        'validity': form.validity.data,
                        'product_introduction': form.product_introduction.data,
                        'supplier_id': form.supplier_id.data,
                        'supplier': form.supplier.data,
                        'is_stop': form.is_stop.data,
                        'is_delete': form.is_delete.data,
                        'create_user_id': self.current_user.id,
                        'create_user': self.current_user.name,
                    })
                else:
                    for field in form.errors:
                        re_data["errorMessage"] = form.errors[field][0]
                    raise ValueError('错误')
            for data in datas:
                for item in await self.application.objects.execute(
                        ProductClassify.select().where(ProductClassify.classify_name == data['product_classify'])):
                    data['product_classify_id'] = item.id
                    data['product_classify_path'] = item.parent_path
                product_list.append(copy.deepcopy(data))
            async with database.atomic_async():
                await self.application.objects.execute(Product.insert_many(product_list))
            re_data["success"] = True
            re_data["errorMessage"] = '导入成功'
        except ValueError as e:
            re_data["success"] = False
        await self.finish(re_data)


class ProductQueryHandler(RedisHandler):
    @authenticated_async
    async def post(self, *args, **kwargs):
        # 产品以及库存查询
        re_data = {}
        data_list = []
        param = self.request.body.decode()
        param = json.loads(param)

        query_sort, expressions = await Conditional(param=param)

        node_id = param['params']['node_id'][0]
        if expressions:
            if 'storehouse_id' in param['params']:
                expressions.append(StorehouseManagement.id == param['params']['storehouse_id'])
            sql = (Product.select(Product.id.alias("product_id"),
                                  Product.name.alias("product_name"),
                                  Product.product_no.alias("product_no"),
                                  Product.id.alias("product_id"),
                                  Product.box_rules,
                                  Product.barcode.alias("barcode"),
                                  Product.name,
                                  Product.price,
                                  Product.rec_price,
                                  fn.SUM(IrProperty.qty).alias('qty'),
                                  fn.AVG(IrProperty.cost_price).alias('cost_price'),)
                   .join(IrProperty, join_type=JOIN.LEFT_OUTER,
                         on=(Product.barcode == IrProperty.barcode))
                   .join(StorehouseManagement, join_type=JOIN.LEFT_OUTER,
                         on=(IrProperty.storehouse_id == StorehouseManagement.id))
                   .where(*expressions)
                   .group_by(Product.id)
                   .order_by(query_sort).dicts())
            data = await self.application.objects.execute(sql)
        else:
            if 'storehouse_id' in param['params']:
                expressions.append(StorehouseManagement.id == param['params']['storehouse_id'])
            classic = await self.application.objects.execute(ProductClassify.select()
                                                             .where(ProductClassify.parent_id == node_id))
            # 判断分类是否存在子节点
            if classic:
                base = (IrProperty.select(fn.SUM(IrProperty.qty).alias('qty'),
                                          fn.AVG(IrProperty.cost_price).alias('cost_price'),
                                          ProductClassify.parent_path)
                        .join(Product, join_type=JOIN.LEFT_OUTER, on=(Product.barcode == IrProperty.barcode))
                        .join(ProductClassify, join_type=JOIN.LEFT_OUTER,
                              on=(Product.product_classify_id == ProductClassify.id))
                        .join(StorehouseManagement, join_type=JOIN.LEFT_OUTER,
                              on=(IrProperty.storehouse_id == StorehouseManagement.id))
                        .where(*expressions)
                        .group_by(ProductClassify.classify_no)
                        .cte('ir_account'))
                sql = (ProductClassify.select(ProductClassify.id.alias("product_classify_id"),
                                              ProductClassify.classify_no.alias("product_no"),
                                              ProductClassify.classify_name.alias("product_name"),
                                              ProductClassify.parent_path.alias("parent_path"),
                                              fn.SUM(base.c.qty).alias('qty'),
                                              fn.AVG(base.c.cost_price).alias('cost_price'), )
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
                if expressions:
                    base = (last.select(last.product_no,
                                        fn.SUM(IrProperty.qty).alias('qty'),
                                        fn.AVG(IrProperty.cost_price).alias('cost_price'),
                                        )
                            .join(IrProperty, join_type=JOIN.RIGHT_OUTER, on=(last.barcode == IrProperty.barcode))
                            .join(StorehouseManagement, join_type=JOIN.LEFT_OUTER,
                                  on=(IrProperty.storehouse_id == StorehouseManagement.id))
                            .where(*expressions)
                            .group_by(last.product_no))
                else:
                    base = (last.select(last.product_no,
                                        fn.SUM(IrProperty.qty).alias('qty'),
                                        fn.AVG(IrProperty.cost_price).alias('cost_price'),
                                        )
                            .join(IrProperty, join_type=JOIN.RIGHT_OUTER, on=(last.barcode == IrProperty.barcode))
                            .join(StorehouseManagement, join_type=JOIN.LEFT_OUTER,
                                  on=(IrProperty.storehouse_id == StorehouseManagement.id))
                            .group_by(last.product_no))
                sql = (Product.select(Product.id.alias("product_id"),
                                      Product.name.alias("product_name"),
                                      Product.product_no.alias("product_no"),
                                      Product.barcode.alias("barcode"),
                                      Product.box_rules,
                                      Product.name,
                                      Product.price,
                                      Product.rec_price,
                                      base.c.qty,
                                      base.c.cost_price)
                       .join(base, join_type=JOIN.LEFT_OUTER, on=(base.c.product_no == Product.product_no))
                       .where(Product.product_classify_id == node_id)
                       .order_by(query_sort).dicts())
                data = await self.application.objects.execute(sql)

        for item in data:
            data_list.append(item)
        re_data["data"] = data_list
        re_data["success"] = True
        await self.finish(json.dumps(re_data, default=json_serial))


class GetProductImage(RedisHandler):
    async def post(self, *args, **kwargs):
        param = self.request.body.decode('utf-8')
        file_path = os.path.join(self.settings["MEDIA_ROOT"], param)
        # pic=open(file_path,'r')
        async with aiofiles.open(file_path, 'rb') as f:
            while True:
                data = await f.read(1024)
                if not data:
                    break
                self.write(data)
                await self.flush()


class ProductHandler(RedisHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        # 产品产品列表
        re_data = {}
        data = []
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
            if key == 'product_classify_id':
                product = await self.application.objects.get(ProductClassify, id=int(value))
                param_datas.update({'product_classify_id': product.parent_path})
        param = {'product_no', 'name', 'barcode', 'product_classify_id', 'supplier_id', 'is_stop', }

        # 处理排序
        if add_time == 'ascend':
            query_sort = Product.add_time.asc()
        elif add_time == 'descend':
            query_sort = Product.add_time.desc()
        elif modified == 'ascend':
            query_sort = Product.modified.asc()
        elif modified == 'descend':
            query_sort = Product.modified.desc()
        else:
            query_sort = Product.add_time.desc()

        # 没有参数就返回全部数据并分页
        if all(v not in param_datas for v in param):
            products = await self.application.objects.execute(Product
                                                              .select()
                                                              .order_by(query_sort)
                                                              .paginate(int(current), int(pageSize)))
            total = await self.application.objects.count(Product.select())
            for product in products:
                product_image = None
                if product.product_image:
                    product_image = "{}/media/{}".format(self.settings["SITE_URL"], product.product_image)
                item_data = model_to_dict(product)
                item_data['product_image'] = product_image
                data.append(item_data)
            re_data["data"] = data
            re_data["total"] = total
            re_data["page"] = current
            re_data["success"] = True
        else:
            query_params = await query_product_list(param_datas)
            query = await self.application.objects.execute(query_params
                                                           .select()
                                                           .order_by(query_sort)
                                                           .paginate(int(current), int(pageSize)))
            total = await self.application.objects.count(query_params.select())
            for product in query:
                product_image = None
                if product.product_image:
                    product_image = "{}/media/{}".format(self.settings["SITE_URL"], product.product_image)
                item_data = model_to_dict(product)
                item_data['product_image'] = product_image
                data.append(item_data)
            re_data["data"] = data
            re_data["total"] = total
            re_data["page"] = current
            re_data["success"] = True
        await self.finish(json.dumps(re_data, default=json_serial))

    @authenticated_async
    async def post(self, *args, **kwargs):
        # 新增产品
        re_data = {}
        # 不能使用jsonform
        param = self.request.body_arguments['data'][0]
        param = json.loads(param)
        form = CreatProductForm.from_json(param)
        if form.validate():
            # 查询客户编号是否重复
            product_no = await self.application.objects.execute(Product.select()
                                                                .where(Product.product_no == form.product_no.data))
            if len(product_no) > 0:
                re_data["success"] = False
                re_data["errorMessage"] = '产品编号已存在，请修改产品编号'
                return await self.finish(re_data)

            barcode = await self.application.objects.execute(Product.select()
                                                             .where(Product.barcode == form.barcode.data))
            if len(barcode) > 0:
                re_data["success"] = False
                re_data["errorMessage"] = '产品条码已存在，请修改产品条码'
                return await self.finish(re_data)

                # 自己完成图片字段验证
            files_meta = self.request.files.get("image_files", None)
            new_filename = ''
            if files_meta:
                # 完成图片保存并将值设置给对应的记录
                # 通过aiofiles写文件
                # 1.文件名
                for meta in files_meta:
                    filename = meta["filename"]
                    new_filename = "{uuid}_{name}".format(uuid=uuid.uuid1(), name=filename)
                    file_path = os.path.join(self.settings["MEDIA_ROOT"], new_filename)
                    async with aiofiles.open(file_path, 'wb') as f:
                        await f.write(meta['body'])
            await self.application.objects.create(Product, product_no=form.product_no.data, name=form.name.data,
                                                  barcode=form.barcode.data, price=float(form.price.data),
                                                  cost=float(form.cost.data),
                                                  box_rules=form.box_rules.data, validity=form.validity.data,
                                                  product_classify_id=form.product_classify_id.data,
                                                  product_classify_path=form.product_classify_path.data,
                                                  product_classify=form.product_classify.data,
                                                  product_introduction=form.product_introduction.data,
                                                  supplier_id=form.supplier_id.data, supplier=form.supplier.data,
                                                  is_stop=form.is_stop.data,
                                                  create_user_id=self.current_user.id,
                                                  create_user=self.current_user.name,
                                                  product_image=new_filename
                                                  )
            re_data["success"] = True
            re_data["errorMessage"] = '数据插入成功'
        else:
            for field in form.errors:
                re_data["errorMessage"] = form.errors[field][0]
        await self.finish(re_data)

    @authenticated_async
    async def patch(self, product_id, *args, **kwargs):
        # 更新产品
        re_data = {}
        # 不能使用jsonform
        param = self.request.body_arguments['data'][0]
        param = json.loads(param)
        form = CreatProductForm.from_json(param)
        if form.validate():
            try:
                product = await self.application.objects.get(Product, id=int(product_id))

                # 查询客户编号是否重复
                product_no = await self.application.objects.execute(Product.select()
                                                                    .where(Product.product_no == form.product_no.data,
                                                                           Product.id != int(product_id)))
                if len(product_no) > 0:
                    re_data["success"] = False
                    re_data["errorMessage"] = '产品编号已存在，请修改产品编号'
                    return await self.finish(re_data)

                barcode = await self.application.objects.execute(Product.select()
                                                                 .where(Product.barcode == form.barcode.data,
                                                                        Product.id != int(product_id)))
                if len(barcode) > 0:
                    re_data["success"] = False
                    re_data["errorMessage"] = '产品条码已存在，请修改产品条码'
                    return await self.finish(re_data)

                    # 自己完成图片字段验证

                files_meta = self.request.files.get("image_files", None)
                new_filename = None
                if files_meta:
                    # 判断图片是否修改
                    filename = files_meta[0]["filename"]
                    if filename == product.product_image:
                        new_filename = filename
                    else:
                        # 删除原来的图片
                        # 完成图片保存并将值设置给对应的记录
                        # 通过aiofiles写文件
                        # 1.文件名
                        if product.product_image is None or len(product.product_image) == 0:
                            for meta in files_meta:
                                filename = meta["filename"]
                                new_filename = "{uuid}_{name}".format(uuid=uuid.uuid1(), name=filename)
                                file_path = os.path.join(self.settings["MEDIA_ROOT"], new_filename)
                                async with aiofiles.open(file_path, 'wb') as f:
                                    await f.write(meta['body'])
                        else:
                            os.remove(os.path.join(self.settings["MEDIA_ROOT"], product.product_image).encode("utf-8"))
                            for meta in files_meta:
                                filename = meta["filename"]
                                new_filename = "{uuid}_{name}".format(uuid=uuid.uuid1(), name=filename)
                                file_path = os.path.join(self.settings["MEDIA_ROOT"], new_filename)
                                async with aiofiles.open(file_path, 'wb') as f:
                                    await f.write(meta['body'])
                else:
                    if product.product_image is not None and len(product.product_image) != 0:
                        os.remove(os.path.join(self.settings["MEDIA_ROOT"], product.product_image).encode("utf-8"))
                product.product_no = form.product_no.data
                product.name = form.name.data
                product.barcode = form.barcode.data
                product.price = float(form.price.data)
                product.cost = float(form.cost.data)
                product.box_rules = form.box_rules.data
                product.validity = form.validity.data
                product.product_classify_id = form.product_classify_id.data
                product.product_classify_path = form.product_classify_path.data
                product.product_classify = form.product_classify.data
                product.product_introduction = form.product_introduction.data
                product.supplier_id = form.supplier_id.data
                product.supplier = form.supplier.data
                product.is_stop = form.is_stop.data
                product.create_user_id = self.current_user.id
                product.create_user = self.current_user.name
                product.modified = datetime.now()
                product.product_image = new_filename

                await self.application.objects.update(product)
                re_data["success"] = True
                re_data["errorMessage"] = '数据修改成功'
            except Product.DoesNotExist as e:
                re_data["success"] = False
                re_data["errorMessage"] = '产品不存在！'
        else:
            for field in form.errors:
                re_data["errorMessage"] = form.errors[field][0]
        await self.finish(re_data)

    @authenticated_async
    async def delete(self, product_id, *args, **kwargs):
        re_data = {}
        try:
            product = await self.application.objects.get(Product, id=int(product_id))
            await self.application.objects.execute(Product.delete().where(Product.id == product_id))
            os.remove(os.path.join(self.settings["MEDIA_ROOT"], product.product_image))
            re_data["success"] = True
            re_data["errorMessage"] = '数据删除成功'
        except Product.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '数据删除失败'
        await self.finish(re_data)


class ProductClassifyHandler(RedisHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        # 查询产品分类信息
        re_data = {}
        data = []
        # 获取redis内存 菜单权限
        if (product_classify := await self.redis_conn.get('产品分类信息')) is not None:
            data = json.loads(product_classify)
            re_data["data"] = data
            re_data["success"] = True
        else:
            menu_data = await self.application.objects.execute(ProductClassify.select())
            for item in menu_data:
                data.append(model_to_dict(item))
            data = await find_menu(data)
            # 产品分类信息权限存入redis
            await self.redis_conn.set('产品分类信息',
                                      json.dumps(data, default=json_serial), ex=1)
            re_data["data"] = data
            re_data["success"] = True
        await self.finish(json.dumps(re_data, default=json_serial))

    @authenticated_async
    async def delete(self, product_classify_id, *args, **kwargs):
        # 删除产品分类
        re_data = {}
        try:
            await self.application.objects.get(ProductClassify, id=int(product_classify_id))
            product_classify_child = await self.application.objects.execute(ProductClassify
                                                                            .select()
                                                                            .where(ProductClassify.parent_id ==
                                                                                   int(product_classify_id)))
            product_classify = await self.application.objects.execute(Product
                                                                      .select()
                                                                      .where(Product.product_classify_id ==
                                                                             int(product_classify_id)))
            if len(product_classify_child) == 0 and len(product_classify) == 0:
                await self.application.objects.execute(ProductClassify.delete().where(ProductClassify.id ==
                                                                                      int(product_classify_id)))
                re_data["success"] = True
                re_data["errorMessage"] = '分类删除成功'
            else:
                re_data["success"] = False
                re_data["errorMessage"] = '分类下存在数据，无法删除'
        except ProductClassify.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '分类不存在'
        await self.finish(re_data)

    @authenticated_async
    async def post(self, *args, **kwargs):
        re_data = {}
        param = self.request.body.decode("utf8")
        param = json.loads(param)
        form = CreateProductClassify.from_json(param)
        if form.validate():
            try:
                await self.application.objects.get(ProductClassify, classify_no=str(form.classify_no.data))
                re_data["success"] = False
                re_data["errorMessage"] = '分类编号重复'
            except ProductClassify.DoesNotExist as e:
                if form.parent_id.data != 0:
                    try:
                        pi_path = await self.application.objects.get(ProductClassify, id=form.parent_id.data)
                        async with database.atomic_async():
                            product_classify = await self.application.objects.create(ProductClassify,
                                                                                     classify_no=form.classify_no.data,
                                                                                     classify_name=form.classify_name.data,
                                                                                     parent_id=form.parent_id.data,
                                                                                     level=form.level.data,
                                                                                     status=form.status.data,
                                                                                     order_num=form.order_num.data,
                                                                                     create_user_id=self.current_user.id,
                                                                                     create_user=self.current_user.name)
                            product_classify.parent_path = str(pi_path.parent_path) + str(product_classify.id) + '/'
                            await self.application.objects.update(product_classify)
                    except ProductClassify.DoesNotExist as e:
                        re_data["success"] = False
                        re_data["errorMessage"] = '上级目录不存在'
                else:
                    async with database.atomic_async():
                        product_classify = await self.application.objects.create(ProductClassify,
                                                                                 classify_no=form.classify_no.data,
                                                                                 classify_name=form.classify_name.data,
                                                                                 parent_id=form.parent_id.data,
                                                                                 level=form.level.data,
                                                                                 status=form.status.data,
                                                                                 order_num=form.order_num.data,
                                                                                 create_user_id=self.current_user.id,
                                                                                 create_user=self.current_user.name)
                        product_classify.parent_path = str(product_classify.id) + '/'
                        await self.application.objects.update(product_classify)
                re_data["success"] = True
                re_data["errorMessage"] = '分类新建成功'
        else:
            for field in form.errors:
                re_data["errorMessage"] = form.errors[field][0]
        await self.finish(re_data)

    @authenticated_async
    async def patch(self, *args, **kwargs):
        # 更新产品分类
        re_data = {}
        param = self.request.body.decode("utf8")
        param = json.loads(param)
        form = UpdateProductClassify.from_json(param)
        if form.validate():
            try:
                product_classify = await self.application.objects.get(ProductClassify, id=int(form.id.data))
                product_classify.classify_no = form.classify_no.data
                product_classify.classify_name = form.classify_name.data
                product_classify.status = form.status.data
                product_classify.order_num = form.order_num.data
                product_classify.modified = datetime.now()

                await self.application.objects.update(product_classify)
                re_data["success"] = True
                re_data["errorMessage"] = '分类更新成功'

            except ProductClassify.DoesNotExist as e:
                re_data["success"] = False
                re_data["errorMessage"] = '分类不存在'
        else:
            for field in form.errors:
                re_data["errorMessage"] = form.errors[field][0]
        await self.finish(re_data)
