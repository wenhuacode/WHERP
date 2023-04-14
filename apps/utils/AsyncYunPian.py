import json
from urllib.parse import urlencode

from tornado import httpclient
from tornado.httpclient import HTTPRequest


class AsyncYunPian:
    def __init__(self, api_key):
        self.api_key = api_key

    async def send_single_sms(self, code, mobile):
        http_client = httpclient.AsyncHTTPClient()
        url = "https://sms.yunpian.com/v2/sms/single_send.json"
        text = "【WHERP】您的验证码是{}。如非本人操作，请忽略本短信".format(code)
        post_request = HTTPRequest(url=url, method="POST", body=urlencode({
            "apikey": self.api_key,
            "mobile": mobile,
            "text": text
        }))

        res =  await http_client.fetch(post_request)
        return json.loads(res.body.decode("utf8"))

