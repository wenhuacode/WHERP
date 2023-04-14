from tornado.web import url
from apps.admin.role.handler import *

urlpattern = (
    url("/api/role/list/", RoleHandler),
    url("/api/role/create/", RoleHandler),
    url("/api/role/([0-9]+)/", RoleHandler),
    url("/api/role/([0-9]+)/menus/", RoleMenusHandler),
)