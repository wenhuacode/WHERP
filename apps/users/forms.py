from wtforms_tornado import Form
from wtforms import StringField, PasswordField, SelectField, IntegerField, FieldList, BooleanField, SelectMultipleField
from wtforms.validators import DataRequired, Regexp, AnyOf, NoneOf

MOBILE_REGEX = "^1[34578]\d{9}$"


class SmsCodeForm(Form):
    phone = StringField("手机号码",
                        validators=[DataRequired(message="请输入手机号码"), Regexp(MOBILE_REGEX, message="请输入合法的手机号码")])


class LoginFormUserName(Form):
    username = StringField("姓名", validators=[DataRequired(message="请输入姓名")])
    password = PasswordField("密码", validators=[DataRequired(message="请输入密码")])


class LoginFormPhone(Form):
    phone = StringField("手机号码",
                        validators=[DataRequired(message="请输入手机号码"), Regexp(MOBILE_REGEX, message="请输入合法的手机号码")])
    captcha = StringField("验证码", validators=[DataRequired(message="请输入验证码")])


class RegisterForm(Form):
    phone = StringField("手机号码",
                        validators=[DataRequired(message="请输入手机号码"), Regexp(MOBILE_REGEX, message="请输入合法的手机号码")])

    captcha = StringField("验证码", validators=[DataRequired(message="请输入验证码")])
    password = PasswordField("密码", validators=[DataRequired(message="请输入密码")])
    name = StringField("姓名", validators=[DataRequired(message="请输入姓名")])
    employee_classify_id = IntegerField("部门分类ID", validators=[NoneOf([])])
    employee_classify_path = StringField("路径", validators=[NoneOf([])])
    employee_classify = StringField("部门分类名称", validators=[NoneOf([])])


class CreatEmployee(Form):
    phone = StringField("手机号码",
                        validators=[DataRequired(message="请输入手机号码"), Regexp(MOBILE_REGEX, message="请输入合法的手机号码")])
    name = StringField("姓名", validators=[DataRequired(message="请输入姓名")])
    roles = FieldList(StringField("角色id", validators=[NoneOf([])]))
    status = BooleanField("状态", default=True, validators=[AnyOf([True, False])])
    password = PasswordField("密码", validators=[DataRequired(message="请输入密码")])
    employee_classify_id = IntegerField("部门分类ID", validators=[NoneOf([])])


class UpdateEmployeeRoles(Form):
    employee_id = IntegerField("员工ID", validators=[DataRequired(message="请输入员工id")])
    roles = FieldList(StringField("角色id", validators=[DataRequired(message="请选择角色id")]))


class CreateEmployeeClassify(Form):
    classify_no = StringField("分类编号", validators=[DataRequired(message="请输入分类编号")])
    classify_name = StringField("分类名称", validators=[DataRequired(message="请输入分类名称")])
    parent_id = IntegerField("父级目录id", validators=[NoneOf([])])
    level = IntegerField("层级", validators=[DataRequired(message="请输入层级")])
    # parent_path = StringField("路径", validators=[DataRequired(message="请输入路径")])
    status = StringField("是否启用", validators=[DataRequired(message="请选择是否启用")])
    order_num = IntegerField("优先级", validators=[DataRequired(message="请输入优先级")])


class UpdateEmployeeClassify(Form):
    id = IntegerField("id", validators=[DataRequired(message="id缺失")])
    classify_no = StringField("分类编号", validators=[DataRequired(message="请输入分类编号")])
    classify_name = StringField("分类名称", validators=[DataRequired(message="请输入分类名称")])
    parent_id = IntegerField("父级目录id", validators=[NoneOf([])])
    level = IntegerField("层级", validators=[DataRequired(message="请输入层级")])
    # parent_path = StringField("路径", validators=[DataRequired(message="请输入路径")])
    status = StringField("是否启用", validators=[DataRequired(message="请选择是否启用")])
    order_num = IntegerField("优先级", validators=[DataRequired(message="请输入优先级")])
