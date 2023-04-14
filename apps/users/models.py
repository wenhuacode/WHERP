from peewee import *
from bcrypt import hashpw, gensalt

from WHERP.models import BaseModel


class PasswordHash(bytes):
    def check_password(self, password):
        password = password.encode('utf-8')
        return hashpw(password, self) == self


class PasswordField(BlobField):
    def __init__(self, iterations=12, *args, **kwargs):
        if None in (hashpw, gensalt):
            raise ValueError('Missing library required for PasswordField: bcrypt')
        self.bcrypt_iterations = iterations
        self.raw_password = None
        super(PasswordField, self).__init__(*args, **kwargs)

    def db_value(self, value):
        """Convert the python value for storage in the database."""
        if isinstance(value, PasswordHash):
            return bytes(value)

        if isinstance(value, str):
            value = value.encode('utf-8')
        salt = gensalt(self.bcrypt_iterations)
        return value if value is None else hashpw(value, salt)

    def python_value(self, value):
        """Convert the database value to a pythonic value."""
        if isinstance(value, str):
            value = value.encode('utf-8')

        return PasswordHash(value)


class Employee(BaseModel):
    phone = CharField(max_length=11, verbose_name="手机号码", index=True, unique=True)
    # 1. 密文, 2.不可反解
    password = PasswordField(verbose_name="密码")
    name = CharField(max_length=20, verbose_name="姓名")
    employee_classify_id = IntegerField(null=True, verbose_name="公司分类ID")
    employee_classify = CharField(max_length=255, verbose_name="公司分类名称", null=True)
    employee_classify_path = CharField(max_length=255, verbose_name="路径", null=True)
    department = CharField(max_length=20, verbose_name="部门")
    notify_count = IntegerField(default=0, null=True, verbose_name="通知数")
    unread_count = IntegerField(default=0, null=True, verbose_name="未读计数")
    status = BooleanField(default=False, null=True, verbose_name="状态")
    create_user_id = IntegerField(null=True, verbose_name="创建人id")
    create_user = CharField(null=True, verbose_name="创建人")


class Employeeclassify(BaseModel):
    classify_no = CharField(max_length=24, verbose_name="分类编号", index=True, unique=True)
    classify_name = CharField(max_length=24, verbose_name="分类名称", index=True)
    parent_id = IntegerField(default=0, verbose_name="父级目录id", null=True)
    level = IntegerField(default=0, verbose_name="层级", null=True)
    parent_path = CharField(max_length=255, verbose_name="路径", null=True)
    status = CharField(default='1', verbose_name="是否启用", null=True)
    order_num = IntegerField(verbose_name="优先级", null=True)
    create_user_id = IntegerField(verbose_name="创建人id")
    create_user = CharField(verbose_name="创建人")


class EmployeeRoles(BaseModel):
    employee_id = IntegerField(verbose_name="员工ID")
    role_id = IntegerField(verbose_name="角色ID")
