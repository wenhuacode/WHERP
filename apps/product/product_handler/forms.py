from wtforms_tornado import Form
from wtforms import StringField, SelectField, IntegerField, DateTimeField, FieldList, DecimalField, FormField
from wtforms.validators import DataRequired, Regexp, AnyOf, NoneOf


class CreatProductForm(Form):
    product_no = StringField("产品编号", validators=[DataRequired(message="请输入产品编号")])
    name = StringField("产品名称", validators=[DataRequired(message="请输入产品名称")])
    barcode = StringField("产品条码", validators=[DataRequired(message="请输入产品条码")])
    product_classify_id = IntegerField("产品分类ID", validators=[NoneOf([])])
    product_classify_path = StringField("路径", validators=[NoneOf([])])
    product_classify = StringField("产品分类名称", validators=[NoneOf([])])
    price = DecimalField("单价", validators=[NoneOf([])])
    cost = DecimalField("成本", validators=[NoneOf([])])
    box_rules = IntegerField("箱规", validators=[NoneOf([])])
    validity = IntegerField("有效期天数", validators=[NoneOf([])])
    product_introduction = StringField("产品简介", validators=[NoneOf([])])
    supplier_id = IntegerField("供应商ID", validators=[NoneOf([])])
    supplier = StringField("供应商", validators=[NoneOf([])])
    is_stop = StringField("是否停用", validators=[NoneOf([])])


class CreateProductClassify(Form):
    classify_no = StringField("分类编号", validators=[DataRequired(message="请输入分类编号")])
    classify_name = StringField("分类名称", validators=[DataRequired(message="请输入分类名称")])
    parent_id = IntegerField("父级目录id", validators=[NoneOf([])])
    level = IntegerField("层级", validators=[DataRequired(message="请输入层级")])
    # parent_path = StringField("路径", validators=[DataRequired(message="请输入路径")])
    status = StringField("是否启用", validators=[DataRequired(message="请选择是否启用")])
    order_num = IntegerField("优先级", validators=[DataRequired(message="请输入优先级")])


class UpdateProductClassify(Form):
    id = IntegerField("id", validators=[DataRequired(message="id缺失")])
    classify_no = StringField("分类编号", validators=[DataRequired(message="请输入分类编号")])
    classify_name = StringField("分类名称", validators=[DataRequired(message="请输入分类名称")])
    parent_id = IntegerField("父级目录id", validators=[NoneOf([])])
    level = IntegerField("层级", validators=[DataRequired(message="请输入层级")])
    # parent_path = StringField("路径", validators=[DataRequired(message="请输入路径")])
    status = StringField("是否启用", validators=[DataRequired(message="请选择是否启用")])
    order_num = IntegerField("优先级", validators=[DataRequired(message="请输入优先级")])


class BatchUpdateProductForm(Form):
    classify = IntegerField("分类id", validators=[DataRequired(message="请选择分类")])
    product_ids = FieldList(IntegerField("id", validators=[DataRequired(message="请选择客户")]))