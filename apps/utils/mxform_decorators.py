import functools
import jwt

from apps.users.models import Employee


def authenticated_async(method):
    @functools.wraps(method)
    async def wrapper(self, *args, **kwargs):
        re_data = {}
        AccessToken = self.request.headers.get("Access_Token", None)
        if AccessToken:
            try:
                try:
                    send_data = jwt.decode(AccessToken, self.settings["secret_key"], leeway=self.settings["jwt_expire"],
                                           options={"verify_exp": True}, algorithms=['HS256'])
                    user_id = send_data["id"]
                    # 从数据库中获取到user并设置给_current_user
                    try:
                        user = await self.application.objects.get(Employee
                                                                  .select(Employee.id, Employee.phone, Employee.name,
                                                                          Employee.department, Employee.notify_count,
                                                                          Employee.unread_count, Employee.status,
                                                                          Employee.create_user_id,
                                                                          Employee.create_user,), id=user_id)
                        self._current_user = user
                        # 此处很关键
                        await method(self, *args, **kwargs)
                    except Employee.DoesNotExist as e:
                        self.set_status(401)
                except jwt.DecodeError as e:
                    self.set_status(401)
                    re_data["success"] = False
                    re_data["errorMessage"] = '账户未登录'
                    await self.finish(re_data)
            except jwt.ExpiredSignatureError as e:
                self.set_status(401)
        else:
            self.set_status(401)
    return wrapper