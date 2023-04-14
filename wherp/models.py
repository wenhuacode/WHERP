from datetime import datetime

from wherp.settings import database
from peewee import *

# DISABLE_STATUS = (
#     (False, "正常"),
#     (True, "停用")
# )

DELETE_STATUS = (
    (False, "未删除"),
    (True, "已删除")
)


class BaseModel(Model):
    add_time = DateTimeField(default=datetime.now, verbose_name="添加时间")
    is_delete = BooleanField(choices=DELETE_STATUS, default=False, verbose_name="是否删除")
    update_time = DateTimeField(default=datetime.now, verbose_name="修改时间")

    def save(self, *args, **kwargs):
        # 判断这是一个新添加的数据还是更新的数据
        if self._pk is not None:
            # 这是一个新数据
            self.update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return super().save(*args, **kwargs)

    @classmethod
    def update(cls, *args, **kwargs):
        kwargs['update_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return super().update(**kwargs)

    @classmethod
    def delete(cls, permanently=False):  # permanently表示是否永久删除
        if permanently:
            return super().delete()
        else:
            return super().update(is_delete=True)

    def delete_instance(self, permanently=False, recursive=False, delete_nullable=False):
        if permanently:
            return self.delete(permanently).where(self._pk_expr()).execute()
        else:
            self.is_delete = True
            self.save()

    @classmethod
    def select(cls, *fields):
        return super().select(*fields).where(cls.is_delete == False)

    class Meta:
        database = database
