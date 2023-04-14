from tornado.web import url
from apps.admin.menu.handler import *

urlpattern = (
    url("/api/menu/list/", MenuHandler),
    url("/api/menu/create/", MenuHandler),
    url("/api/menu/([0-9]+)/", MenuHandler),
)