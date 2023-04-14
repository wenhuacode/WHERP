from peewee import *
from wherp.models import BaseModel

from apps.inventory_management.inventory_distribution_cost.models import StorehouseManagement
from apps.customer.customer_handler.models import Customer
from apps.users.models import Employee
from apps.product.product_handler.models import Product
from apps.finance.accounting_subject.models import AccountingSubject


IS_FREE_GIFT = (
    (0, False),
    (1, True)
)


class OrderIndex(BaseModel):
    order_no = CharField(max_length=255, verbose_name="订单编号", index=True, unique=True)
    order_type = IntegerField(verbose_name="订单类型",)
    storehouse_id = IntegerField(verbose_name="仓库id", null=True)
    rs_storehouse = IntegerField(verbose_name="仓库id", null=True)
    customer_id = IntegerField(verbose_name="客户id", null=True)
    employee_id = IntegerField(verbose_name="经手人id", null=True)
    signed_data = DateField(verbose_name="签订日期", formats='%Y-%m-%d', null=True)
    order_state = IntegerField(default=1, verbose_name="订单状态", null=True)
    is_push_jst = BooleanField(choices=IS_FREE_GIFT, default=False, verbose_name="是否推送聚水潭", null=True)
    order_qty = IntegerField(verbose_name="销售数量", null=True)
    total_sales_amount = DecimalField(default=0, max_digits=18, decimal_places=4, verbose_name="销售总金额", null=True)
    order_discount = FloatField(verbose_name="折扣", null=True)
    express_fee = DecimalField(default=0, max_digits=18, decimal_places=4, verbose_name="快递费", null=True)
    discount_amount = DecimalField(default=0, max_digits=18, decimal_places=4, verbose_name="优惠金额", null=True)
    order_amount = DecimalField(default=0, max_digits=18, decimal_places=4, verbose_name="订单金额", null=True)
    note = TextField(verbose_name="摘要", null=True)
    contact_person = CharField(max_length=20, verbose_name="联系人", null=True)
    phone_number = CharField(max_length=20, verbose_name="联系电话", null=True)
    province_id = IntegerField(verbose_name="省id", null=True)
    city_id = IntegerField(verbose_name="市id", null=True)
    district_id = IntegerField(verbose_name="区id", null=True)
    address = CharField(max_length=255, verbose_name="详细地址", null=True)
    delivery_status = CharField(max_length=20, verbose_name="聚水潭发货状态", null=True)
    courier_company = SmallIntegerField(verbose_name="物流公司", null=True)
    courier_number = CharField(max_length=30, verbose_name="快递号码", null=True)
    bank_account = SmallIntegerField(verbose_name="银行账户", null=True)
    rp_amount = DecimalField(default=0, max_digits=18, decimal_places=4, verbose_name="金额", null=True)
    create_user_id = IntegerField(verbose_name="创建人id")
    checked_user = IntegerField(verbose_name="审核人", null=True)

    @classmethod
    def extend(cls):
        # 没有参数就返回全部数据并分页
        create_user = Employee.alias()
        return cls.select(cls, StorehouseManagement.storehouse_name, Customer.id, Customer.name, create_user.name,).join(
            StorehouseManagement, join_type=JOIN.LEFT_OUTER, on=(cls.storehouse_id == StorehouseManagement.id),
            attr='storehouse').switch(cls).join(
            Customer, join_type=JOIN.LEFT_OUTER, on=(cls.customer_id == Customer.id), attr='Customer').switch(cls).join(
            create_user, join_type=JOIN.LEFT_OUTER, on=(cls.employee_id == create_user.id), attr='create_user')


class OrderDetail(BaseModel):
    order_no = CharField(max_length=255, verbose_name="订单编号", index=True)
    order_type = IntegerField(verbose_name="订单类型")
    barcode = CharField(max_length=255, verbose_name="产品条码", null=True)
    qty = IntegerField(verbose_name="数量", null=True)
    box_qty = FloatField(verbose_name="箱数量", null=True)
    box_rules = IntegerField(default=0, verbose_name="箱规", null=True)
    discount = FloatField(verbose_name="折扣", null=True)
    discount_price = DecimalField(default=0, max_digits=18, decimal_places=4, verbose_name="折扣价格", null=True)
    discount_total = DecimalField(default=0, max_digits=18, decimal_places=2, verbose_name="总折后金额", null=True)
    price = DecimalField(default=0, max_digits=18, decimal_places=4, verbose_name="单价", null=True)
    total = DecimalField(default=0, max_digits=18, decimal_places=2, verbose_name="总计", null=True)
    is_free_gift = BooleanField(choices=IS_FREE_GIFT, default=False, null=True, verbose_name="是否赠品")
    note = TextField(verbose_name="备注", null=True)

    @classmethod
    def extend(cls):
        return cls.select(cls, Product.name, ).join(
            Product, join_type=JOIN.LEFT_OUTER, on=(cls.barcode == Product.barcode), attr='product')

    @classmethod
    def extend_other(cls):
        return cls.select(cls, AccountingSubject.name).join(
            AccountingSubject, join_type=JOIN.LEFT_OUTER, on=(cls.barcode == AccountingSubject.as_no),
            attr='accounting_subject')


class OrderDetailAccount(BaseModel):
    order_no = CharField(max_length=255, verbose_name="订单编号", index=True)
    order_type = IntegerField(verbose_name="订单类型")
    storehouse_id = IntegerField(verbose_name="仓库id", null=True)
    rs_storehouse = IntegerField(verbose_name="备用仓库", null=True)
    customer_id = IntegerField(verbose_name="客户id", null=True)
    employee_id = IntegerField(verbose_name="经手人id", null=True)
    signed_data = DateField(verbose_name="审核日期", formats='%Y-%m-%d', null=True)
    order_state = IntegerField(verbose_name="订单状态", null=True)
    barcode = CharField(max_length=255, verbose_name="产品条码", null=True)
    qty = IntegerField(verbose_name="数量", null=True)
    box_qty = FloatField(verbose_name="箱数量", null=True)
    box_rules = IntegerField(default=0, verbose_name="箱规", null=True)
    discount = FloatField(verbose_name="折扣", null=True)
    discount_price = DecimalField(default=0, max_digits=18, decimal_places=4, verbose_name="折扣单价", null=True)
    discount_total = DecimalField(default=0, max_digits=18, decimal_places=2, verbose_name="总折后金额", null=True)
    cost_price = DecimalField(default=0, max_digits=18, decimal_places=4, verbose_name="成本单价", null=True)
    cost_total = DecimalField(default=0, max_digits=18, decimal_places=2, verbose_name="总成本金额", null=True)
    price = DecimalField(default=0, max_digits=18, decimal_places=4, verbose_name="单价", null=True)
    total = DecimalField(default=0, max_digits=18, decimal_places=2, verbose_name="总计", null=True)
    is_free_gift = BooleanField(choices=IS_FREE_GIFT, null=True, verbose_name="是否赠品")
    note = TextField(verbose_name="备注", null=True)
    checked_user_id = IntegerField(verbose_name="审核人id")


class SubsidiaryLedger(BaseModel):
    order_type = CharField(max_length=24, verbose_name='单据类型')
    date = DateField(verbose_name="日期", formats='%Y-%m-%d', null=True)
    order_no = CharField(max_length=255, verbose_name='单据编号')
    employee_id = IntegerField(verbose_name="员工id", index=True, null=True)
    as_id = CharField(verbose_name="科目id", index=True, null=True)
    customer_id = IntegerField(verbose_name="客户id", null=True)
    amount = DecimalField(max_digits=14, decimal_places=2, verbose_name="金额", null=True)
    note = TextField(verbose_name="备注", null=True)
    create_user_id = IntegerField(verbose_name="创建人id")

