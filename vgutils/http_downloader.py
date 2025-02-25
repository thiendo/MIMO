import logging
import requests

# disable warnings
requests.packages.urllib3.disable_warnings()


# HTTP 下载器
class HttpDownloader(object):
    def __init__(self, pool_connections=64, pool_maxsize=64, logger=None):
        super().__init__()
        if logger is None:
            self.logger = logging.getLogger(__name__ + ".HttpDownloader")
        else:
            self.logger = logger

        adapter = requests.adapters.HTTPAdapter(
            pool_connections=pool_connections, pool_maxsize=pool_maxsize)
        self.session = requests.Session()
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    def downloadData(self, url, timeout=60, verify=False, headers=None):
        try:
            if headers != None:
                rsp = self.session.get(url, timeout=timeout,
                                       verify=verify, headers=headers)
            else:
                rsp = self.session.get(url, timeout=timeout, verify=verify)
            if rsp.status_code == 200:
                data = rsp.content
                return data
            else:
                return None
        except Exception as e:
            self.logger.error("HttpDownloader download data error: ", e)
            return None

    def downloadFile(self, url, file_path, timeout=60, verify=False, headers=None):
        try:
            if headers != None:
                rsp = self.session.get(url, timeout=timeout,
                                       verify=verify, headers=headers)
            else:
                rsp = self.session.get(url, timeout=timeout, verify=verify)
            if rsp.status_code == 200:
                with open(file_path, "wb") as file:
                    file.write(rsp.content)
                return True
            else:
                return False
        except Exception as e:
            self.logger.error("HttpDownloader download file error: ", e)
            return False
