from peewee import *

from wherp.models import BaseModel


class SubsidiaryLedger(BaseModel):
    order_type = IntegerField(verbose_name='单据类型')
    date = DateField(verbose_name="日期", formats='%Y-%m-%d', null=True)
    order_no = CharField(max_length=255, verbose_name='单据编号')
    employee_id = IntegerField(verbose_name="员工id", index=True, null=True)
    as_id = CharField(verbose_name="科目id", index=True, null=True)
    customer_id = IntegerField(verbose_name="客户id", null=True)
    amount = DecimalField(max_digits=14, decimal_places=2, verbose_name="金额", null=True)
    note = TextField(verbose_name="备注", null=True)
    create_user_id = IntegerField(verbose_name="创建人id")
