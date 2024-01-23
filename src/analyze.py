


from typing import List
from collections import Counter
import os
import boto3
import json


class LogSave():
    def __init__(self, tempFile:str, bucket:str="plattform-services/opserver"):
        if not os.path.isabs(tempFile):
            raise Exception
        self.__file = tempFile
        self.bucket = bucket
        self.s3 = boto3.client(
            "s3",
            endpoint_url=os.environ.get("S3_ENDPOINT_URL"),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"))

    def write(self, data:dict, file:str):
        with open(self.__file, "w") as f:
            json.dump(data, f)
        self.s3.upload_fileobj(self.__file, self.bucket, file)

class IstioDAnalyze():
    def __init__(self, logs:List[str]):
        self.__logs = logs

    def __mostFrequentWords(self, logs: List[str], nFrequent:int=5):
        trace = [log.split("\t")[-1] for log in logs]
        words = " ".join(trace).split()
        mostCommonNotUsed = ["for", "new", "PUSH", "request", "CDS", "RDS", "LDS"]
        words = [w for w in words if w not in mostCommonNotUsed]
        mfw = Counter(words)
        return dict(mfw.most_common(nFrequent))

    def analyze(self) -> List[dict]:
        logs = []
        for index, log in enumerate(self.__logs):
            splash = log.split("\t")
            if len(splash) <= 3:
                continue
            if splash[1].lower() in ["warn", "error"]:
                mfw = self.__mostFrequentWords(self.__logs[index-10:index])
                logs.append({
                    "trace": splash[-1], 
                    "mfw": mfw,
                    "time": splash[0],
                    "type": splash[1].lower()
                })
        return logs

        