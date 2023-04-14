import requests
from datetime import datetime

import json
import jwt
from wherp.settings import settings


current_time = datetime.utcnow()

web_url = "http://127.0.0.1:8888"

data = jwt.encode({
    "name": "张文华",
    "id": 1,
    "exp": current_time
}, settings["secret_key"])

headers = {
    "Access_Token": data
}


def test_register():
    url = "{}/api/data_center/purchase/product_purchase_query/".format(web_url)
    data = {
        "test": 1
    }
    res = requests.post(url, json=data, headers=headers)
    print(json.loads(res.text))


def test_purchase_detail():
    url = "{}/api/data_center/purchase/product_purchase_query_detail/".format(web_url)
    data = {
        'params': {
            "startTime": '2023-03-01',
            "endTime": '2023-03-20',
        },
        "sort": {},
    }
    res = requests.post(url, json=data, headers=headers)
    print(json.loads(res.text))


if __name__ == "__main__":
    # test_register()
    test_purchase_detail()