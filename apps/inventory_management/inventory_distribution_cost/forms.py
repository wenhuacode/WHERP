from wtforms_tornado import Form
from wtforms import StringField, SelectField, IntegerField, DateTimeField, FieldList, DecimalField
from wtforms.validators import DataRequired, Regexp, AnyOf, NoneOf


# 创建仓库验证
class CreateStorehouseManagement(Form):
    storehouse_no = StringField("仓库编号", validators=[DataRequired(message="请输入仓库编号")])
    storehouse_name = StringField("仓库名称", validators=[DataRequired(message="请输入仓库名称")])
    employee_id = IntegerField("负责人id", validators=[NoneOf([])])
    employee = StringField("负责人姓名", validators=[NoneOf([])])
    is_stop = StringField("是否停用", validators=[NoneOf([])])
    note = StringField("备注", validators=[NoneOf([])])
    jst_storehouse_no = StringField("聚水潭仓库编号", validators=[NoneOf([])])