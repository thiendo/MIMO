import os
import logging
import requests
import oss2

# disable warnings
requests.packages.urllib3.disable_warnings()


# OSS 下载器
class OssDownloader(object):
    def __init__(self, oss_access_key, oss_access_secret, oss_bucket=None, oss_endpoint=None, oss_prefix=None, logger=None
                 ):
        super().__init__()
        if logger is None:
            self.logger = logging.getLogger(__name__ + ".OssDownloader")
        else:
            self.logger = logger

        # init params
        if oss_bucket is None:
            oss_bucket = os.environ.get('OSS_BUCKET')
        if oss_endpoint is None:
            oss_endpoint = os.environ.get('OSS_ENDPOINT')
        if oss_prefix is None:
            oss_prefix = os.environ.get('OSS_PREFIX')

        auth = oss2.Auth(oss_access_key, oss_access_secret)
        self.oss_bucket = oss2.Bucket(auth, oss_endpoint, oss_bucket)
        self.oss_bucket_name = oss_bucket
        self.oss_endpoint = oss_endpoint
        self.oss_prefix = oss_prefix

    def downloadData(self, url, headers=None):
        try:
            # url needs remove prefix
            oss_prefix = "oss://" + self.oss_bucket_name + "/"
            if url.startswith(oss_prefix):
                url = url[len(oss_prefix):]
            # get data
            result = self.oss_bucket.get_object(url, headers=headers)
            return result.read()
        except Exception as e:
            self.logger.error("OssDownloader download data error: ", e)
            return None

    def downloadFile(self, url, file_path, headers=None):
        try:
            # url needs remove prefix
            oss_prefix = "oss://" + self.oss_bucket_name + "/"
            if url.startswith(oss_prefix):
                url = url[len(oss_prefix):]
            # get data
            self.oss_bucket.get_object_to_file(url, file_path, headers=headers)
            return True
        except Exception as e:
            self.logger.error("OssDownloader download file error: ", e)
            return False
