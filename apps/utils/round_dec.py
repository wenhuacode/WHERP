from decimal import *


def round_dec(n, d):
    s = '0.' + '0' * d
    return Decimal(str(n)).quantize(Decimal(s), ROUND_HALF_UP)