from wtforms_tornado import Form
from wtforms import StringField, FormField, IntegerField, DateField, FieldList, FloatField, DecimalField, BooleanField
from wtforms.validators import DataRequired, Regexp, AnyOf, NoneOf, NumberRange


class TableDataForm(Form):
    order_no = StringField("订单编号", validators=[DataRequired(message="请输入订单编号")])
    order_type = StringField('订单类型', validators=[DataRequired(message="订单类型为空")])
    barcode = StringField('科目编号', validators=[DataRequired(message="科目编号")])
    discount_total = FloatField("合计金额", validators=[NumberRange(message="合计金额")])
    note = StringField('摘要')


class FinanceOrderForms(Form):
    order_no = StringField("订单编号", validators=[DataRequired(message="请输入订单编号")])
    order_type = StringField('订单类型', validators=[DataRequired(message="订单类型为空")])
    order_amount = FloatField("合计金额", validators=[NumberRange(message="合计金额")])
    customer_id = IntegerField("客户ID", validators=[NoneOf([])])
    employee_id = IntegerField("经手人ID", validators=[DataRequired(message="请输入经手人")])
    signed_data = DateField('订单日期', validators=[DataRequired(message='订单日期')])
    note = StringField('摘要')
    bank_account = IntegerField("银行账户", validators=[NoneOf([])])
    rp_amount = FloatField("收付金额", validators=[NoneOf([])])
    table = FieldList(FormField(TableDataForm))
