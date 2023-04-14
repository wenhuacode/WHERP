import json
from datetime import datetime

from WHERP.handler import RedisHandler
from WHERP.settings import database
from apps.utils.mxform_decorators import authenticated_async
from apps.admin.menu.models import Menu
from apps.admin.menu.forms import CreatMenuForm
from apps.admin.role.models import RoleMenus
from apps.utils.util_func import json_serial
from apps.utils.FindMenu import find_menu
from playhouse.shortcuts import model_to_dict


class MenuHandler(RedisHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        re_data = {}
        data = []
        try:
            menu = await self.application.objects.execute(Menu.select())
            for menus in menu:
                data.append(model_to_dict(menus))
            data = await find_menu(data)

            re_data["data"] = data
            re_data["success"] = True

        except Menu.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = "数据不存在"
        await self.finish(json.dumps(re_data, default=json_serial))

    @authenticated_async
    async def post(self, *args, **kwargs):
        re_data = {}
        param = self.request.body.decode("utf-8")
        param = json.loads(param)
        form = CreatMenuForm.from_json(param)
        if form.validate():
            try:
                await self.application.objects.get(Menu, identifier=form.identifier.data)
                re_data["success"] = False
                re_data["errorMessage"] = "标识符重复，请修改标识符"
            except Menu.DoesNotExist as e:
                await self.application.objects.create(Menu, name=form.name.data,
                                                      icon=form.icon.data,
                                                      identifier=form.identifier.data,
                                                      path=form.path.data,
                                                      parent_id=form.parent_id.data,
                                                      hide=form.hide.data,
                                                      order=form.order.data,
                                                      create_user_id=self.current_user.id )
                re_data["success"] = True
                re_data["errorMessage"] = "菜单创建成功"

        else:
            self.set_status(400)
            for field in form.errors:
                re_data[field] = form.errors[field][0]
        await self.finish(re_data)

    @authenticated_async
    async def patch(self, menu_id, *args, **kwargs):
        # 更新菜单信息
        re_data = {}
        param = self.request.body.decode("utf8")
        param = json.loads(param)
        form = CreatMenuForm.from_json(param)
        if form.validate():
            try:
                menus = await self.application.objects.get(Menu, id=int(menu_id))

                menus.name = form.name.data
                menus.icon = form.icon.data
                menus.identifier = form.identifier.data
                menus.path = form.path.data
                menus.parent_id = form.parent_id.data
                menus.hide = form.hide.data
                menus.order = form.order.data
                menus.modified = datetime.now()

                await self.application.objects.update(menus)
                re_data["success"] = True

            except Menu.DoesNotExist as e:
                re_data["success"] = False
                re_data["errorMessage"] = "菜单不存在"

        else:
            self.set_status(400)
            for field in form.errors:
                re_data[field] = form.errors[field][0]
        await self.finish(re_data)

    @authenticated_async
    async def delete(self, menu_id, *args, **kwargs):
        re_data = {}
        try:
            menus = await self.application.objects.get(Menu, id=int(menu_id))
            try:
                async with database.atomic_async():
                    await self.application.objects.execute(Menu.delete().where(Menu.id == int(menu_id)))
                    await self.application.objects.execute(RoleMenus.delete(permanently=True).where(RoleMenus.menu_id == int(menu_id)))
                    re_data["success"] = True
                    re_data["errorMessage"] = "更新删除成功"
            except Exception as e:
                re_data["success"] = False
                re_data["errorMessage"] = "更新删除失败"
        except Menu.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = "菜单不存在"
        await self.finish(re_data)
