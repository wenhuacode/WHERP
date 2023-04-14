from apps.inventory_management.inventory_distribution_cost.models import *
from WHERP.settings import database
from WHERP.settings import settings

database.set_allow_sync(True)
database = MySQLDatabase(
    'wh-erp',
    host="127.0.0.1",
    port=3306,
    user="root",
    password="root"
)


def init():
    pass
    # # 员工
    # database.create_tables([Employee, Employeeclassify, EmployeeRoles])
    #
    # # 客户
    # database.create_tables([Customer, CustomerClassify, CustomerAccountCurrent])
    # database.create_tables([AddressClassify])
    #
    # # 角色权限
    # database.create_tables([Menu, Role, RoleMenus, PagePermissions, RolePagePermissions])
    #
    # # 产品
    # database.create_tables([Product, ProductClassify])
    #
    # # 最新成本表, 仓库
    # database.create_tables([IrProperty, StorehouseManagement])
    # # # 历史成本表
    # # database.create_tables([ProductPriceHistory])
    #
    # # 销售订单
    # database.create_tables([OrderIndex, OrderDetail, OrderRecordOperation])
    #
    # # 销售订单正式明细表
    # database.create_tables([OrderDetailAccount])
    #
    # # 供应商
    # database.create_tables([Supplier, SupplierAccountCurrent])
    #
    #
    # # 采购订单
    # database.create_tables([PurchaseOrderIndex, PurchaseOrderDetail, PurchaseOrderRecordOperation])
    #
    # # 采购退货
    # database.create_tables([PurchaseReturnIndex, PurchaseReturnDetail, PurchaseReturnRecordOperation])
    #
    # # 采购正式订单明细表
    # database.create_tables([PurchaseOrderDetailAccount])
    #
    # # 财务模块
    # # 科目模块 收款单 付款单 往来明细 一般费用单 应收调整 应付调整 资金调整
    # database.create_tables([AccountingSubject, Receipt, Payment, SubsidiaryLedger, GeneralCost,
    #                         ArAdjust, ApAdjust, CapitalAdjust])
    #
    # # 库存模块
    # # 报损单

    # 初始化表
    # database.create_tables([OrderType])


def insert():
    order_type = [
        {'name': '销售单', 'num_ber_head': settings['company']['init_name'] + 'XS'},
        {'name': '销售退货单', 'num_ber_head': settings['company']['init_name'] + 'XSTH'},
        {'name': '采购单', 'num_ber_head': settings['company']['init_name'] + 'CG'},
        {'name': '采购退货单', 'num_ber_head': settings['company']['init_name'] + 'CGTH'},

        {'name': '报损单', 'num_ber_head': settings['company']['init_name'] + 'BSD'},
        {'name': '报溢单', 'num_ber_head': settings['company']['init_name'] + 'BYD'},
        {'name': '其他出库单', 'num_ber_head': settings['company']['init_name'] + 'QTCKD'},
        {'name': '其他入库单', 'num_ber_head': settings['company']['init_name'] + 'QTRKD'},
        {'name': '调拨单', 'num_ber_head': settings['company']['init_name'] + 'DBD'},
        {'name': '成本调整单', 'num_ber_head': settings['company']['init_name'] + 'CBTJ'},

        {'name': '收款单', 'num_ber_head': settings['company']['init_name'] + 'SK'},
        {'name': '付款单', 'num_ber_head': settings['company']['init_name'] + 'FK'},
        {'name': '一般费用单', 'num_ber_head': settings['company']['init_name'] + 'YBFY'},
        {'name': '应收增加单', 'num_ber_head': settings['company']['init_name'] + 'YSZJ'},
        {'name': '应收减少单', 'num_ber_head': settings['company']['init_name'] + 'YSJS'},
        {'name': '应付增加单', 'num_ber_head': settings['company']['init_name'] + 'YFZJ'},
        {'name': '应付减少单', 'num_ber_head': settings['company']['init_name'] + 'YFJS'},
        {'name': '资金调整单', 'num_ber_head': settings['company']['init_name'] + 'ZJTZ'},
    ]

    # OrderType.insert_many(order_type).execute()


if __name__ == "__main__":
    init()
    insert()