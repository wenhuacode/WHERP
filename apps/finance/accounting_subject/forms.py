from wtforms_tornado import Form
from wtforms import StringField, SelectField, IntegerField, DateTimeField, BooleanField, DateField
from wtforms.validators import DataRequired, Regexp, AnyOf, NumberRange, NoneOf


class CreateAccountingSubjectForm(Form):
    as_no = StringField("科目编号", validators=[DataRequired(message="请输入科目编号")])
    name = StringField("科目名称", validators=[DataRequired(message="请输入科目名称")])
    parent_id = IntegerField("父级目录id", validators=[NoneOf([])])
    level = IntegerField("层级", validators=[DataRequired(message="请输入层级")])
    # parent_path = StringField("路径", validators=[DataRequired(message="请输入路径")])
    status = StringField("是否启用", validators=[DataRequired(message="请选择是否启用")])
    order_num = IntegerField("优先级", validators=[DataRequired(message="请输入优先级")])
    initial_balance = StringField('期初金额', validators=[DataRequired(message="请输入期初金额")])


class UpdateAccountingSubjectForm(Form):
    id = IntegerField("id", validators=[DataRequired(message="id缺失")])
    as_no = StringField("科目编号", validators=[DataRequired(message="请输入科目编号")])
    name = StringField("科目名称", validators=[DataRequired(message="请输入科目名称")])
    parent_id = IntegerField("父级目录id", validators=[NoneOf([])])
    level = IntegerField("层级", validators=[DataRequired(message="请输入层级")])
    # parent_path = StringField("路径", validators=[DataRequired(message="请输入路径")])
    status = StringField("是否启用", validators=[DataRequired(message="请选择是否启用")])
    order_num = IntegerField("优先级", validators=[DataRequired(message="请输入优先级")])
    initial_balance = StringField('期初金额', validators=[NoneOf([])])