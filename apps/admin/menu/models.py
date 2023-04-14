from peewee import *

from wherp.models import BaseModel


class Menu(BaseModel):
    name = CharField(max_length=200, verbose_name="菜单姓名")
    icon = CharField(max_length=200, verbose_name="图标名称")
    identifier = CharField(max_length=200, verbose_name="标识符")
    path = CharField(max_length=200, verbose_name="路径")
    parent_id = IntegerField(default=0, verbose_name="父级目录id")
    hide = BooleanField(default=False, verbose_name="是否隐藏")
    order = IntegerField(verbose_name="优先级")
    type = CharField(null=True, verbose_name="菜单类型")
    create_user_id = IntegerField(null=True, verbose_name="创建人id")
    create_user = CharField(null=True, verbose_name="创建人")