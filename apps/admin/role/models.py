from peewee import *

from wherp.models import BaseModel


class Role(BaseModel):
    name = CharField(max_length=200, verbose_name="角色姓名")
    identifier = CharField(max_length=200, verbose_name="标识符")
    order = IntegerField(verbose_name="优先级")
    disabled = BooleanField(default=False, verbose_name="是否启用")
    expireTime = DateTimeField(null=True, verbose_name="过期时间")
    create_user_id = IntegerField(null=True, verbose_name="创建人id")
    create_user = CharField(null=True, verbose_name="创建人")


class RoleMenus(BaseModel):
    role_id = IntegerField(verbose_name="角色ID")
    menu_id = IntegerField(verbose_name="菜单ID")


class RolePagePermissions(BaseModel):
    role_id = IntegerField(verbose_name="角色ID")
    menu_id = IntegerField(verbose_name="菜单ID")
    page_permissions_id = CharField(verbose_name="页面权限ID")
