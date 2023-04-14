from wtforms_tornado import Form
from wtforms import StringField, SelectField, IntegerField, DateField, FieldList, FloatField, DecimalField
from wtforms.validators import DataRequired, Regexp, AnyOf, NoneOf


class CreateOrderForm(Form):
    order_no = StringField('订单编号', validators=[DataRequired(message="请输入订单")])
    order_name = StringField("订单名称", validators=[DataRequired(message="请输入订单名称")])
    storehouse_id = IntegerField("仓库ID", validators=[DataRequired(message="请输入仓库ID")])
    storehouse_name = StringField("仓库名称", validators=[DataRequired(message="请输入仓库名称")])
    supplier_id = IntegerField("供应商ID", validators=[DataRequired(message="请输入供应商ID")])
    supplier = StringField("供应商名称", validators=[DataRequired(message="请输入供应商名称")])
    employee_id = IntegerField("经手人ID", validators=[DataRequired(message="请输入经手人")])
    employee = StringField("经手人", validators=[DataRequired(message="请输入经手人")])
    signed_data = DateField('订单日期', validators=[DataRequired(message='订单日期')])
    total_sales_amount = StringField('产品合计金额', validators=[DataRequired(message="产品合计金额出错")])
    order_discount = StringField('整单折扣率', validators=[DataRequired(message="整单折扣率出错")])
    order_qty = IntegerField("数量", validators=[DataRequired(message="产品数量")])
    express_fee = StringField("快递费", validators=[NoneOf([])])
    discount_amount = StringField("优惠金额", validators=[DataRequired(message="优惠金额出错")])
    order_amount = StringField("订单金额", validators=[DataRequired(message="请输入订单金额")])
    person_contact = StringField("联系人", validators=[DataRequired(message="请输入联系人")])
    mobile = StringField("联系电话", validators=[DataRequired(message="请输入联系电话")])
    note = StringField('摘要', validators=[NoneOf([])])