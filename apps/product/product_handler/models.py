from peewee import *
from wherp.models import BaseModel
from apps.inventory_management.inventory_distribution_cost.models import IrProperty
from apps.inventory_management.inventory_distribution_cost.models import StorehouseManagement


class Product(BaseModel):
    product_no = CharField(max_length=255, verbose_name="产品编号", index=True, unique=True)
    name = CharField(max_length=255, verbose_name="产品名称")
    barcode = CharField(max_length=255, verbose_name="产品条码", index=True, unique=True)
    product_image = CharField(max_length=255, verbose_name="产品图片", null=True)
    product_classify_id = IntegerField(null=True, verbose_name="产品分类ID")
    product_classify_path = CharField(max_length=255, verbose_name="路径", null=True)
    product_classify = CharField(max_length=255, verbose_name="产品分类名称", null=True)
    price = DecimalField(default=0, max_digits=14, decimal_places=4, verbose_name="单价", null=True)
    cost = DecimalField(default=0, max_digits=14, decimal_places=4, verbose_name="分析成本", null=True)
    box_rules = IntegerField(default=0, verbose_name="箱规", null=True)
    validity = IntegerField(default=0, verbose_name="保质期", null=True)
    product_introduction = TextField(verbose_name="产品简介", null=True)
    supplier_id = IntegerField(null=True, verbose_name="供应商ID")
    supplier = CharField(max_length=255, null=True, verbose_name="供应商名称")
    rec_price = DecimalField(default=0, max_digits=14, decimal_places=4, verbose_name="最新进价", null=True)
    create_user_id = IntegerField(verbose_name="创建人id")
    create_user = CharField(verbose_name="创建人")

    @classmethod
    def extend(cls):
        return cls.select(
            cls, fn.sum(IrProperty.qty).alias('qty'), IrProperty.cost_price).join(
            IrProperty, join_type=JOIN.LEFT_OUTER, on=(cls.barcode == IrProperty.barcode),
            attr='inventory').join(StorehouseManagement, join_type=JOIN.LEFT_OUTER,
                                   on=(IrProperty.storehouse_id == StorehouseManagement.id)).group_by(cls)


class ProductClassify(BaseModel):
    classify_no = CharField(max_length=24, verbose_name="分类编号", index=True, unique=True)
    classify_name = CharField(max_length=24, verbose_name="分类名称", index=True)
    parent_id = IntegerField(default=0, verbose_name="父级目录id", null=True)
    level = IntegerField(default=0, verbose_name="层级", null=True)
    parent_path = CharField(max_length=255, verbose_name="路径", index=True, null=True)
    status = CharField(default='1', verbose_name="是否启用", null=True)
    order_num = IntegerField(verbose_name="优先级", null=True)
    create_user_id = IntegerField(verbose_name="创建人id")
    create_user = CharField(verbose_name="创建人")
