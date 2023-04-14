from wtforms_tornado import Form
from wtforms import StringField, SelectField, IntegerField, DateTimeField, FieldList, BooleanField
from wtforms.validators import DataRequired, Regexp, AnyOf, NoneOf


class CreatCustomerForm(Form):
    uk_customer_no = StringField("客户编号", validators=[DataRequired(message="请输入客户编号")])
    name = StringField("姓名", validators=[DataRequired(message="请输入姓名")])
    person_contact = StringField("联系人姓名", validators=[NoneOf([])])
    mobile = StringField("手机号码", validators=[NoneOf([])])
    phone = StringField("座机", validators=[NoneOf([])])
    area = FieldList(IntegerField("地址", validators=[NoneOf([])]), min_entries=3, max_entries=3)
    address = StringField("详细地址", validators=[NoneOf([])])
    employee = IntegerField("负责人ID", validators=[NoneOf([])])
    customer_classify = IntegerField("客户分类ID", validators=[NoneOf([])])
    customer_type = IntegerField("客户类型", validators=[NoneOf([])])
    bank = StringField("银行", validators=[NoneOf([])])
    bank_account = IntegerField("银行账户", validators=[NoneOf([])])
    tax_no = StringField("纳税号码", validators=[NoneOf([])])
    note = StringField("备注", validators=[NoneOf([])])
    ar_amount = StringField("期初应收金额", validators=[NoneOf([])])
    ap_amount = StringField("期初应付金额", validators=[NoneOf([])])
    is_stop = BooleanField("是否停用", validators=[NoneOf([])])


class ImportCustomerForm(Form):
    uk_customer_no = StringField("客户编号", validators=[DataRequired(message="请输入客户编号")])
    name = StringField("姓名", validators=[DataRequired(message="请输入姓名")])
    person_contact = StringField("联系人姓名", validators=[NoneOf([])])
    mobile = StringField("手机号码", validators=[NoneOf([])])
    phone = StringField("座机", validators=[NoneOf([])])
    province_id = IntegerField("省id", validators=[NoneOf([])])
    province = StringField("省", validators=[NoneOf([])])
    city_id = IntegerField('市id', validators=[NoneOf([])])
    city = StringField('市', validators=[NoneOf([])])
    district_id = IntegerField('区id', validators=[NoneOf([])])
    district = StringField('区', validators=[NoneOf([])])
    address = StringField("详细地址", validators=[NoneOf([])])
    customer_manager_id = IntegerField("负责人ID", validators=[NoneOf([])])
    customer_manager = StringField("负责人", validators=[NoneOf([])])
    customer_classify_id = IntegerField("客户分类ID", validators=[NoneOf([])])
    customer_classify = StringField("客户分类", validators=[NoneOf([])])
    customer_type = IntegerField("客户类型", validators=[NoneOf([])])
    bank = StringField("银行", validators=[NoneOf([])])
    bank_account = IntegerField("银行账户", validators=[NoneOf([])])
    tax_no = StringField("纳税号码", validators=[NoneOf([])])
    note = StringField("备注", validators=[NoneOf([])])
    ar_amount = StringField("期初应收金额", validators=[NoneOf([])])
    ap_amount = StringField("期初应付金额", validators=[NoneOf([])])
    is_stop = StringField("是否停用", validators=[NoneOf([])])


class CreateCustomerClassifyForm(Form):
    classify_no = StringField("分类编号", validators=[DataRequired(message="请输入分类编号")])
    classify_name = StringField("分类名称", validators=[DataRequired(message="请输入分类名称")])
    parent_id = IntegerField("父级目录id", validators=[NoneOf([])])
    level = IntegerField("层级", validators=[DataRequired(message="请输入层级")])
    status = StringField("是否启用", validators=[DataRequired(message="请选择是否启用")])
    order_num = IntegerField("优先级", validators=[DataRequired(message="请输入优先级")])


class UpdateCustomerClassifyForm(Form):
    id = IntegerField("id", validators=[DataRequired(message="id缺失")])
    classify_no = StringField("分类编号", validators=[DataRequired(message="请输入分类编号")])
    classify_name = StringField("分类名称", validators=[DataRequired(message="请输入分类名称")])
    parent_id = IntegerField("父级目录id", validators=[NoneOf([])])
    level = IntegerField("层级", validators=[DataRequired(message="请输入层级")])
    status = StringField("是否启用", validators=[DataRequired(message="请选择是否启用")])
    order_num = IntegerField("优先级", validators=[DataRequired(message="请输入优先级")])


class CreateAddressClassify(Form):
    classify_no = StringField("分类编号", validators=[DataRequired(message="请输入分类编号")])
    classify_name = StringField("分类名称", validators=[DataRequired(message="请输入分类名称")])
    parent_id = IntegerField("父级目录id", validators=[NoneOf([])])
    level = IntegerField("层级", validators=[DataRequired(message="请输入层级")])
    status = StringField("是否启用", validators=[DataRequired(message="请选择是否启用")])
    order_num = IntegerField("优先级", validators=[DataRequired(message="请输入优先级")])


class UpdateAddressClassify(Form):
    classify_no = StringField("分类编号", validators=[DataRequired(message="请输入分类编号")])
    classify_name = StringField("分类名称", validators=[DataRequired(message="请输入分类名称")])
    parent_id = IntegerField("父级目录id", validators=[NoneOf([])])
    level = IntegerField("层级", validators=[DataRequired(message="请输入层级")])
    status = StringField("是否启用", validators=[DataRequired(message="请选择是否启用")])
    order_num = IntegerField("优先级", validators=[DataRequired(message="请输入优先级")])


class BatchUpdateCustomerForm(Form):
    classify = IntegerField("分类id", validators=[DataRequired(message="请选择分类")])
    customer_ids = FieldList(IntegerField("id", validators=[DataRequired(message="请选择客户")]))