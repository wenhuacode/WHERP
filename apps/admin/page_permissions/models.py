from peewee import *

from WHERP.models import BaseModel


class PagePermissions(BaseModel):
    name = CharField(max_length=200, verbose_name="权限名称")
    identifier = CharField(max_length=200, verbose_name="标识符")
    menu_id = IntegerField(default=0, verbose_name="所属菜单")
    hide = BooleanField(default=False, verbose_name="是否隐藏")
    order = IntegerField(verbose_name="优先级")
    create_user_id = IntegerField(null=True, verbose_name="创建人id")
    create_user = CharField(null=True, verbose_name="创建人")