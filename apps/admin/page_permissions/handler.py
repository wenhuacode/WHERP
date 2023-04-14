import copy
import json
from datetime import datetime

from wherp.handler import RedisHandler
from wherp.settings import database
from apps.utils.mxform_decorators import authenticated_async
from apps.admin.page_permissions.models import *
from apps.admin.menu.models import Menu
from apps.admin.page_permissions.forms import *
from apps.admin.role.models import RoleMenus, RolePagePermissions
from apps.utils.util_func import json_serial
from playhouse.shortcuts import model_to_dict


class CreateMenuPermissionsHandler(RedisHandler):
    @authenticated_async
    async def patch(self, rold_id, *args, **kwargs):
        re_data = {}
        param = self.request.body.decode("utf-8")
        param = json.loads(param)
        form = CreateMenuPermissions.from_json(param)
        if form.validate():
            async with database.atomic_async():
                await self.application.objects.execute(RolePagePermissions
                                                       .delete()
                                                       .where((RolePagePermissions.role_id == form.role_id.data) &
                                                              (RolePagePermissions.menu_id == form.menu_id.data)))
                await self.application.objects.create(RolePagePermissions,
                                                      role_id=form.role_id.data,
                                                      menu_id=form.menu_id.data,
                                                      page_permissions_id=str(form.page_permissions_id.data))
            re_data["success"] = True
            re_data["errorMessage"] = "保存成功"
        else:
            self.set_status(400)
            for field in form.errors:
                re_data["success"] = False
                re_data["errorMessage"] = form.errors[field][0]
        await self.finish(re_data)


class GetMenuPermissionsHandler(RedisHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        re_data = {}
        data = []
        menu_permissions_data = []
        permissions = await self.application.objects.execute(PagePermissions
                                                             .select(fn.GROUP_CONCAT(PagePermissions.name, '-',
                                                                                     PagePermissions.id)
                                                                     .alias('page_permissions'),
                                                                     PagePermissions.menu_id,
                                                                     Menu.name.alias('menu_name'))
                                                             .join(Menu, join_type=JOIN.RIGHT_OUTER,
                                                                   on=(PagePermissions.menu_id == Menu.id))
                                                             .group_by(PagePermissions.menu_id)
                                                             .dicts())
        for item in permissions:
            tmp_list = []
            item['page_permissions'] = [s.split('-') for s in item['page_permissions'].split(',')]
            item['page_permissions'] = [{item[0]: int(item[1])} for item in item['page_permissions']]
            for dict in item['page_permissions']:
                my_new_dict = {}
                for key, value in dict.items():
                    my_new_dict['label'] = key
                    my_new_dict['value'] = value

                tmp_list.append(my_new_dict)
            item['page_permissions'] = copy.deepcopy(tmp_list)
            tmp_list.clear()
            data.append(item)
        re_data["data"] = data
        re_data["success"] = True
        await self.finish(json.dumps(re_data, default=json_serial))


class PermissionsHandler(RedisHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        re_data = {}
        data = []
        try:
            permissions = await self.application.objects.execute(PagePermissions
                                                                 .select(PagePermissions, Menu.name)
                                                                 .join(Menu,
                                                                       join_type=JOIN.LEFT_OUTER,
                                                                       on=(PagePermissions.menu_id == Menu.id),
                                                                       attr='menu'))
            for item in permissions:
                datas = model_to_dict(item)
                if 'menu' in dir(item):
                    datas['menu_name'] = item.menu.name
                data.append(datas)

            re_data["data"] = data
            re_data["success"] = True

        except PagePermissions.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = "数据不存在"
        await self.finish(json.dumps(re_data, default=json_serial))

    @authenticated_async
    async def post(self, *args, **kwargs):
        re_data = {}
        param = self.request.body.decode("utf-8")
        param = json.loads(param)
        form = CreatPagePermissionsForm.from_json(param)
        if form.validate():
            try:
                await self.application.objects.get(PagePermissions, identifier=form.identifier.data)
                re_data["success"] = False
                re_data["errorMessage"] = "标识符重复，请修改标识符"
            except PagePermissions.DoesNotExist as e:
                await self.application.objects.create(PagePermissions,
                                                      name=form.name.data,
                                                      identifier=form.identifier.data,
                                                      menu_id=form.menu_id.data,
                                                      hide=form.hide.data,
                                                      order=form.order.data,
                                                      create_user_id=self.current_user.id,
                                                      create_user=self.current_user.name, )
                re_data["success"] = True
                re_data["errorMessage"] = "权限创建成功"

        else:
            self.set_status(400)
            for field in form.errors:
                re_data["errorMessage"] = form.errors[field][0]
        await self.finish(re_data)

    @authenticated_async
    async def patch(self, permissions_id, *args, **kwargs):
        # 更新权限信息
        re_data = {}
        param = self.request.body.decode("utf8")
        param = json.loads(param)
        form = CreatPagePermissionsForm.from_json(param)
        if form.validate():
            try:
                permissions = await self.application.objects.get(PagePermissions, id=int(permissions_id))

                permissions.name = form.name.data
                permissions.identifier = form.identifier.data
                permissions.menu_id = form.menu_id.data
                permissions.hide = form.hide.data
                permissions.order = form.order.data
                permissions.modified = datetime.now()

                await self.application.objects.update(permissions)
                re_data["success"] = True

            except PagePermissions.DoesNotExist as e:
                re_data["success"] = False
                re_data["errorMessage"] = "权限不存在"
        else:
            self.set_status(400)
            for field in form.errors:
                re_data["errorMessage"] = form.errors[field][0]
        await self.finish(re_data)

    @authenticated_async
    async def delete(self, permissions_id, *args, **kwargs):
        re_data = {}
        try:
            await self.application.objects.get(PagePermissions, id=int(permissions_id))
            try:
                async with database.atomic_async():
                    await self.application.objects.execute(
                        PagePermissions.delete().where(PagePermissions.id == int(permissions_id)))
                    await self.application.objects.execute(
                        RoleMenus.delete().where(RoleMenus.menu_id == int(permissions_id)))
                    re_data["success"] = True
                    re_data["errorMessage"] = "权限删除成功"
            except Exception as e:
                re_data["success"] = False
                re_data["errorMessage"] = "权限删除失败"
        except PagePermissions.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = "权限不存在"
        await self.finish(re_data)
