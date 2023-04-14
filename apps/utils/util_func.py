import decimal
from datetime import datetime, date

from apps.users.models import PasswordHash


def json_serial(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    if isinstance(obj, PasswordHash):
        return str(obj)

    raise TypeError("TYPE {}s not serializable".format(type(obj)))