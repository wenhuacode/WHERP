from wtforms_tornado import Form
from wtforms import StringField, SelectMultipleField, IntegerField, FormField, BooleanField, FieldList, Form, validators
from wtforms.validators import DataRequired, Regexp, AnyOf, NumberRange, NoneOf


class CreatPagePermissionsForm(Form):
    name = StringField("权限名称", validators=[DataRequired(message="请输入权限名称")])
    identifier = StringField("标识符", validators=[DataRequired(message="请输入标识符")])
    menu_id = IntegerField("所属菜单", validators=[DataRequired(message="请输入所属菜单")])
    hide = BooleanField("是否隐藏", default=False, validators=[AnyOf([True, False])])
    order = IntegerField("优先级", validators=[DataRequired(message="请输入优先级")])


# 自定义验证器函数，用于验证嵌套列表
def validate_nested_list(form, field):
    for value in field.data:
        if not isinstance(value, list):
            raise validators.ValidationError('Field must contain a nested list.')
        if not all(isinstance(item, int) for item in value):
            raise validators.ValidationError('Nested list must contain only integers.')


# 自定义验证器函数，用于验证嵌套字典
def validate_nested_dict(form, field):
    for key, value in field.data.items():
        if not isinstance(key, int):
            raise validators.ValidationError('Dictionary keys must be integers.')
        if not isinstance(value, list):
            raise validators.ValidationError('Dictionary values must be lists.')
        if not all(isinstance(item, int) for item in value):
            raise validators.ValidationError('Nested lists must contain only integers.')


# 定义包含嵌套列表的表单字段
class NestedListForm(Form):
    my_field = FieldList(
        validators=[validate_nested_list],
        unbound_field=IntegerField,)


class CreateMenuPermissions(Form):
    page_permissions_id = FormField(NestedListForm, validators=[validate_nested_dict])