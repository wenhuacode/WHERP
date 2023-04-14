from wtforms_tornado import Form
from wtforms import StringField, FormField, IntegerField, DateField, FieldList, FloatField, DecimalField, BooleanField
from wtforms.validators import DataRequired, Regexp, AnyOf, NoneOf, NumberRange


class InventoryTableDataForm(Form):
    order_type = StringField('订单类型', validators=[DataRequired(message="订单类型为空")])
    barcode = StringField("产品条码", validators=[DataRequired(message="请输入产品条码")])
    qty = IntegerField("产品数量", validators=[DataRequired(message="请输入产品数量")])
    price = FloatField("单价", validators=[NumberRange(message="单价出错")])
    discount = FloatField("折扣", validators=[NoneOf([])])
    discount_price = FloatField("折后单价",  validators=[NumberRange(message="折后单价出错")])
    discount_total = FloatField("折后金额",  validators=[NumberRange(message="折后金额出错")])
    is_free_gift = BooleanField("是否赠品", validators=[NoneOf([])])
    box_qty = FloatField("箱数量", validators=[NumberRange(message="箱数量出错")])
    box_rules = IntegerField("箱规", validators=[NumberRange(message="箱规出错")])
    total = FloatField("合计金额", validators=[NumberRange(message="合计金额出错")])
    note = StringField('摘要')
    order_no = StringField("订单编号", validators=[DataRequired(message="请输入订单编号")])


class CreateInventoryOrderForm(Form):
    order_no = StringField('订单编号', validators=[DataRequired(message="请输入订单编号")])
    order_type = StringField('订单类型', validators=[DataRequired(message="订单类型为空")])
    storehouse_id = IntegerField("仓库ID", validators=[DataRequired(message="请输入仓库ID")])
    rs_storehouse = IntegerField("仓库ID", validators=[NoneOf([])])
    employee_id = IntegerField("经手人ID", validators=[DataRequired(message="请输入经手人")])
    signed_data = DateField('订单日期', validators=[DataRequired(message='订单日期')])
    is_push_jst = BooleanField('是否推送聚水潭', validators=[NoneOf([])])
    total_sales_amount = FloatField('产品合计金额', validators=[NumberRange(message="产品合计金额出错")])
    order_discount = FloatField('整单折扣率', validators=[NumberRange(message="整单折扣率出错")])
    order_qty = IntegerField("数量", validators=[DataRequired(message="产品数量")])
    express_fee = DecimalField("快递费", validators=[NumberRange(message="快递费字段出错")])
    discount_amount = FloatField("优惠金额", validators=[NumberRange(message="请输入优惠金额")])
    order_amount = FloatField("订单金额", validators=[NumberRange(message="请输入订单金额")])
    note = StringField('摘要', validators=[NoneOf([])])
    table = FieldList(FormField(InventoryTableDataForm))