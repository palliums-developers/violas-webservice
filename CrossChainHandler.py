import requests
import logging
from enum import IntEnum
from util import get_show_name

class CrossChainState(IntEnum):
    SUCESSED = 4001
    PROCESSING = 4002
    STOPED = 4003
    CANCELED = 4004

class CrossChainHandler():
    def __init__(self, url):
        self.url = url

    def getCrosschainTransactions(self, address, offset, limit):
        payload = {
            "opt": "records",
            "senders": address,
            "opttype": "swap",
            "cursor": offset,
            "limit": limit
        }
        res = self.sendWithRetry(payload)
        if res is None:
            return False, None
        return True, self.transferResponse(res)

    def transferResponse(self, res):
        ret = list()
        for data in res.get("datas").get("datas"):
            tr = dict()
            tr["data"] = data.get("expiration_time")
            tr["input_amount"] = data.get("in_amount")
            tr["output_amount"] = data.get("out_amount")
            tr["input_name"] = data.get("in_token")
            tr["output_name"] = data.get("out_token")
            tr["version"] = data.get("version")
            tr["input_shown_name"] = get_show_name(tr["input_name"])
            tr["output_shown_name"] = get_show_name(tr["output_name"])
            tr["from_chain"] = data.get("from_chain")
            tr["to_chain"] = data.get("to_chain")

            state = data.get("state")
            if state == "end":
                tr["status"] = CrossChainState.SUCESSED
            elif state == "start":
                tr["status"] = CrossChainState.PROCESSING
            else:
                tr["status"] = CrossChainState.STOPED
            ret.append(tr)
        return ret

    def sendWithRetry(self, payload):
        try_time = 3
        while try_time > 0:
            r = self.send(payload)
            try_time -= 1
            if r is None or r.status_code != 200:
                import time
                time.sleep(1)
                continue
            break
        if r is None or r.status_code != 200:
            logging.error(f"ERROR: {self.url} params:{payload} request fail")
            return None
        return r.json()


    def send(self, payload):
        try:
            r = requests.get(url=self.url, params=payload, headers={'content-type': 'application/json'})
        except:
            return None
        finally:
            r.close()
        return r
