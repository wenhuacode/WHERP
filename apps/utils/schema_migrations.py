from datetime import datetime

from playhouse.migrate import *
from wherp.settings import database

database.set_allow_sync(True)


class Migrator:
    def __init__(self):
        self.migrator = MySQLMigrator(database)
        self.tables = database.get_tables()


class SchemaMigrator(Migrator):
    def drop_column(self, table_name: str = None, column_name: str = None, cascade: bool = False) -> bool:
        """
        删除字段
        :param cascade:
        :param table_name:
        :param column_name:
        :return:
        """
        if table_name:
            migrate(self.migrator.drop_column(table_name, column_name, cascade))
            return True
        else:
            if self.tables:
                for item in self.tables:
                    cl = database.get_columns(item)
                    data = []
                    for c in cl:
                        data.append(c.name)
                    if column_name in data:
                        migrate(self.migrator.drop_column(item, column_name, cascade))
                        data.clear()

    def add_column(self, table_name: str = None, column_name: str = None, field: Field = None) -> bool:
        """
        添加字段
        :param table_name:
        :param column_name:
        :param field:
        :return:
        """
        if table_name:
            migrate(self.migrator.add_column(table_name, column_name, field))
        else:
            if self.tables:
                for item in self.tables:
                    cl = database.get_columns(item)
                    data = []
                    for c in cl:
                        data.append(c.name)
                    if column_name not in data:
                        migrate(self.migrator.add_column(item, column_name, field))
                        data.clear()
            else:
                return False

    def rename_table(self, old_name, new_name) -> bool:
        """
        修改表字段名称, 修改之后要及时修改模型
        """
        if self.tables:
            for item in self.tables:
                cl = database.get_columns(item)
                for c in cl:
                    if old_name == c.name:
                        migrate(self.migrator.rename_column(item, old_name, new_name))
        else:
            return False

    def add_not_null(self, column) -> bool:
        """
        设置字段不为空
        :param column:
        :return:
        """
        if self.tables:
            for item in self.tables:
                cl = database.get_columns(item)
                for c in cl:
                    if column == c.name:
                        migrate(self.migrator.add_not_null(item, column))
        else:
            return False

    def drop_not_null(self, column) -> bool:
        """
        设置字段为空
        :param column:
        :return:
        """
        if self.tables:
            for item in self.tables:
                cl = database.get_columns(item)
                for c in cl:
                    if column == c.name:
                        migrate(self.migrator.drop_not_null(item, column))
        else:
            return False


if __name__ == "__main__":
    con = SchemaMigrator()
    # con.rename_table('modified', 'update_time')
    # con.add_not_null('update_time')
    # con.add_not_null('is_delete')

    DELETE_STATUS = (
        (False, "未删除"),
        (True, "已删除")
    )
    is_delete = BooleanField(choices=DELETE_STATUS, default=False, verbose_name="是否删除")
    con.add_column(column_name='is_delete', field=is_delete)

    # con.add_not_null('is_stop')

    # DISABLE_STATUS = (
    #     (False, "正常"),
    #     (True, "停用")
    # )
    # is_stop = CharField(choices=DISABLE_STATUS, default=False, verbose_name="是否停用")
    # con.add_column('is_stop', is_stop)

    # product_id = IntegerField(verbose_name="产品id", null=True)
    # con.add_column("irProperty", "product_id", product_id)

    # con.drop_column(column_name="is_delete")
