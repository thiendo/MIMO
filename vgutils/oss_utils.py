import os
import logging
import requests

from vgutils.http_downloader import HttpDownloader
from vgutils.oss_downloader import OssDownloader
from vgutils.uploader import Uploader

# disable warnings
requests.packages.urllib3.disable_warnings()

# logging system
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s|%(levelname)s|%(name)s|%(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')


# OSS 工具
class OssUtils(object):
    def __init__(
            self,
            # oss
            oss_prefix=None,
            oss_bucket=None,
            oss_endpoint=None,
            oss_access_key=None,
            oss_access_secret=None,
            logger=None
    ):
        super().__init__()
        if logger is None:
            self.logger = logging.getLogger(__name__ + ".OssUtils")
        else:
            self.logger = logger

        self.oss_access_key = oss_access_key
        self.oss_access_secret = oss_access_secret
        self.oss_bucket = oss_bucket
        self.oss_endpoint = oss_endpoint
        self.oss_prefix = oss_prefix
        # request pool
        self.pool_connections = 64
        self.pool_maxsize = 64

        # init uploader
        self.uploader = Uploader(
            oss_access_key=self.oss_access_key,
            oss_access_secret=self.oss_access_secret,
            oss_prefix=self.oss_prefix,
            oss_bucket=self.oss_bucket,
            oss_endpoint=self.oss_endpoint,
            logger=logger,
        )
        # init http_downloader
        self.http_downloader = HttpDownloader(
            pool_connections=self.pool_connections,
            pool_maxsize=self.pool_maxsize,
            logger=logger,
        )
        # init oss_downloader
        self.oss_downloader = OssDownloader(
            oss_access_key=self.oss_access_key,
            oss_access_secret=self.oss_access_secret,
            oss_prefix=self.oss_prefix,
            oss_bucket=self.oss_bucket,
            oss_endpoint=self.oss_endpoint,
            logger=logger,
        )

    def uploadData(self, data, filename):
        """ upload data and return oss url """
        self.logger.info("uploadData: %s " % ({data, filename}))
        return self.uploader.uploadData(data=data, filename=filename)

    def uploadFile(self, file_path, oss_path):
        """ upload file and return oss url """
        self.logger.info("uploadFile: %s " % ({file_path}))
        return self.uploader.uploadFile(file_path=file_path, oss_path=oss_path)

    def sign(self, oss_url, timeout=3600):
        """ sign oss url to http url """
        self.logger.info("sign: %s " % ({oss_url, timeout}))
        return self.uploader.sign(oss_url=oss_url, timeout=timeout)

    def downloadData(self, url="", headers=None, timeout=60, verify=False):
        """ download data """
        self.logger.info("sign: %s " % ({url, timeout, headers, verify}))

        # oss download
        if url.startswith("oss"):
            return self.oss_downloader.downloadData(url, headers=headers)

        # http download
        if url.startswith("http"):
            return self.http_downloader.downloadData(url=url, timeout=timeout, verify=verify, headers=headers)

    def downloadFile(self, url="", file_path="", timeout=60, verify=False, headers=None):
        """ download file """
        self.logger.info("sign: %s " % ({url, file_path, timeout, headers, verify}))

        # oss download
        if url.startswith("oss"):
            return self.oss_downloader.downloadFile(url, file_path=file_path, headers=headers)

        # http download
        if url.startswith("http"):
            return self.http_downloader.downloadFile(url=url, file_path=file_path, timeout=timeout, verify=verify,
                                                     headers=headers)