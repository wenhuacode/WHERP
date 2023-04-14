import copy
import json
from datetime import datetime

from random import choice
import jwt

from wherp.handler import RedisHandler
from apps.users.models import *
from apps.admin.menu.models import Menu
from apps.admin.role.models import RoleMenus, RolePagePermissions
from apps.users.forms import *
from apps.utils.AsyncYunPian import AsyncYunPian
from apps.utils.mxform_decorators import authenticated_async
from apps.utils.util_func import json_serial
from apps.utils.FindMenu import find_menu
from wherp.settings import database
from playhouse.shortcuts import model_to_dict


def query_employee(RealName=None, Phone=None, Department=None, IsStop=None):
    queryList = []
    if RealName is not None:
        queryList.append(Employee.name.contains(str(RealName)))
    if Phone is not None:
        queryList.append(Employee.phone.contains(str(Phone)))
    if Department is not None:
        queryList.append((Employee.department.contains(str(Department))))
    if IsStop is not None:
        queryList.append((Employee.isStop.contains(str(IsStop))))
    query = queryList[0]
    for data in queryList[1:]:
        query = query & data
    query = Employee.select().where(query)
    return query


class ImportHandler(RedisHandler):

    @authenticated_async
    async def get(self, *args, **kwargs):
        # 获取所有用户
        re_data = {}
        data = []

        RealName = self.get_argument("realName", None)
        Phone = self.get_argument("phone", None)
        Department = self.get_argument("department", None)
        IsStop = self.get_argument("isStop", None)

        # 没有参数就返回全部数据并分页
        if RealName == None and Phone == None and Department == None and IsStop == None:
            employees = await self.application.objects.execute(Employee.select())
            for employee in employees:
                item_data = {
                    "name": employee.name,
                    "phone": employee.phone,
                    "department": employee.department,
                    "isStop": employee.isStop,
                    "UserNo": employee.id,
                    "currentAuthority": employee.currentAuthority,
                }
                data.append(item_data)
            re_data['data'] = data
            re_data["success"] = "True"
            await self.finish(json.dumps(re_data, default=json_serial))
        else:
            # 有参数就判断参数添加情况，并拼接sql
            Query_employee = query_employee(RealName, Phone, Department, IsStop)
            employees = await self.application.objects.execute(Query_employee)

            for employee in employees:
                item_data = {
                    "name": employee.name,
                    "phone": employee.phone,
                    "department": employee.department,
                    "isStop": employee.isStop,
                    "UserNo": employee.id,
                    "currentAuthority": employee.currentAuthority,
                }
                data.append(item_data)
            re_data['data'] = data
            await self.finish(json.dumps(re_data, default=json_serial))

    @authenticated_async
    async def post(self, *args, **kwargs):
        re_data = {}
        param = self.request.body.decode("utf-8")
        param = json.loads(param)
        for data in param:
            form = CreatEmployee.from_json(data)
            if form.validate():
                insert_data = []
                tem_data = {}
                for data in param:
                    tem_data["name"] = data["realName"]
                    tem_data["phone"] = data["phone"]
                    tem_data["currentAuthority"] = data["role"]
                    tem_data["department"] = data["department"]
                    tem_data["password"] = data["password"]
                    tem_data["isStop"] = data["isStop"]

                    # 深拷贝数据到列表
                    insert_data.append(copy.deepcopy(tem_data))
                    # 清空列表
                    tem_data.clear()
                try:
                    # 事务批量插入
                    async with database.atomic_async():
                        await self.application.objects.execute(Employee.insert_many(insert_data))
                    re_data["success"] = True
                except Exception as e:
                    re_data["success"] = False
                    re_data["errorMessage"] = e.args[1]
            else:
                self.set_status(400)
                for field in form.errors:
                    re_data[field] = form.errors[field][0]
        await self.finish(re_data)


class EmployeeMenu(RedisHandler):
    async def get(self, *args, **kwargs):
        # 查询公司分类信息
        re_data = {}
        data = []
        # 获取redis内存 菜单权限
        if (product_classify := await self.redis_conn.get('公司分类信息')) is not None:
            data = json.loads(product_classify)
            re_data["data"] = data
            re_data["success"] = True
        else:
            menu_data = await self.application.objects.execute(Employeeclassify.select())
            for item in menu_data:
                data.append(model_to_dict(item))
            data = await find_menu(data)
            # 产品分类信息权限存入redis
            await self.redis_conn.set('公司分类信息',
                                      json.dumps(data, default=json_serial), ex=1)
            re_data["data"] = data
            re_data["success"] = True
        await self.finish(json.dumps(re_data, default=json_serial))

    @authenticated_async
    async def delete(self, employee_classify_id, *args, **kwargs):
        # 删除公司分类
        re_data = {}
        try:
            await self.application.objects.get(Employeeclassify, id=int(employee_classify_id))
            employee_classify_child = await self.application.objects.execute(Employeeclassify
                                                                             .select()
                                                                             .where(Employeeclassify.parent_id ==
                                                                                    int(employee_classify_id)))
            employee_classify = await self.application.objects.execute(Employee
                                                                       .select()
                                                                       .where(Employee.employee_classify_id ==
                                                                              int(employee_classify_id)))
            if len(employee_classify_child) == 0 and len(employee_classify) == 0:
                await self.application.objects.execute(Employeeclassify.delete().where(Employeeclassify.id ==
                                                                                       int(employee_classify_id)))
                re_data["success"] = True
                re_data["errorMessage"] = '分类删除成功'
            else:
                re_data["success"] = False
                re_data["errorMessage"] = '分类下存在数据，无法删除'
        except Employeeclassify.DoesNotExist as e:
            re_data["success"] = False
            re_data["errorMessage"] = '分类不存在'
        await self.finish(re_data)

    @authenticated_async
    async def post(self, *args, **kwargs):
        re_data = {}
        param = self.request.body.decode("utf8")
        param = json.loads(param)
        form = CreateEmployeeClassify.from_json(param)
        if form.validate():
            try:
                await self.application.objects.get(Employeeclassify, classify_no=str(form.classify_no.data))
                re_data["success"] = False
                re_data["errorMessage"] = '分类编号重复'
            except Employeeclassify.DoesNotExist as e:
                if form.parent_id.data != 0:
                    try:
                        pi_path = await self.application.objects.get(Employeeclassify, id=form.parent_id.data)
                        async with database.atomic_async():
                            product_classify = await self.application.objects.create(Employeeclassify,
                                                                                     classify_no=form.classify_no.data,
                                                                                     classify_name=form.classify_name.data,
                                                                                     parent_id=form.parent_id.data,
                                                                                     level=form.level.data,
                                                                                     status=form.status.data,
                                                                                     order_num=form.order_num.data,
                                                                                     create_user_id=self.current_user.id,
                                                                                     create_user=self.current_user.name)
                            product_classify.parent_path = str(pi_path.parent_path) + str(product_classify.id) + '/'
                            await self.application.objects.update(product_classify)
                    except Employeeclassify.DoesNotExist as e:
                        re_data["success"] = False
                        re_data["errorMessage"] = '上级目录不存在'
                else:
                    async with database.atomic_async():
                        product_classify = await self.application.objects.create(Employeeclassify,
                                                                                 classify_no=form.classify_no.data,
                                                                                 classify_name=form.classify_name.data,
                                                                                 parent_id=form.parent_id.data,
                                                                                 level=form.level.data,
                                                                                 status=form.status.data,
                                                                                 order_num=form.order_num.data,
                                                                                 create_user_id=self.current_user.id,
                                                                                 create_user=self.current_user.name)
                        product_classify.parent_path = str(product_classify.id) + '/'
                        await self.application.objects.update(product_classify)
                re_data["success"] = True
                re_data["errorMessage"] = '分类新建成功'
        else:
            for field in form.errors:
                re_data["errorMessage"] = form.errors[field][0]
        await self.finish(re_data)

    @authenticated_async
    async def patch(self, *args, **kwargs):
        # 更新公司分类
        re_data = {}
        param = self.request.body.decode("utf8")
        param = json.loads(param)
        form = UpdateEmployeeClassify.from_json(param)
        if form.validate():
            try:
                employee_classify = await self.application.objects.get(Employeeclassify, id=int(form.id.data))
                employee_classify.classify_no = form.classify_no.data
                employee_classify.classify_name = form.classify_name.data
                employee_classify.status = form.status.data
                employee_classify.order_num = form.order_num.data

                await self.application.objects.update(employee_classify)
                re_data["success"] = True
                re_data["errorMessage"] = '分类更新成功'

            except Employeeclassify.DoesNotExist as e:
                re_data["success"] = False
                re_data["errorMessage"] = '分类不存在'
        else:
            for field in form.errors:
                re_data["errorMessage"] = form.errors[field][0]
        await self.finish(re_data)


class EmployeeHandler(RedisHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        # 获取所有员工
        re_data = {}
        datas = []
        data = []
        current = self.get_argument("current", None)
        pageSize = self.get_argument("pageSize", None)
        name = self.get_argument("name", None)
        phone = self.get_argument("phone", None)
        department = self.get_argument("department", None)
        status = self.get_argument("status", None)

        # 没有参数就返回全部数据并分页
        if name == None and phone == None and department == None and status == None:

            employees = await self.application.objects.execute(Employee
                                                               .select(Employee.id,
                                                                       Employee.phone,
                                                                       Employee.name,
                                                                       Employee.employee_classify_id,
                                                                       Employee.notify_count,
                                                                       Employee.unread_count,
                                                                       Employee.status,
                                                                       Employee.create_user_id,
                                                                       fn.GROUP_CONCAT(EmployeeRoles.role_id)
                                                                       .alias('role_id'))
                                                               .join(EmployeeRoles, join_type=JOIN.LEFT_OUTER,
                                                                     on=(Employee.id == EmployeeRoles.employee_id),
                                                                     attr="employeeRoles")
                                                               .group_by(Employee))
            total = await self.application.objects.count(Employee.select())
            for employee in employees:
                data = (model_to_dict(employee))
                data['roles'] = (str(employee.role_id)).split(',')
                datas.append(data)
            re_data["data"] = datas
            re_data["total"] = total
            re_data["page"] = current
            re_data["success"] = True
        else:
            # 有参数就判断参数添加情况，并拼接sql
            Query_employee = query_employee(name, phone, department, status)
            employees = await self.application.objects.execute(Query_employee.paginate(int(current), int(pageSize)))
            total = await self.application.objects.count(Query_employee)

            for employee in employees:
                data.append(model_to_dict(employee))
            re_data["data"] = data
            re_data["total"] = total
            re_data["page"] = current
            re_data["success"] = True
        await self.finish(json.dumps(re_data, default=json_serial))

    @authenticated_async
    async def patch(self, user_id, *args, **kwargs):
        # 用户信息更新
        re_data = {}
        param = self.request.body.decode("utf8")
        param = json.loads(param)
        form = CreatEmployee.from_json(param)
        if form.validate():
            try:
                employee = await self.application.objects.get(Employee, id=user_id)
                employee.name = form.name.data
                employee.phone = form.phone.data
                employee.status = form.status.data
                employee.password = form.password.data
                employee.employee_classify_id = form.employee_classify_id.data
                role = form.roles.data

                try:
                    async with database.atomic_async():
                        await self.application.objects.update(employee)
                        await self.application.objects.execute(EmployeeRoles.delete(permanently=True)
                                                               .where(EmployeeRoles.employee_id == int(user_id)))
                        if len(role) == 0:
                            re_data["success"] = True
                            re_data["errorMessage"] = "更新数据成功"
                        else:
                            insert_data = []
                            item_data = {}
                            for data in role:
                                item_data["employee_id"] = int(user_id)
                                item_data["role_id"] = int(data)
                                # 深拷贝数据到列表
                                insert_data.append(copy.deepcopy(item_data))
                                # 清空列表
                                item_data.clear()
                            await self.application.objects.execute(EmployeeRoles.delete()
                                                                   .where(EmployeeRoles.employee_id == int(user_id)))
                            await self.application.objects.execute(EmployeeRoles.insert_many(insert_data))
                            re_data["success"] = True
                            re_data["errorMessage"] = "更新数据成功"
                except Exception as e:
                    re_data["success"] = False
                    re_data["errorMessage"] = "更新数据失败"

            except Employee.DoesNotExist as e:
                self.set_status(404)
        else:
            self.set_status(400)
            for field in form.errors:
                re_data[field] = form.errors[field][0]
        await self.finish(re_data)

    @authenticated_async
    async def delete(self, employee_id, *args, **kwargs):
        # 删除员工
        re_data = {}
        try:
            await self.application.objects.get(Employee, id=int(employee_id))
            try:
                async with database.atomic_async():
                    await self.application.objects.execute(Employee.delete()
                                                           .where(Employee.id == int(employee_id)))
                    await self.application.objects.execute(EmployeeRoles.delete()
                                                           .where(EmployeeRoles.employee_id == int(employee_id)))
                    re_data["success"] = True
                    re_data["errorMessage"] = "更新数据成功"

            except Exception as e:
                re_data["success"] = False
                re_data["errorMessage"] = "删除失败"

        except Employee.DoesNotExist as e:
            self.set_status(404)
            re_data["message"] = "员工不存在"
        await self.finish(re_data)

    @authenticated_async
    async def post(self, *args, **kwargs):
        # 新增员工
        re_data = {}
        param = self.request.body.decode("utf-8")
        param = json.loads(param)
        form = CreatEmployee.from_json(param)
        if form.validate():
            role = form.roles.data
            try:
                await self.application.objects.get(Employee, phone=form.phone.data)
                re_data["success"] = False
                re_data["data"] = {}
                re_data["errorMessage"] = '手机号码已存在，请修改手机号码'
            except Employee.DoesNotExist as e:
                try:
                    async with database.atomic_async():
                        user = await self.application.objects.create(Employee,
                                                                     name=form.name.data,
                                                                     phone=form.phone.data,
                                                                     password=form.password.data,
                                                                     department=form.department.data,
                                                                     status=form.status.data, )
                        insert_data = []
                        item_data = {}
                        for data in role:
                            item_data["employee_id"] = int(user.id)
                            item_data["role_id"] = int(data)
                            # 深拷贝数据到列表
                            insert_data.append(copy.deepcopy(item_data))
                            # 清空列表
                            item_data.clear()
                        await self.application.objects.execute(EmployeeRoles.insert_many(insert_data))
                    re_data["success"] = True
                    re_data["errorMessage"] = "插入数据成功"
                except Exception as e:
                    re_data["success"] = False
                    re_data["errorMessage"] = "插入数据失败"
        else:
            self.set_status(400)
            for field in form.errors:
                re_data[field] = form.errors[field][0]
        await self.finish(re_data)


class OutLoginHandler(RedisHandler):
    @authenticated_async
    async def post(self, *args, **kwargs):
        re_data = {}
        re_data["data"] = {}
        re_data["success"] = True
        await self.finish(re_data)


class CurrentUserHandler(RedisHandler):
    @authenticated_async
    async def get(self, *args, **kwargs):
        # 获取当前用户信息
        user = self.current_user
        re_data = {}

        re_data["data"] = model_to_dict(user)
        re_data["success"] = True
        await self.finish(json.dumps(re_data, default=json_serial))


class EmployeeMenusHandler(RedisHandler):
    @authenticated_async
    async def get(self):
        # 获取当前用户信息
        re_data = {}
        roles_list = []
        menu_no = []
        menu_data = []
        permissions_id = []
        # 获取redis内存 菜单权限
        if (user_menu := await self.redis_conn.get('{}用户菜单权限'.format(self.current_user.id))) is not None:
            data = json.loads(user_menu)
            re_data["data"] = data
            re_data["success"] = True
        else:
            employee_roles = await self.application.objects.execute(EmployeeRoles.select()
                                                                    .where(EmployeeRoles.employee_id ==
                                                                           self.current_user.id))
            # 查询用户角色
            for roles in employee_roles:
                roles_list.append(roles.role_id)
            # 查询角色所拥有的菜单并去重
            for role in roles_list:
                if role is None:
                    break
                try:
                    role_menus = await self.application.objects.execute(RoleMenus.select()
                                                                        .where(RoleMenus.role_id == int(role)))
                    for menus in role_menus:
                        menu_no.append(menus.menu_id)
                    # 去重 排序
                    new_menu_no = list(set(menu_no))
                    new_menu_no.sort(key=menu_no.index)
                except RoleMenus.DoesNotExist as e:
                    re_data["success"] = False
                    re_data["errorMessage"] = "数据不存在"
                    break
            # 查询角色拥有的按钮权限
            role_menu_permissions = await self.application.objects.execute(RolePagePermissions
                                                                           .select()
                                                                           .where(RolePagePermissions
                                                                                  .role_id.in_(roles_list)))
            for permissions in role_menu_permissions:
                for item in json.loads(permissions.page_permissions_id):
                    permissions_id.append(item)
            try:
                user_menus = await self.application.objects.execute(Menu.select().where(Menu.id.in_(menu_no)))
                for menu in user_menus:
                    menu_data.append(model_to_dict(menu))
                # 预先处理排序
                menu_data.sort(key=lambda x: (x['identifier']))
                data = await find_menu(menu_data)
                # 处理排序
                data.sort(key=lambda x: (x['identifier']))
                # 用户权限存入redis
                await self.redis_conn.set('{}用户菜单权限'.format(self.current_user.id),
                                          json.dumps(data, default=json_serial), ex=1)
                re_data["data"] = data
                re_data["permissions_id"] = permissions_id
                re_data["success"] = True
            except RoleMenus.DoesNotExist as e:
                re_data["success"] = False
                re_data["errorMessage"] = "数据不存在"
        await self.finish(json.dumps(re_data, default=json_serial))


class LoginHandler(RedisHandler):
    async def post(self, *args, **kwargs):
        re_data = {}

        param = self.request.body.decode("utf-8")
        param = json.loads(param)
        if param["type"] == "account":
            form = LoginFormUserName.from_json(param)

            if form.validate():
                username = form.username.data
                password = form.password.data

                try:
                    user = await self.application.objects.get(Employee, name=username)
                    if not user.password.check_password(password):
                        re_data["success"] = False
                        re_data["errorMessage"] = "手机号或密码错误"
                    else:
                        if not user.status:
                            re_data["success"] = False
                            re_data["errorMessage"] = "帐号未通过审核"
                        else:
                            # 生成json web token
                            payload = {
                                "id": user.id,
                                "name": user.name,
                                "exp": datetime.utcnow()
                            }
                            token = jwt.encode(payload, self.settings["secret_key"], algorithm="HS256")

                            re_data["id"] = user.id
                            re_data["name"] = user.name
                            re_data["token"] = token
                            re_data["success"] = True
                except Employee.DoesNotExist as e:
                    re_data["success"] = False
                    re_data["errorMessage"] = "用户不存在"
            else:
                for field in LoginFormUserName.errors:
                    re_data[field] = LoginFormUserName[field][0]

        elif param["type"] == "mobile":
            form = LoginFormPhone.from_json(param)

            if form.validate():
                phone = form.phone.data
                captcha = form.captcha.data

                try:
                    user = await self.application.objects.get(Employee, phone=phone)
                    redis_key = "{}_{}".format(phone, captcha)
                    if not await self.redis_conn.get(redis_key):
                        re_data["success"] = False
                        re_data["errorMessage"] = "验证码错误或者失效"
                    else:
                        if user.status == False:
                            re_data["success"] = False
                            re_data["errorMessage"] = "帐号未通过审核"
                        else:
                            # 登录成功 生成json web token
                            payload = {
                                "id": user.id,
                                "name": user.name,
                                "exp": datetime.utcnow()
                            }
                            token = jwt.encode(payload, self.settings["secret_key"], algorithm="HS256")
                            re_data["id"] = user.id
                            re_data["name"] = user.name
                            re_data["token"] = token
                            re_data["success"] = True
                except Employee.DoesNotExist as e:
                    re_data["success"] = False
                    re_data["errorMessage"] = "用户不存在"
            else:
                re_data["success"] = False
                for field in LoginFormPhone.errors:
                    re_data["errorMessage"] = LoginFormPhone[field][0]
        else:
            re_data["success"] = False
            re_data["errorMessage"] = "登录失败"
        await self.finish(re_data)


class RegisterHandler(RedisHandler):
    async def post(self, *args, **kwargs):
        re_data = {}

        param = self.request.body.decode("utf-8")
        param = json.loads(param)
        form = RegisterForm.from_json(param)
        if form.validate():
            # 验证码是否正确
            redis_key = "{}_{}".format(form.phone.data, form.captcha.data)
            if not await self.redis_conn.get(redis_key):
                re_data["success"] = False
                re_data["errorMessage"] = "验证码错误或者失效"
            else:
                # 验证用户是否存在
                try:
                    await self.application.objects.get(Employee, phone=form.phone.data)
                    re_data["success"] = False
                    re_data["errorMessage"] = "用户已存在"
                except Employee.DoesNotExist as e:
                    user = await self.application.objects.create(Employee,
                                                                 phone=form.phone.data,
                                                                 password=form.password.data,
                                                                 name=form.name.data,
                                                                 employee_classify_id=form.employee_classify_id.data,
                                                                 employee_classify_path=form.employee_classify_path.data,
                                                                 employee_classify=form.employee_classify.data, )
                    re_data["success"] = True
                    re_data["errorMessage"] = "注册成功, 请联系管理员审核"
                    re_data["id"] = user.id
        else:
            re_data["success"] = False
            for field in form.errors:
                re_data["errorMessage"] = form.errors[field][0]
        await self.finish(re_data)


class SmsHandler(RedisHandler):
    def generate_code(self):
        """
        生成随机4位数字验证码
        :return:
        """
        seeds = "1234567890"
        random_str = []
        for i in range(4):
            random_str.append(choice(seeds))
        return "".join(random_str)

    async def post(self, *args, **kwargs):
        re_data = {}

        param = self.request.body.decode("utf-8")
        param = json.loads(param)
        sms_form = SmsCodeForm.from_json(param)
        if sms_form.validate():
            mobile = sms_form.phone.data
            code = self.generate_code()
            yun_pian = AsyncYunPian("keys")

            re_json = await yun_pian.send_single_sms(code, mobile)
            if re_json["code"] != 0:
                re_data["success"] = False
                re_data["errorMessage"] = re_json["msg"]
            else:
                # 将验证码写入到redis中
                await self.redis_conn.set("{}_{}".format(mobile, code), 1, 100 * 60)
                re_data["code"] = code
        else:
            re_data["success"] = False
            for field in sms_form.errors:
                re_data["errorMessage"] = sms_form.errors[field][0]

        await self.finish(re_data)
