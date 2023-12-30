import json
import random
import grpc

from amaas.grpc.protos.scan_pb2_grpc import ScanServicer
from amaas.grpc.protos.scan_pb2 import STAGE_INIT, STAGE_FINI, STAGE_RUN
from amaas.grpc.protos.scan_pb2 import CMD_QUIT, CMD_RETR
from amaas.grpc.protos.scan_pb2 import S2C


SDK_SCHEMA_VERSION = "1.0.0"
MAX_RUN = 5
FINAL_MSG = S2C(stage=STAGE_FINI, cmd=CMD_QUIT)


class MockScanServicer(ScanServicer):
    IDENTIFIER_VIRUS = "virus"
    IDENTIFIER_UNKNOWN_CMD = "unknown_cmd"
    IDENTIFIER_MISMATCHED = "mismatched"
    IDENTIFIER_GRPC_ERROR = "grpc_error"
    IDENTIFIER_EXCEED_RATE = "exceed_rate"
    UNKNOWN_CMD = 999

    def __init__(self):
        self.fsize = 0
        self.identifier = ""

    def getS2CMsg(self):
        start = random.randint(0, self.fsize - 1)
        end = random.randint(start, self.fsize)
        s2cmsg = S2C(stage=STAGE_RUN, cmd=CMD_RETR, offset=start, length=end - start)
        return s2cmsg

    def getUnknwonCmd(self):
        start = random.randint(0, self.fsize - 1)
        end = random.randint(start, self.fsize)
        s2cmsg = S2C(
            stage=STAGE_RUN,
            cmd=MockScanServicer.UNKNOWN_CMD,
            offset=start,
            length=end - start,
        )
        return s2cmsg

    def getMismatchedCmdStage(self):
        start = random.randint(0, self.fsize - 1)
        end = random.randint(start, self.fsize)
        s2cmsg = S2C(stage=STAGE_RUN, cmd=CMD_QUIT, offset=start, length=end - start)
        return s2cmsg

    def Run(self, request_iterator, context):
        count = 0
        for req in request_iterator:
            if req.stage == STAGE_INIT:
                self.fsize = req.rs_size
                self.identifier = req.file_name
                msg = self.getS2CMsg()
            elif req.stage == STAGE_RUN:
                if self.identifier == MockScanServicer.IDENTIFIER_UNKNOWN_CMD:
                    msg = self.getUnknwonCmd()
                elif self.identifier == MockScanServicer.IDENTIFIER_MISMATCHED:
                    msg = self.getMismatchedCmdStage()
                elif self.identifier == MockScanServicer.IDENTIFIER_GRPC_ERROR:
                    context.set_details("Ouch!")
                    context.set_code(grpc.StatusCode.INTERNAL)
                    msg = ""
                elif self.identifier == MockScanServicer.IDENTIFIER_EXCEED_RATE:
                    context.set_details("Http Error Code: 429")
                    context.set_code(grpc.StatusCode.INTERNAL)
                    msg = ""
                elif count >= MAX_RUN:
                    msg = FINAL_MSG
                    result = {
                        "scannerVersion": "1.0.0-1",
                        "schemaVersion": SDK_SCHEMA_VERSION,
                        "scanResult": 0,
                        "foundMalwares": [],
                    }
                    if self.identifier == MockScanServicer.IDENTIFIER_VIRUS:
                        result["scanResult"] = 1
                        result["foundMalwares"] = ["virus1", "virus2"]
                    msg.result = json.dumps(result)
                else:
                    msg = self.getS2CMsg()
            count += 1
            yield msg
