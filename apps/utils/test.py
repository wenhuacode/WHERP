from apps.utils.value_dispatch import value_dispatch


@value_dispatch
def get_discount(level):
    return '等级错误'


@get_discount.register("1")
def parse_level_1(level):
    discount = 0.1
    return discount


@get_discount.register("2")
def parse_level_2(level):
    discount = 0.2
    return discount


@get_discount.register_for_all({"4", "3"})
def parse_level_3(level):
    discount = 0.3
    return discount


discount = get_discount(88)
print(f'等级3的用户，获得的折扣是：{discount}')