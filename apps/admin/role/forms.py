from wtforms_tornado import Form
from wtforms import StringField, SelectMultipleField, IntegerField, DateTimeField, BooleanField, FieldList
from wtforms.validators import DataRequired, Regexp, AnyOf, NoneOf


class CreatRoleForm(Form):
    name = StringField("菜单名称", validators=[DataRequired(message="请输入菜单名称")])
    identifier = StringField("标识符", validators=[DataRequired(message="请输入标识符")])
    disabled = BooleanField("是否启用", default=False, validators=[AnyOf([True, False])])
    order = IntegerField("优先级", validators=[DataRequired(message="请输入优先级")])


class UpdateRoleMenus(Form):
    menus = FieldList(IntegerField("菜单id", validators=[NoneOf([])]))
