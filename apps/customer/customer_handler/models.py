from peewee import *
from WHERP.models import BaseModel

DISABLE_STATUS = (
    ("0", "正常"),
    ("1", "停用")
)


class CustomerClassify(BaseModel):
    classify_no = CharField(max_length=24, verbose_name="分类编号", index=True, unique=True)
    classify_name = CharField(max_length=24, verbose_name="分类名称", index=True)
    parent_id = IntegerField(default=0, verbose_name="父级目录id", null=True)
    level = IntegerField(default=0, verbose_name="层级", null=True)
    parent_path = CharField(max_length=255, verbose_name="路径", null=True)
    status = CharField(default='1', verbose_name="是否启用", null=True)
    order_num = IntegerField(verbose_name="优先级", null=True)
    create_user_id = IntegerField(verbose_name="创建人id")

    @classmethod
    def extend(cls, path):
        return cls.select(cls.id).where(cls.parent_path.contains(path))


class Customer(BaseModel):
    uk_customer_no = CharField(max_length=255, verbose_name="客户编号", index=True, unique=True)
    name = CharField(max_length=255, verbose_name="姓名")
    person_contact = CharField(max_length=20, verbose_name="联系人姓名", null=True)
    mobile = CharField(max_length=11, verbose_name="手机号码", null=True)
    phone = CharField(max_length=15, verbose_name="座机", null=True)
    province_id = IntegerField(verbose_name="省id", null=True)
    city_id = IntegerField(verbose_name="市id", null=True)
    district_id = IntegerField(verbose_name="区id", null=True)
    address = CharField(max_length=255, verbose_name="详细地址", null=True)
    employee = IntegerField(verbose_name="负责人id", null=True)
    customer_classify = IntegerField(verbose_name="客户分类id", null=True)
    customer_type = CharField(max_length=255, verbose_name="客户类型", null=True)
    bank = CharField(max_length=20, verbose_name="开户银行", null=True)
    bank_account = CharField(max_length=255, verbose_name="银行账户", null=True)
    tax_no = CharField(max_length=255, verbose_name="纳税号码", null=True)
    ar_amount = DecimalField(default=0, max_digits=14, decimal_places=2, verbose_name="应收金额", null=True)
    ap_amount = DecimalField(default=0, max_digits=14, decimal_places=2, verbose_name="应付金额", null=True)
    note = TextField(verbose_name="备注", null=True)
    is_stop = BooleanField(default=False, null=True)
    parent_id = IntegerField(default=0, null=True, verbose_name="上级客户id")
    create_user_id = IntegerField(verbose_name="创建人id")

    @classmethod
    def extend(cls):
        return cls.select(cls, CustomerClassify.classify_name).where().join(CustomerClassify, join_type=JOIN.LEFT_OUTER,
                                                                       on=(cls.customer_classify == CustomerClassify.id),
                                                                       attr='CustomerClassify')


class AddressClassify(BaseModel):
    classify_no = CharField(max_length=24, verbose_name="分类编号", index=True, unique=True)
    classify_name = CharField(max_length=24, verbose_name="分类名称", index=True)
    parent_id = IntegerField(default=0, verbose_name="父级目录id", null=True)
    level = IntegerField(default=0, verbose_name="层级", null=True)
    parent_path = CharField(max_length=255, verbose_name="路径", null=True)
    status = CharField(default='1', verbose_name="是否启用", null=True)
    order_num = IntegerField(verbose_name="优先级", null=True)
    create_user_id = IntegerField(verbose_name="创建人id")

    @classmethod
    def extend(cls, province_id, city_id, district_id):
        return cls.select(fn.GROUP_CONCAT(cls.classify_name)).where(
            (cls.id == int(province_id)) | (cls.id == int(city_id)) | (cls.id == int(district_id)))


class CustomerAccountCurrent(BaseModel):
    order_no = CharField(max_length=60, verbose_name="单据编号", null=True, index=True)
    order_type = CharField(max_length=20, default="销售单", verbose_name="单据类型", null=True, )
    customer_id = IntegerField(verbose_name="客户编号", null=True, index=True)
    customer = CharField(max_length=255, verbose_name="客户名称", null=True, )
    date = DateField(verbose_name="发生日期", formats='%Y-%m-%d', null=True)
    add_amount = DecimalField(default=0, max_digits=14, decimal_places=2, verbose_name="增加金额", null=True)
    sub_amount = DecimalField(default=0, max_digits=14, decimal_places=2, verbose_name="减少金额", null=True)
    note = TextField(verbose_name="备注", null=True)
    create_user_id = IntegerField(verbose_name="创建人id")
    create_user = CharField(verbose_name="创建人")


class CustomerFollowUpRecord(BaseModel):
    pass
