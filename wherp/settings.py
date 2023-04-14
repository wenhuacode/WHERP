import os

import peewee as pw
import peewee_async
from peewee_async import PooledMySQLDatabase as AsyncPooledMySQLDatabase
# 断线重连+连接池
from playhouse.shortcuts import ReconnectMixin

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
settings = {
    "port": 8888,
    "template_path": "templates",  # 全局路径
    "secret_key": "mfTWa6DkQ@h8lDyx",
    "jwt_expire": 7*24*3600,
    "MEDIA_ROOT": os.path.join(BASE_DIR, "media"),
    "SITE_URL": "http://127.0.0.1:8888",
    "redis": {
        "host": "127.0.0.1",
        "port": 6379,
    },
    "company": {
        "name": "WH-ERP",
        "init_name": "WH"
    },
}


db_config = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': 'root',
    'database': 'wh-erp',
}


OP_MAP = {
            "id": pw.OP.EQ,
            "name": pw.OP.ILIKE,
            "barcode": pw.OP.ILIKE,
            "order_no": pw.OP.ILIKE,
            "order_type": pw.OP.EQ,
            "order_state": pw.OP.EQ,
            "signed_data": pw.OP.BETWEEN,
            "customer_name": pw.OP.ILIKE,
            "storehouse_id": pw.OP.EQ,
            "customer_classify": pw.OP.IN,
            "employee_id": pw.OP.EQ,
            "employee": pw.OP.EQ,
            "note": pw.OP.ILIKE,
            "contact_person": pw.OP.ILIKE,
            "phone_number": pw.OP.ILIKE,
            "province_id": pw.OP.EQ,
            "city_id": pw.OP.EQ,
            "district_id": pw.OP.EQ,
            "create_user_id": pw.OP.EQ,
            "startTime": pw.OP.GTE,
            "endTime": pw.OP.LTE,

            "is_stop": pw.OP.EQ,
            'customer_manager': pw.OP.EQ,
            "mobile": pw.OP.ILIKE,
            "uk_customer_no": pw.OP.EQ,
        }


class ReconnectAsyncPooledMySQLDatabase(ReconnectMixin, AsyncPooledMySQLDatabase):
    pass


# 数据库实例
database = ReconnectAsyncPooledMySQLDatabase(**db_config)

# 设置数据库同步
database.set_allow_sync(False)  # 设置是否同步
objects = peewee_async.Manager(database)