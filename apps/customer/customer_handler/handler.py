import copy
import json
from datetime import datetime

from wherp.handler import RedisHandler
from wherp.settings import database
from apps.customer.customer_handler.models import *
from apps.utils.mxform_decorators import authenticated_async
from apps.customer.customer_handler.forms import *
from apps.finance.subsidiary_ledger.models import SubsidiaryLedger
from apps.utils.util_func import json_serial
from apps.utils.FindMenu import find_menu
from playhouse.shortcuts import model_to_dict


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
    if 'customer_name' in param['params']:
        expressions.append(Customer.name.contains(param['params']['customer_name']))
    if 'customer_id' in param['params']:
        expressions.append(Customer.id == param['params']['customer_id'])
    if 'customer_no' in param['params']:
        expressions.append(Customer.uk_customer_no.contains(param['params']['customer_no']))

    return query_sort, expressions


class BatchUpdateEditCustomerHandler(RedisHandler):
    @authenticated_async
    async def post(self, *args, **kwargs):
        re_data = {}
        param = self.request.body.decode()
        param = json.loads(param)
        form = BatchUpdateCustomerForm.from_json(param)
        if form.validate():
            try:
                await self.application.objects.get(CustomerClassify, id=form.classify.data)
                data = await self.application.objects.execute(Customer
                                                              .update(customer_classify=form.classify.data)
                                                              .where(Customer.id.in_(form.customer_ids.data)))
                re_data["success"] = True
                re_data["errorMessage"] = '更新成功'
            except CustomerClassify.DoesNotExist as e:
                re_data["success"] = False
                re_data["errorMessage"] = '分类不存在'
        else:
            for field in form.errors:
                re_data["errorMessage"] = form.errors[field][0]
        await self.finish(re_data)


class queryCustomerHandler(RedisHandler):
    @authenticated_async
    async def post(self, *args, **kwargs):
        re_data = {}
        data_list = []
        param = self.request.body.decode()
        param = json.loads(param)

        query_sort, expressions = await Conditional(param=param)

        node_id = param['params']['node_id'][0]
        if expressions:
            sql = (Customer.select(Customer.name.alias("customer_name"),
                                   Customer.uk_customer_no.alias("customer_no"),
                                   Customer.id.alias("customer_id"),
                                   Customer.person_contact,
                                   Customer.mobile,
                                   Customer.province_id,
                                   Customer.city_id,
                                   Customer.district_id,
                                   Customer.address,
                                   fn.SUM(Case(None, [((SubsidiaryLedger.as_id == 38),
                                                       SubsidiaryLedger.amount)], 0)).alias('ar_amount'),
                                   fn.SUM(Case(None, [((SubsidiaryLedger.as_id == 47),
                                                       SubsidiaryLedger.amount)], 0)).alias('ap_amount'),)
                   .where(*expressions)
                   .join(SubsidiaryLedger, join_type=JOIN.LEFT_OUTER,
                         on=(Customer.id == SubsidiaryLedger.customer_id))
                   .group_by(Customer.id)
                   .order_by(query_sort)
                   .dicts())
            data = await self.application.objects.execute(sql)
        else:
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

                sql = (CustomerClassify.select(CustomerClassify.id.alias("customer_classify_id"),
                                               CustomerClassify.classify_no.alias("customer_no"),
                                               CustomerClassify.classify_name.alias("customer_name"),
                                               CustomerClassify.parent_path.alias("parent_path"),
                                               fn.SUM(Case(None, [(((base.c.ar - base.c.ap) > 0),
                                                                   (base.c.ar - base.c.ap))], 0)).alias('ar_amount'),
                                               fn.ABS(fn.SUM(Case(None, [(((base.c.ar - base.c.ap) < 0),
                                                                          (base.c.ar - base.c.ap))], 0))).alias('ap_amount'), )
                       .join(base, join_type=JOIN.LEFT_OUTER,
                             on=(base.c.parent_path.contains(CustomerClassify.parent_path)))
                       .where(CustomerClassify.parent_id == node_id)
                       .group_by(CustomerClassify.id)
                       .order_by(query_sort)
                       .dicts()
                       .with_cte(base))
                # sql = (CustomerClassify.select(CustomerClassify.id.alias("customer_classify_id"),
                #                                CustomerClassify.classify_no.alias("customer_no"),
                #                                CustomerClassify.classify_name.alias("customer_name"),
                #                                CustomerClassify.parent_path.alias("parent_path"), )
                #        .where(CustomerClassify.parent_id == node_id)
                #        .group_by(CustomerClassify.id)
                #        .order_by(query_sort)
                #        .dicts())
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

                sql = (Customer.select(Customer.name.alias("customer_name"),
                                       Customer.uk_customer_no.alias("customer_no"),
                                       Customer.id.alias("customer_id"),
                                       Customer.person_contact,
                                       Customer.mobile,
                                       Customer.province_id,
                                       Customer.city_id,
                                       Customer.district_id,
                                       Customer.address,
                                       fn.SUM(Case(None, [(((base.c.ar - base.c.ap) > 0), (base.c.ar - base.c.ap))],
                                                   0)).alias('ar_amount'),
                                       fn.ABS(
                                           fn.SUM(Case(None, [(((base.c.ar - base.c.ap) < 0), (base.c.ar - base.c.ap))],
                                                       0))).alias('ap_amount'), )
                       .join(base, join_type=JOIN.LEFT_OUTER, on=(Customer.uk_customer_no == base.c.uk_customer_no))
                       .group_by(Customer.id)
                       .where(Customer.customer_classify == node_id)
                       .order_by(query_sort)
                       .dicts()
                       .with_cte(base))

                # sql = (Customer.select(Customer.name.alias("customer_name"),
                #                        Customer.uk_customer_no.alias("customer_no"),
                #                        Customer.id.alias("customer_id"),
                #                        Customer.person_contact,
                #                        Customer.mobile,
                #                        Customer.province_id,
                #                        Customer.city_id,
                #                        Customer.district_id,
                #                        Customer.address)
                #        .where(Customer.customer_classify == node_id)
                #        .order_by(query_sort).dicts())

                data = await self.application.objects.execute(sql)

        for item in data:
            data_list.append(item)

        re_data['data'] = data_list
        re_data["success"] = True
        await self.finish(json.dumps(re_data, default=json_serial))


class GETARDetailListHandler(RedisHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        re_data = {}
        datas = []

        classify_id = self.get_argument('id', None)

        old_Customer = Customer.alias()
        data_query = (old_Customer
                      .select(old_Customer,
                              fn.COALESCE(old_Customer.ar_amount + fn.SUM(SubsidiaryLedger.add_amount -
                                                                          SubsidiaryLedger.sub_amount),
                                          old_Customer.ar_amount).alias('total'))
                      .join(SubsidiaryLedger, join_type=JOIN.LEFT_OUTER,
                            on=(old_Customer.id == SubsidiaryLedger.customer_id))
                      .group_by(old_Customer.id)
                      .where(old_Customer.customer_classify_id == int(classify_id), SubsidiaryLedger.as_id == 38))
        query = await self.application.objects.execute(data_query)
        for item in query:
            data = model_to_dict(item)
            data['total'] = item.total
            datas.append(copy.deepcopy(data))

        re_data["data"] = datas
        re_data["success"] = True

        await self.finish(json.dumps(re_data, default=json_serial))


class ARHandler(RedisHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        re_data = {}
        datas = []

        old_customer = Customer.alias()
        old_ar = SubsidiaryLedger.alias()

        cte = (old_customer
               .select(old_customer, fn.COALESCE(old_customer.ar_amount + fn.SUM(old_ar.add_amount - old_ar.sub_amount),
                                                 old_customer.ar_amount).alias('total'))
               .where(old_ar.as_id == 38)
               .join(old_ar, join_type=JOIN.LEFT_OUTER, on=(old_customer.id == old_ar.customer_id))
               .group_by(old_customer.uk_customer_no).cte('order_as'))

        order_as = CustomerClassify.alias()
        cte2 = (order_as
                .select(order_as, fn.SUM(cte.c.total).alias('actual_amount'))
                .join(cte, join_type=JOIN.LEFT_OUTER,
                      on=(order_as.id == cte.c.customer_classify_id))
                .group_by(order_as.classify_no).cte('as_tree_amount'))

        query = await self.application.objects.execute(CustomerClassify
                                                       .select(CustomerClassify,
                                                               cte2.select(fn.SUM(cte2.c.actual_amount))
                                                               .where(cte2.c.parent_path
                                                                      .contains(CustomerClassify.parent_path))
                                                               .alias('actual_amount'))
                                                       .join(cte2, join_type=JOIN.LEFT_OUTER,
                                                             on=(CustomerClassify.id == cte2.c.id))
                                                       .with_cte(cte, cte2))
        for item in query:
            data = model_to_dict(item)
            data['actual_amount'] = item.actual_amount
            datas.append(data)
        datas = await find_menu(datas)

        re_data["data"] = datas
        re_data["success"] = True
        await self.finish(json.dumps(re_data, default=json_serial))


class ImportAndExportCustomerHandler(RedisHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        # 导出客户
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
                form = ImportCustomerForm.from_json(data)
                if form.validate():
                    datas.append({
                        'uk_customer_no': form.uk_customer_no.data,
                        'name': form.name.data,
                        'person_contact': form.person_contact.data,
                        'mobile': form.mobile.data,
                        'phone': form.phone.data,
                        'province': form.province.data,
                        'city': form.city.data,
                        'district': form.district.data,
                        'address': form.address.data,
                        'customer_manager': form.customer_manager.data,
                        'customer_classify': form.customer_classify.data,
                        'customer_type': form.customer_type.data,
                        'bank': form.bank.data,
                        'bank_account': form.bank_account.data,
                        'tax_no': form.tax_no.data,
                        'ar_amount': form.ar_amount.data,
                        'ap_amount': form.ap_amount.data,
                        'note': form.note.data,
                        'is_stop': form.is_stop.data,
                        'create_user_id': self.current_user.id,
                        'create_user': self.current_user.name,
                    })
                else:
                    for field in form.errors:
                        re_data["errorMessage"] = form.errors[field][0]
                    raise ValueError('错误')
            for data in datas:
                for item in await self.application.objects.execute(
                        CustomerClassify.select().where(CustomerClassify.classify_name == data['customer_classify'])):
                    data['customer_classify_id'] = item.id
                if data['province'] is not None:
                    for item in await self.application.objects.execute(
                            AddressClassify.select().where(AddressClassify.classify_name.contains(data['province']))):
                        data['province_id'] = item.id
                if data['city'] is not None:
                    for item in await self.application.objects.execute(
                            AddressClassify.select().where(AddressClassify.classify_name.contains(data['city']))):
                        data['city_id'] = item.id
                if data['district'] is not None:
                    for item in await self.application.objects.execute(
                            AddressClassify.select().where(AddressClassify.classify_name.contains(data['district']))):
                        data['district_id'] = item.id
                product_list.append(copy.deepcopy(data))
            async with database.atomic_async():
                await self.application.objects.execute(Customer.insert_many(product_list))
            re_data["success"] = True
            re_data["errorMessage"] = '导入成功'
        except ValueError as e:
            re_data["success"] = False
        await self.finish(re_data)


class CustomerClassifyHandler(RedisHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        # 查询客户分类信息
        re_data = {}
        data = []
        # 获取redis内存 菜单权限
        if (cuatomer_classify := await self.redis_conn.get('客户分类信息')) is not None:
            data = json.loads(cuatomer_classify)
            re_data["data"] = data
            re_data["success"] = True
        else:
            menu_data = await self.application.objects.execute(CustomerClassify.select())
            for item in menu_data:
                data.append(model_to_dict(item))
            data = await find_menu(data)
            # 客户分类信息权限存入redis
            await self.redis_conn.set('客户分类信息',
                                      json.dumps(data, default=json_serial), ex=1)
            re_data["data"] = data
            re_data["success"] = True
        await self.finish(json.dumps(re_data, default=json_serial))

    @authenticated_async
    async def delete(self, customer_classify_id, *args, **kwargs):
        # 删除客户分类
        re_data = {}
        try:
            await self.application.objects.get(CustomerClassify, id=int(customer_classify_id))
            customer_classify_child = await self.application.objects.execute(CustomerClassify
                                                                             .select()
                                                                             .where(CustomerClassify.parent_id ==
                                                                                    int(customer_classify_id)))
            customer_classify = await self.application.objects.execute(Customer
                                                                       .select()
                                                                       .where(Customer.customer_classify ==
                                                                              int(customer_classify_id)))
            if len(customer_classify_child) == 0 and len(customer_classify) == 0:
                await self.application.objects.execute(CustomerClassify.delete().where(CustomerClassify.id ==
                                                                                       int(customer_classify_id)))
                re_data["success"] = True
                re_data["errorMessage"] = '科目删除成功'
            else:
                re_data["success"] = False
                re_data["errorMessage"] = '科目下存在数据，无法删除'
        except CustomerClassify.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '科目不存在'
        await self.finish(re_data)

    @authenticated_async
    async def post(self, *args, **kwargs):
        re_data = {}
        param = self.request.body.decode("utf8")
        param = json.loads(param)
        form = CreateCustomerClassifyForm.from_json(param)
        if form.validate():
            try:
                await self.application.objects.get(CustomerClassify, classify_no=str(form.classify_no.data))
                re_data["success"] = False
                re_data["errorMessage"] = '分类编号重复'
            except CustomerClassify.DoesNotExist as e:
                if form.parent_id.data != 0:
                    try:
                        pi_path = await self.application.objects.get(CustomerClassify, id=form.parent_id.data)
                        async with database.atomic_async():
                            customer_classify = await self.application.objects.create(CustomerClassify,
                                                                                      classify_no=form.classify_no.data,
                                                                                      classify_name=form.classify_name.data,
                                                                                      parent_id=form.parent_id.data,
                                                                                      level=form.level.data,
                                                                                      status=form.status.data,
                                                                                      order_num=form.order_num.data,
                                                                                      create_user_id=self.current_user.id,
                                                                                      create_user=self.current_user.name)
                            customer_classify.parent_path = str(pi_path.parent_path) + str(customer_classify.id) + '/'
                            await self.application.objects.update(customer_classify)
                    except CustomerClassify.DoesNotExist as e:
                        re_data["success"] = False
                        re_data["errorMessage"] = '上级目录不存在'
                else:
                    async with database.atomic_async():
                        customer_classify = await self.application.objects.create(CustomerClassify,
                                                                                  classify_no=form.classify_no.data,
                                                                                  classify_name=form.classify_name.data,
                                                                                  parent_id=form.parent_id.data,
                                                                                  level=form.level.data,
                                                                                  status=form.status.data,
                                                                                  order_num=form.order_num.data,
                                                                                  create_user_id=self.current_user.id,
                                                                                  create_user=self.current_user.name)
                        customer_classify.parent_path = str(customer_classify.id) + '/'
                        await self.application.objects.update(customer_classify)
                re_data["success"] = True
                re_data["errorMessage"] = '分类新建成功'
        else:
            for field in form.errors:
                re_data["errorMessage"] = form.errors[field][0]
        await self.finish(re_data)

    @authenticated_async
    async def patch(self, *args, **kwargs):
        # 更新客户分类
        re_data = {}
        param = self.request.body.decode("utf8")
        param = json.loads(param)
        form = UpdateCustomerClassifyForm.from_json(param)
        if form.validate():
            try:
                customer_classify = await self.application.objects.get(CustomerClassify, id=int(form.id.data))
                customer_classify.classify_no = form.classify_no.data
                customer_classify.classify_name = form.classify_name.data
                customer_classify.status = form.status.data
                customer_classify.order_num = form.order_num.data
                customer_classify.modified = datetime.now()

                await self.application.objects.update(customer_classify)
                re_data["success"] = True
                re_data["errorMessage"] = '分类更新成功'

            except CustomerClassify.DoesNotExist as e:
                re_data["success"] = False
                re_data["errorMessage"] = '分类不存在'
        else:
            for field in form.errors:
                re_data["errorMessage"] = form.errors[field][0]
        await self.finish(re_data)


class CustomerHandler(RedisHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        # 查询客户
        re_data = {}
        data = []

        current = self.get_argument("current", None)
        pageSize = self.get_argument("pageSize", None)

        from apps.utils.FilterParams import Filter

        expressions = await Filter(self.request.arguments).customer_filter(model=Customer, model2=CustomerClassify)
        items = await self.application.objects.execute(
            Customer.extend().where(*expressions).order_by(Customer.add_time.desc()).paginate(int(current),
                                                                                              int(pageSize)))
        total = await self.application.objects.count(Customer.select().where(*expressions))
        for item in items:
            obj_data = model_to_dict(item)
            if 'CustomerClassify' in dir(item):
                obj_data['customer_classify_id'] = item.CustomerClassify.classify_name
            obj_data['area'] = [item.province_id, item.city_id, item.district_id]
            data.append(obj_data)
        re_data["data"] = data
        re_data["total"] = total
        re_data["page"] = current
        re_data["success"] = True

        await self.finish(json.dumps(re_data, default=json_serial))

    @authenticated_async
    async def post(self, *args, **kwargs):
        # 新增客户
        re_data = {}
        param = self.request.body.decode("utf-8")
        param = json.loads(param)
        form = CreatCustomerForm.from_json(param)
        if form.validate():
            try:
                # 查询客户编号是否重复
                await self.application.objects.get(Customer, uk_customer_no=form.uk_customer_no.data)
                re_data["success"] = False
                re_data["errorMessage"] = '客户编号已存在，请修改客户编号'
            except Customer.DoesNotExist as e:
                # 插入数据
                await self.application.objects.create(Customer,
                                                      uk_customer_no=form.uk_customer_no.data,
                                                      name=form.name.data,
                                                      person_contact=form.person_contact.data,
                                                      mobile=form.mobile.data,
                                                      phone=form.phone.data,
                                                      province_id=form.area.data[0],
                                                      city_id=form.area.data[1],
                                                      district_id=form.area.data[2],
                                                      address=form.address.data,
                                                      employee=form.employee.data,
                                                      customer_classify=form.customer_classify.data,
                                                      customer_type=form.customer_type.data,
                                                      bank=form.bank.data,
                                                      bank_account=form.bank_account.data,
                                                      tax_no=form.tax_no.data,
                                                      note=form.note.data,
                                                      ar_amount=form.ar_amount.data,
                                                      ap_amount=form.ap_amount.data,
                                                      create_user_id=self.current_user.id)
                re_data["success"] = True
                re_data["errorMessage"] = '数据插入成功'

        else:
            for field in form.errors:
                re_data["errorMessage"] = form.errors[field][0]
        await self.finish(re_data)

    @authenticated_async
    async def patch(self, customer_id, *args, **kwargs):
        # 更新客户
        re_data = {}
        param = self.request.body.decode("utf-8")
        param = json.loads(param)
        form = CreatCustomerForm.from_json(param)
        if form.validate():
            try:
                # 查询客户编号是否重复
                customer = await self.application.objects.get(Customer, id=customer_id)

                customer.uk_customer_no = form.uk_customer_no.data
                customer.name = form.name.data
                customer.person_contact = form.person_contact.data
                customer.mobile = form.mobile.data
                customer.phone = form.phone.data
                customer.province_id = form.area.data[0]
                customer.city_id = form.area.data[1]
                customer.district_id = form.area.data[2]
                customer.address = form.address.data
                customer.employee = form.employee.data
                customer.customer_classify = form.customer_classify.data
                customer.customer_type = form.customer_type.data
                customer.bank = form.bank.data
                customer.bank_account = form.bank_account.data
                customer.tax_no = form.tax_no.data
                customer.note = form.note.data
                customer.is_stop = form.is_stop.data
                customer.ar_amount = form.ar_amount.data
                customer.ap_amount = form.ap_amount.data

                # 更新数据
                await self.application.objects.update(customer)
                re_data["success"] = True
                re_data["errorMessage"] = '数据更新成功'

            except Customer.DoesNotExist as e:
                re_data["success"] = False
                re_data["errorMessage"] = '客户不存在'
        else:
            for field in form.errors:
                re_data["errorMessage"] = form.errors[field][0]
        await self.finish(re_data)

    @authenticated_async
    async def delete(self, customer_id, *args, **kwargs):
        re_data = {}
        try:
            await self.application.objects.get(Customer, id=int(customer_id))
            await self.application.objects.execute(Customer.delete().where(Customer.id == int(customer_id)))
            re_data["success"] = True
            re_data["errorMessage"] = "客户数据删除成功"
        except Customer.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = "数据不存在"
        await self.finish(re_data)


class AddressClassifyHandler(RedisHandler):
    async def get(self, *args, **kwargs):
        # 查询地区分类信息
        re_data = {}
        data = []
        # 获取redis内存 菜单权限
        if (address := await self.redis_conn.get('地区分类信息')) is not None:
            data = json.loads(address)
            re_data["data"] = data
            re_data["success"] = True
        else:
            menu_data = await self.application.objects.execute(AddressClassify.select())
            for item in menu_data:
                data.append(model_to_dict(item))
            data = await find_menu(data)
            # 地区分类存入redis
            await self.redis_conn.set('地区分类信息',
                                      json.dumps(data, default=json_serial), ex=60 * 60 * 24 * 7)

            re_data["data"] = data
            re_data["success"] = True
        await self.finish(json.dumps(re_data, default=json_serial))

    @authenticated_async
    async def delete(self, address_classify_id, *args, **kwargs):
        # 删除地区分类
        re_data = {}
        try:
            await self.application.objects.get(AddressClassify, id=int(address_classify_id))
            address_classify_child = await self.application.objects.execute(AddressClassify
                                                                            .select()
                                                                            .where(AddressClassify.parent_id ==
                                                                                   int(address_classify_id)))
            if len(address_classify_child) == 0:
                await self.application.objects.execute(AddressClassify.delete().where(AddressClassify.id ==
                                                                                      int(address_classify_id)))

                # 地区分类存入redis
                data = []
                menu_data = await self.application.objects.execute(AddressClassify.select())
                for item in menu_data:
                    data.append(model_to_dict(item))
                data = await find_menu(data)
                await self.redis_conn.set('地区分类信息',
                                          json.dumps(data, default=json_serial), ex=60 * 60 * 24 * 7)

                re_data["success"] = True
                re_data["errorMessage"] = '分类删除成功'
            else:
                re_data["success"] = False
                re_data["errorMessage"] = '分类下存在数据，无法删除'
        except AddressClassify.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '科目不存在'
        await self.finish(re_data)

    @authenticated_async
    async def post(self, *args, **kwargs):
        # 新增地区分类
        re_data = {}
        param = self.request.body.decode("utf8")
        param = json.loads(param)
        form = CreateAddressClassify.from_json(param)
        if form.validate():
            try:
                await self.application.objects.get(AddressClassify, classify_no=str(form.classify_no.data))
                re_data["success"] = False
                re_data["errorMessage"] = '分类编号重复'
            except AddressClassify.DoesNotExist as e:
                if form.parent_id.data != 0:
                    try:
                        pi_path = await self.application.objects.get(AddressClassify, id=form.parent_id.data)
                        async with database.atomic_async():
                            address_classify = await self.application.objects.create(AddressClassify,
                                                                                     classify_no=form.classify_no.data,
                                                                                     classify_name=form.classify_name.data,
                                                                                     parent_id=form.parent_id.data,
                                                                                     level=form.level.data,
                                                                                     status=form.status.data,
                                                                                     order_num=form.order_num.data,
                                                                                     create_user_id=self.current_user.id,
                                                                                     create_user=self.current_user.name)
                            address_classify.parent_path = str(pi_path.parent_path) + str(address_classify.id) + '/'
                            await self.application.objects.update(address_classify)
                    except AddressClassify.DoesNotExist as e:
                        re_data["success"] = False
                        re_data["errorMessage"] = '上级目录不存在'
                else:
                    async with database.atomic_async():
                        address_classify = await self.application.objects.create(AddressClassify,
                                                                                 classify_no=form.classify_no.data,
                                                                                 classify_name=form.classify_name.data,
                                                                                 parent_id=form.parent_id.data,
                                                                                 level=form.level.data,
                                                                                 status=form.status.data,
                                                                                 order_num=form.order_num.data,
                                                                                 create_user_id=self.current_user.id,
                                                                                 create_user=self.current_user.name)
                        address_classify.parent_path = str(address_classify.id) + '/'
                        await self.application.objects.update(address_classify)

                # 地区分类存入redis
                data = []
                menu_data = await self.application.objects.execute(AddressClassify.select())
                for item in menu_data:
                    data.append(model_to_dict(item))
                data = await find_menu(data)
                await self.redis_conn.set('地区分类信息',
                                          json.dumps(data, default=json_serial), ex=60 * 60 * 24 * 7)
                re_data["success"] = True
                re_data["errorMessage"] = '分类新建成功'
        else:
            for field in form.errors:
                re_data["errorMessage"] = form.errors[field][0]
        await self.finish(re_data)

    @authenticated_async
    async def patch(self, id, *args, **kwargs):
        # 更新地区分类
        re_data = {}
        param = self.request.body.decode("utf8")
        param = json.loads(param)
        form = UpdateAddressClassify.from_json(param)
        if form.validate():
            try:
                product_classify = await self.application.objects.get(AddressClassify, id=int(id))
                product_classify.classify_no = form.classify_no.data
                product_classify.classify_name = form.classify_name.data
                product_classify.status = form.status.data
                product_classify.order_num = form.order_num.data
                product_classify.modified = datetime.now()

                await self.application.objects.update(product_classify)
                re_data["success"] = True
                re_data["errorMessage"] = '分类更新成功'

                # 地区分类存入redis
                data = []
                menu_data = await self.application.objects.execute(AddressClassify.select())
                for item in menu_data:
                    data.append(model_to_dict(item))
                data = await find_menu(data)
                await self.redis_conn.set('地区分类信息',
                                          json.dumps(data, default=json_serial), ex=60 * 60 * 24 * 7)

            except AddressClassify.DoesNotExist as e:
                re_data["success"] = False
                re_data["errorMessage"] = '分类不存在'
        else:
            for field in form.errors:
                re_data["errorMessage"] = form.errors[field][0]
        await self.finish(re_data)
