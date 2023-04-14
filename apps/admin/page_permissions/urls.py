from tornado.web import url
from apps.admin.page_permissions.handler import *

urlpattern = (
    url("/api/page_permissions/list/", PermissionsHandler),
    url("/api/page_permissions/create/", PermissionsHandler),
    url("/api/page_permissions/([0-9]+)/", PermissionsHandler),

    url("/api/page_permissions/get_menu_permissions/", GetMenuPermissionsHandler),
    url("/api/page_permissions/create_menu_permissions/([0-9]+)/", CreateMenuPermissionsHandler)
)