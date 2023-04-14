from tornado.web import url
from apps.users.handler import *

urlpattern = (
    url("/api/login/captcha/", SmsHandler),
    url("/api/register/", RegisterHandler),
    url("/api/login/account/", LoginHandler),
    url("/api/login/currentUser/", CurrentUserHandler),
    url("/api/login/outLogin/", OutLoginHandler),

    url("/api/employee/", EmployeeHandler),
    url("/api/employee/([0-9]+)/", EmployeeHandler),
    url("/api/employee/menus/", EmployeeMenusHandler),
    url("/api/employee_classify/list/", EmployeeMenu),
    url("/api/employee_classify/create/", EmployeeMenu),
    url("/api/employee_classify/update/", EmployeeMenu),
    url("/api/employee_classify/delete/([0-9]+)/", EmployeeMenu),
    url("/api/import/", ImportHandler),
)