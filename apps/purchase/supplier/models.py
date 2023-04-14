from peewee import *
from wherp.models import BaseModel

DISABLE_STATUS = (
    ("0", "正常"),
    ("1", "停用")
)


class Supplier(BaseModel):
    uk_supplier_no = CharField(max_length=255, verbose_name="供应商编号", index=True, unique=True)
    name = CharField(max_length=255, verbose_name="供应商名称", index=True,)
    person_contact = CharField(max_length=20, verbose_name="联系人姓名", null=True)
    mobile = CharField(max_length=11, verbose_name="手机号码", null=True)
    province_id = IntegerField(verbose_name="省id", null=True)
    province = CharField(max_length=40, verbose_name="省", null=True)
    city_id = IntegerField(verbose_name="市id", null=True)
    city = CharField(max_length=40, verbose_name="市", null=True)
    district_id = IntegerField(verbose_name="区id", null=True)
    district = CharField(max_length=40, verbose_name="区", null=True)
    address = CharField(max_length=255, verbose_name="详细地址", null=True)
    customer_id = IntegerField(verbose_name="负责人id", null=True)
    customer = CharField(verbose_name="负责人", null=True)
    ar_amount = DecimalField(default=0, max_digits=14, decimal_places=2, verbose_name="期初应收金额", null=True)
    ap_amount = DecimalField(default=0, max_digits=14, decimal_places=2, verbose_name="期初应付金额", null=True)
    note = TextField(verbose_name="备注", null=True)
    is_stop = CharField(choices=DISABLE_STATUS, default="0", null=True, verbose_name="是否停用")
    create_user_id = IntegerField(verbose_name="创建人id")
    create_user = CharField(verbose_name="创建人")


class SupplierAccountCurrent(BaseModel):
    order_no = CharField(max_length=60, verbose_name="单据编号", null=True, index=True)
    order_type = CharField(max_length=20, default="采购单", verbose_name="单据类型", null=True,)
    supplier_id = IntegerField(verbose_name="供应商编号", null=True, index=True)
    supplier = CharField(max_length=255, verbose_name="供应商名称", null=True,)
    date = DateField(verbose_name="发生日期", formats='%Y-%m-%d', null=True)
    add_amount = DecimalField(default=0, max_digits=14, decimal_places=2, verbose_name="增加金额", null=True)
    sub_amount = DecimalField(default=0, max_digits=14, decimal_places=2, verbose_name="减少金额", null=True)
    note = TextField(verbose_name="备注", null=True)
    create_user_id = IntegerField(verbose_name="创建人id")
    create_user = CharField(verbose_name="创建人")
