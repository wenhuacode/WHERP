from wtforms_tornado import Form
from wtforms import StringField, SelectField, IntegerField, DateTimeField, BooleanField
from wtforms.validators import DataRequired, Regexp, AnyOf, NumberRange, NoneOf


class CreatMenuForm(Form):
    name = StringField("菜单名称", validators=[DataRequired(message="请输入菜单名称")])
    icon = StringField("图标名称", validators=[DataRequired(message="请输入图表名称")])
    identifier = StringField("标识符", validators=[DataRequired(message="请输入标识符")])
    path = StringField("菜单路径", validators=[DataRequired(message="请输入菜单路径")])
    parent_id = IntegerField("父级目录id", validators=[NoneOf([])])
    hide = BooleanField("是否隐藏", default=False, validators=[AnyOf([True, False])])
    order = IntegerField("优先级", validators=[DataRequired(message="请输入优先级")])
