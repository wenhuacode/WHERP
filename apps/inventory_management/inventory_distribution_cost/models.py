from peewee import *
from WHERP.models import BaseModel

DISABLE_STATUS = (
    ("0", "正常"),
    ("1", "停用")
)


# 最新库存成本表
class IrProperty(BaseModel):
    product_id = IntegerField(verbose_name="产品id", null=True)
    barcode = CharField(max_length=255, verbose_name="产品条码", index=True)
    storehouse_id = IntegerField(verbose_name="仓库id")
    qty = IntegerField(verbose_name="库存数量")
    cost_price = DecimalField(default=0, max_digits=14, decimal_places=4, verbose_name="成本单价")
    total = DecimalField(default=0, max_digits=14, decimal_places=2, verbose_name="库存金额")


# # 历史成本表
# class ProductPriceHistory(BaseModel):
#     barcode = CharField(max_length=255, verbose_name="产品条码", index=True, unique=True)
#     storehouse_id = IntegerField(verbose_name="仓库id")
#     cost_price = DecimalField(default=0, max_digits=14, decimal_places=2, verbose_name="成本单价")
#     create_user_id = IntegerField(verbose_name="创建人id")
#     create_user = CharField(verbose_name="创建人")


# 仓库表
class StorehouseManagement(BaseModel):
    storehouse_no = CharField(max_length=24, verbose_name="仓库编号", index=True, unique=True)
    storehouse_name = CharField(max_length=24, verbose_name="仓库名称", index=True)
    employee_id = IntegerField(verbose_name="负责人id", null=True)
    employee = CharField(verbose_name="负责人", null=True)
    is_stop = CharField(choices=DISABLE_STATUS, default="0", null=True, verbose_name="是否停用")
    note = TextField(verbose_name="备注", null=True)
    jst_storehouse_no = CharField(max_length=24, verbose_name="聚水潭仓库编号", null=True)
    create_user_id = IntegerField(verbose_name="创建人id")
    create_user = CharField(verbose_name="创建人")
    modified_id = IntegerField(verbose_name="修改人id", null=True)
    modified_name = CharField(verbose_name="修改人姓名", null=True)
