import copy
import json
from datetime import datetime

from wherp.handler import RedisHandler
from apps.utils.mxform_decorators import authenticated_async
from apps.purchase.supplier.models import *
from apps.purchase.supplier.forms import *
from apps.finance.subsidiary_ledger.models import SubsidiaryLedger
from apps.utils.util_func import json_serial
from playhouse.shortcuts import model_to_dict


async def query_suppliers(uk_customer_no=None, name=None, mobile=None, address_id=None, customer_id=None, is_stop=None):
    queryList = []
    if uk_customer_no is not None:
        queryList.append(Supplier.uk_customer_no.contains(str(uk_customer_no)))
    if name is not None:
        queryList.append(Supplier.name.contains(str(name)))
    if mobile is not None:
        queryList.append((Supplier.mobile.contains(str(mobile))))
    if customer_id is not None:
        queryList.append((Supplier.customer_id == (int(customer_id))))

    if address_id is not None:
        if len(address_id) >= 1:
            queryList.append((Supplier.province_id == (int(address_id[0]))))
        if len(address_id) >= 2:
            queryList.append((Supplier.city_id == (int(address_id[1]))))
        if len(address_id) >= 3:
            queryList.append((Supplier.district_id == (int(address_id[2]))))
    if is_stop is not None:
        queryList.append((Supplier.is_stop == (str(is_stop))))


    query = queryList[0]
    for data in queryList[1:]:
        query = query & data
    query = Supplier.select().where(query)

    return query


class GETAPDetailListHandler(RedisHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        re_data = {}
        datas = []

        old_Supplier = Supplier.alias()
        data_query = (old_Supplier
                      .select(old_Supplier,
                              fn.COALESCE(old_Supplier.ap_amount + fn.SUM(SubsidiaryLedger.add_amount -
                                                                          SubsidiaryLedger.sub_amount),
                                          old_Supplier.ap_amount).alias('total'))
                      .join(SubsidiaryLedger, join_type=JOIN.LEFT_OUTER,
                            on=(old_Supplier.id == SubsidiaryLedger.supplier_id))
                      .group_by(old_Supplier.id)
                      .where(SubsidiaryLedger.as_id == 47))
        query = await self.application.objects.execute(data_query)
        for item in query:
            data = model_to_dict(item)
            data['total'] = item.total
            datas.append(copy.deepcopy(data))

        re_data["data"] = datas
        re_data["success"] = True

        await self.finish(json.dumps(re_data, default=json_serial))


class SupplierAccountCurrentHandler(RedisHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        # 查询供应商往来
        re_data = {}
        data = []
        current = self.get_argument("current", None)
        pageSize = self.get_argument("pageSize", None)

        items = await self.application.objects.execute(SubsidiaryLedger
                                                       .select()
                                                       .where(SubsidiaryLedger.as_id == 47)
                                                       .paginate(int(current), int(pageSize)))
        total = await self.application.objects.count(SupplierAccountCurrent.select())

        for item in items:
            item = model_to_dict(item)
            data.append(copy.deepcopy(item))

        re_data["data"] = data
        re_data["total"] = total
        re_data["page"] = current
        re_data["success"] = True

        await self.finish(json.dumps(re_data, default=json_serial))


class getSupplierHandler(RedisHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        re_data = {}
        data = []
        suppliers = await self.application.objects.execute(Supplier.select(Supplier.id, Supplier.name))
        for item in suppliers:
            data.append(model_to_dict(item))
        re_data["data"] = data
        re_data["success"] = True
        await self.finish(re_data)


class PurchaseHandler(RedisHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        # 查询供应商
        re_data = {}
        data = []

        current = self.get_argument("current", None)
        pageSize = self.get_argument("pageSize", None)

        uk_supplier_no = self.get_argument("uk_supplier_no", None)
        name = self.get_argument("name", None)
        mobile = self.get_argument("mobile", None)
        address_id = self.get_arguments("address", True)
        if len(address_id) == 0:
            address_id = None
        customer_id = self.get_argument("customer_id", None)
        is_stop = self.get_argument("is_stop", None)

        # 没有参数就返回全部数据并分页
        if all(v is None for v in [uk_supplier_no, name, mobile, address_id, customer_id,  is_stop]):

            suppliers = await self.application.objects.execute(Supplier.select().paginate(int(current), int(pageSize)))
            total = await self.application.objects.count(Supplier.select())
            for supplier in suppliers:
                item_data = model_to_dict(supplier)
                data.append(item_data)
            re_data["data"] = data
            re_data["total"] = total
            re_data["page"] = current
            re_data["success"] = True
        else:
            query_supplier = await query_suppliers(uk_supplier_no, name, mobile, address_id, customer_id, is_stop)
            customers = await self.application.objects.execute(query_supplier.paginate(int(current), int(pageSize)))
            total = await self.application.objects.count(query_supplier)

            for customer in customers:
                item_data = model_to_dict(customer)
                data.append(item_data)
            re_data["data"] = data
            re_data["total"] = total
            re_data["page"] = current
            re_data["success"] = True
        await self.finish(json.dumps(re_data, default=json_serial))

    @authenticated_async
    async def post(self, *args, **kwargs):
        # 新增供应商
        re_data = {}
        param = self.request.body.decode("utf-8")
        param = json.loads(param)
        form = CreatSupplierForm.from_json(param)
        if form.validate():
            try:
                # 查询客户编号是否重复
                await self.application.objects.get(Supplier, uk_supplier_no=str(form.uk_supplier_no.data))
                re_data["success"] = False
                re_data["errorMessage"] = '供应商编号已存在，请修改供应商编号'
            except Supplier.DoesNotExist as e:
                # 插入数据
                await self.application.objects.create(Supplier,
                                                      uk_supplier_no=form.uk_supplier_no.data,
                                                      name=form.name.data,
                                                      person_contact=form.person_contact.data,
                                                      mobile=form.mobile.data,
                                                      province_id=form.province_id.data,
                                                      province=form.province.data,
                                                      city_id=form.city_id.data,
                                                      city=form.city.data,
                                                      district_id=form.district_id.data,
                                                      district=form.district.data,
                                                      address=form.address.data,
                                                      customer_id=form.customer_id.data,
                                                      customer=form.customer.data,
                                                      note=form.note.data,
                                                      create_user_id=self.current_user.id,
                                                      create_user=self.current_user.name
                                                      )
                re_data["success"] = True
                re_data["errorMessage"] = '数据插入成功'
        else:
            for field in form.errors:
                re_data["errorMessage"] = form.errors[field][0]
        await self.finish(re_data)

    @authenticated_async
    async def patch(self, supplier_id, *args, **kwargs):
        # 更新客户
        re_data = {}
        param = self.request.body.decode("utf-8")
        param = json.loads(param)
        form = CreatSupplierForm.from_json(param)
        if form.validate():
            try:
                # 查询客户是否存在
                supplier = await self.application.objects.get(Supplier, id=int(supplier_id))

                supplier.uk_supplier_no = form.uk_supplier_no.data
                supplier.name = form.name.data
                supplier.person_contact = form.person_contact.data
                supplier.mobile = form.mobile.data
                supplier.province_id = form.province_id.data
                supplier.province = form.province.data
                supplier.city_id = form.city_id.data
                supplier.city = form.city.data
                supplier.district_id = form.district_id.data
                supplier.district = form.district.data
                supplier.address = form.address.data
                supplier.customer_id = form.customer_id.data
                supplier.customer = form.customer.data
                supplier.note = form.note.data
                supplier.is_stop = form.is_stop.data
                supplier.modified = datetime.now()

                # 更新数据
                await self.application.objects.update(supplier)
                re_data["success"] = True
                re_data["errorMessage"] = '数据更新成功'

            except Supplier.DoesNotExist as e:
                re_data["success"] = False
                re_data["errorMessage"] = '客户不存在'
        else:
            for field in form.errors:
                re_data["errorMessage"] = form.errors[field][0]
        await self.finish(re_data)

    @authenticated_async
    async def delete(self, supplier_id, *args, **kwargs):
        # 删除供应商数据
        re_data = {}
        try:
            await self.application.objects.get(Supplier, id=int(supplier_id))
            await self.application.objects.execute(Supplier.delete().where(Supplier.id == int(supplier_id)))
            re_data["success"] = True
            re_data["errorMessage"] = "供应商数据删除成功"
        except Supplier.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = "数据不存在"
        await self.finish(re_data)

