from peewee import *

from WHERP.models import BaseModel

ADJUST_TYPE = (
    (1, "增加"),
    (2, "减少"),
    (3, "增加或减少")
)


class OrderType(BaseModel):
    name = CharField(max_length=24, verbose_name="单据名称")
    num_ber_head = CharField(max_length=24, verbose_name="单据头")

