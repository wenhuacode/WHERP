from peewee import *

from wherp.models import BaseModel


class AccountingSubject(BaseModel):
    as_no = CharField(max_length=24, verbose_name="科目编号", index=True, unique=True)
    name = CharField(max_length=24, verbose_name="科目名称", index=True)
    parent_id = IntegerField(default=0, verbose_name="父级目录id", null=True)
    level = IntegerField(default=0, verbose_name="层级", null=True)
    parent_path = CharField(max_length=255, verbose_name="路径", null=True)
    status = CharField(default='1', verbose_name="是否启用", null=True)
    order_num = IntegerField(verbose_name="优先级", null=True)
    initial_balance = DecimalField(default=0.00, max_digits=14, decimal_places=2, verbose_name="期初金额", null=True)
    create_user_id = IntegerField(verbose_name="创建人id")
    create_user = CharField(verbose_name="创建人")
