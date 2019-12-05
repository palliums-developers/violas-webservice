from SocketHandler import SocketHandler
import json
import struct

class PushServerHandler:
    seq = 0

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def GetSeq(self):
        if self.seq == 99999:
            self.seq = 0

        self.seq += 1
        return self.seq

    def Query(self, msg):
        sockh = SocketHandler()
        if not sockh.Connect(self.host, self.port):
            return False, ""

        if not sockh.Send(self.Serialize(msg)):
            return False, ""

        succ, res = sockh.Recv()
        if not succ:
            return False, ""

        sockh.Close()

        return True, self.Deserialize(res)

    def Serialize(self, msg):
        strMsg = json.JSONEncoder().encode(msg) + "\0"
        msgHead = struct.pack("<H", (len(strMsg) + 2))

        bMsg = msgHead + bytes(strMsg, "utf-8")

        return bMsg

    def Deserialize(self, msg):
        msgLen = struct.unpack_from("<H", msg, 0)
        fmt = "<" + str(msgLen[0] - 3) + "s"
        bMsg = struct.unpack_from(fmt, msg, 2)
        strMsg = str(bMsg[0], "utf-8")
        jMsg = json.JSONDecoder().decode(strMsg)

        return jMsg

    def PushPhoneSMSCode(self, code, addr, usefulness):
        msg = {}
        msg["command"] = "smsVer"
        msg["seq"] = self.GetSeq()
        paras = {}
        paras["code"] = code
        paras["addr"] = addr

        if usefulness == 1:
            paras["mode"] = "login"
        elif usefulness == 2:
            paras["mode"] = "exchange"
        elif usefulness == 3:
            paras["mode"] = "bind"
        elif usefulness == 4:
            paras["mode"] = "changePass"
        elif usefulness == 5:
            paras["mode"] = "violasBind"

        msg["paras"] = paras

        succ, res = self.Query(msg)

        if not succ:
            return False
        else:
            return True

    def PushEmailSMSCode(self, code, addr, usefulness):
        msg = {}
        msg["command"] = "emailVer"
        msg["seq"] = self.GetSeq()
        paras = {}
        paras["code"] = code
        paras["addr"] = addr

        if usefulness == 1:
            paras["mode"] = "login"
        elif usefulness == 2:
            paras["mode"] = "exchange"
        elif usefulness == 3:
            paras["mode"] = "bind"
        elif usefulness == 4:
            paras["mode"] = "changePass"
        elif usefulness == 5:
            paras["mode"] = "violasBind"

        msg["paras"] = paras

        succ, res = self.Query(msg)

        if not succ:
            return False
        else:
            return True
