# -*- coding: utf-8 -*-
import os
import uuid
import time
import logging
import oss2


# Uploader
class Uploader(object):
    def __init__(self, oss_access_key, oss_access_secret, oss_bucket=None, oss_endpoint=None, oss_prefix=None, logger=None):
        super().__init__()
        if logger is None:
            self.logger = logging.getLogger(__name__ + ".Uploader")
        else:
            self.logger = logger

        auth = oss2.Auth(oss_access_key, oss_access_secret)
        if oss_bucket is None:
            oss_bucket = os.environ.get('OSS_BUCKET')
        if oss_endpoint is None:
            oss_endpoint = os.environ.get('OSS_ENDPOINT')
        if oss_prefix is None:
            oss_prefix = os.environ.get('OSS_PREFIX')
        self.bucket = oss2.Bucket(auth, oss_endpoint, oss_bucket)
        self.oss_bucket = oss_bucket
        self.oss_endpoint = oss_endpoint
        self.oss_prefix = oss_prefix

    def uploadData(self, data, filename=None):
        try:
            data_str = time.strftime("%Y-%m-%d", time.localtime())
            uniq_id = str(uuid.uuid4())[0:6]

            oss_path = self.oss_prefix + "/" + data_str + "/"
            if filename != None:
                oss_path = oss_path + filename
            else:
                oss_path = oss_path + uniq_id

            self.bucket.put_object(oss_path, data)
            return "oss://" + self.oss_bucket + "/" + oss_path
        except Exception as e:
            self.logger.error("upload data error: {}".format(e))
            return None

    def uploadFile(self, file_path, oss_path):
        try:
            # data_str = time.strftime("%Y-%m-%d", time.localtime())
            # filename = os.path.basename(file_path)
            # oss_path = self.oss_prefix + "/" + data_str + "/" + filename

            with open(file_path, 'rb') as file:
                self.bucket.put_object(oss_path, file.read())
                return "oss://" + self.oss_bucket + "/" + oss_path
        except Exception as e:
            self.logger.error("upload file error: {}".format(e))
            return None

    def sign(self, oss_url, timeout=3600):
        try:
            oss_path = oss_url[len("oss://" + self.oss_bucket + "/"):]
            return self.bucket.sign_url('GET', oss_path, timeout, slash_safe=True)
        except Exception as e:
            self.logger.error("upload file error: {}".format(e))
            return None
