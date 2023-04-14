import copy
import json
from datetime import datetime

from WHERP.handler import RedisHandler
from WHERP.settings import database
from apps.admin.role.models import *
from apps.admin.role.forms import *
from apps.admin.menu.models import Menu
from apps.admin.page_permissions.models import PagePermissions
from apps.utils.mxform_decorators import authenticated_async
from apps.utils.util_func import json_serial
from playhouse.shortcuts import model_to_dict


class RoleHandler(RedisHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        re_data = {}
        data = []
        try:
            roles = await self.application.objects.execute(Role.select())
            for role in roles:
                data.append(model_to_dict(role))
            re_data["data"] = data
            re_data["success"] = True

        except Role.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = "数据不存在"
        await self.finish(json.dumps(re_data, default=json_serial))

    @authenticated_async
    async def post(self, *args, **kwargs):
        re_data = {}
        param = self.request.body.decode("utf-8")
        param = json.loads(param)
        form = CreatRoleForm.from_json(param)
        if form.validate():
            name = form.name.data
            identifier = form.identifier.data
            disabled = form.disabled.data
            order = form.order.data
            try:
                identifier = await self.application.objects.get(Role, name=name)
                re_data["success"] = False
                re_data["errorMessage"] = "标识符重复，请修改标识符"
            except Role.DoesNotExist as e:
                await self.application.objects.create(Role, name=name, identifier=identifier, disabled=disabled,
                                                      order=order, create_user_id=self.current_user.id)
                re_data["success"] = True

        else:
            self.set_status(400)
            for field in form.errors:
                re_data[field] = form.errors[field][0]
        await self.finish(re_data)

    @authenticated_async
    async def patch(self, role_id, *args, **kwargs):
        # 更新角色信息
        re_data = {}
        param = self.request.body.decode("utf8")
        param = json.loads(param)
        form = CreatRoleForm.from_json(param)
        if form.validate():
            try:
                roles = await self.application.objects.get(Role, id=int(role_id))

                roles.name = form.name.data
                roles.identifier = form.identifier.data
                roles.disabled = form.disabled.data
                roles.order = form.order.data
                roles.modified = datetime.now()

                await self.application.objects.update(roles)
                re_data["success"] = True

            except Role.DoesNotExist as e:
                re_data["success"] = False
                re_data["errorMessage"] = "角色不存在"

        else:
            self.set_status(400)
            for field in form.errors:
                re_data[field] = form.errors[field][0]
        await self.finish(re_data)

    @authenticated_async
    async def delete(self, role_id, *args, **kwargs):
        re_data = {}
        try:
            await self.application.objects.get(Role, id=int(role_id))
            try:
                async with database.atomic_async():
                    await self.application.objects.execute(Role.delete().where(Role.id == int(role_id)))
                    await self.application.objects.execute(RoleMenus.delete().where(RoleMenus.role_id == int(role_id)))
                    re_data["success"] = True
            except Exception as e:
                re_data["success"] = False
                re_data["errorMessage"] = "更新删除失败"
        except Role.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = "角色不存在"
        await self.finish(re_data)


class RoleMenusHandler(RedisHandler):
    @authenticated_async
    async def get(self, role_id, *args, **kwargs):
        re_data = {}
        menus = []
        page_permissions = {}
        try:
            role_menus = await self.application.objects.execute(RoleMenus.select()
                                                                .where(RoleMenus.role_id == role_id))
            role_per = await self.application.objects.execute(RolePagePermissions
                                                              .select(RolePagePermissions,
                                                                      Menu.name.alias("menu_name"), )
                                                              .join(Menu, join_type=JOIN.RIGHT_OUTER,
                                                                    on=(RolePagePermissions.menu_id == Menu.id))
                                                              .where(RolePagePermissions.role_id == role_id)
                                                              .dicts())
            for menu_id in role_menus:
                menus.append(menu_id.menu_id)

            for item in role_per:
                p_id = json.loads(item['page_permissions_id'])
                menu_per = {item['menu_id']: p_id}
                page_permissions.update(menu_per)
            data = {"menus": menus, "page_permissions": page_permissions}

            re_data["data"] = data
            re_data["success"] = True
        except RoleMenus.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = "数据不存在"
        await self.finish(json.dumps(re_data, default=json_serial))

    @authenticated_async
    async def patch(self, role_id, *args, **kwargs):
        re_data = {}
        param = self.request.body.decode("utf-8")
        param = json.loads(param)
        form = UpdateRoleMenus.from_json(param)
        if form.validate():
            menu = form.menus.data
            try:
                await self.application.objects.get(Role, id=int(role_id))
                async with database.atomic_async():
                    if len(menu) == 0:
                        await self.application.objects.execute(RoleMenus.delete(permanently=True)
                                                               .where(RoleMenus.role_id == int(role_id)))
                        re_data["success"] = True
                        re_data["errorMessage"] = "更新数据成功"
                    else:
                        insert_data = []
                        for data in menu:
                            role_menus = RoleMenus()
                            role_menus.role_id = int(role_id)
                            role_menus.menu_id = int(data)
                            # 深拷贝数据到列表
                            insert_data.append(model_to_dict(role_menus))

                        await self.application.objects.execute(RoleMenus.delete(permanently=True)
                                                               .where(RoleMenus.role_id == int(role_id)))
                        await self.application.objects.execute(RoleMenus.insert_many(insert_data))

                        if 'permissions' in param:
                            await self.application.objects.execute(RolePagePermissions.delete(permanently=True)
                                                                   .where(RolePagePermissions.role_id == int(role_id)))
                            permissions = []
                            for key, value in param['permissions'].items():
                                rp_permissions = RolePagePermissions()
                                rp_permissions.role_id = int(role_id)
                                rp_permissions.menu_id = int(key)
                                rp_permissions.page_permissions_id = str(value)

                                permissions.append(model_to_dict(rp_permissions))
                            await self.application.objects.execute(RolePagePermissions.insert_many(permissions))

                        re_data["success"] = True
            except Exception as e:
                re_data["success"] = False
                re_data["errorMessage"] = "插入数据失败"
            except RoleMenus.DoesNotExist as e:
                re_data["success"] = False
                re_data["errorMessage"] = "角色数据不存在"
        else:
            self.set_status(400)
            for field in form.errors:
                re_data["errorMessage"] = form.errors[field][0]
        await self.finish(json.dumps(re_data, default=json_serial))
