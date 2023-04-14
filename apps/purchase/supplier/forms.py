from wtforms_tornado import Form
from wtforms import StringField, SelectField, IntegerField, DateTimeField, FieldList
from wtforms.validators import DataRequired, Regexp, AnyOf, NoneOf


class CreatSupplierForm(Form):
    uk_supplier_no = StringField("供应商编号", validators=[DataRequired(message="请输入供应商编号")])
    name = StringField("供应商名称", validators=[DataRequired(message="请输入供应商名称")])
    person_contact = StringField("联系人姓名", validators=[NoneOf([])])
    mobile = StringField("手机号码", validators=[NoneOf([])])
    province_id = IntegerField("省id", validators=[NoneOf([])])
    province = StringField("省", validators=[NoneOf([])])
    city_id = IntegerField('市id', validators=[NoneOf([])])
    city = StringField('市', validators=[NoneOf([])])
    district_id = IntegerField('区id', validators=[NoneOf([])])
    district = StringField('区', validators=[NoneOf([])])
    address = StringField('地址', validators=[NoneOf([])])
    customer_id = IntegerField("负责人ID", validators=[NoneOf([])])
    customer = StringField("负责人", validators=[NoneOf([])])
    supplier_type = IntegerField("客户分类", validators=[NoneOf([])])
    bank = StringField("银行", validators=[NoneOf([])])
    bank_account = IntegerField("银行账户", validators=[NoneOf([])])
    tax_no = StringField("纳税号码", validators=[NoneOf([])])
    note = StringField("备注", validators=[NoneOf([])])
    is_stop = StringField("是否停用", validators=[NoneOf([])])


