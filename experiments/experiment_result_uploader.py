import os

import easywebdav


class ExperimentResultUploader(object):
    def __init__(self) -> None:
        self.remote_base_path = 'output'
        self.webdav = easywebdav.connect('dennisschroer.stackstorage.com', protocol='https', path='remote.php/webdav',
                                         username='abe', password=None)

    def upload_directory(self, base_path: str, path: str = ''):
        for f in os.listdir(os.path.join(base_path, path)):
            if os.path.isfile(os.path.join(base_path, path, f)):
                self.upload_file(base_path, path, f)
            else:
                self.upload_directory(base_path, os.path.join(path, f))

    def upload_file(self, base_path: str, path: str, file_name: str) -> None:
        print("Uploading %s" % os.path.join(base_path, path, file_name))
        self.webdav.upload(os.path.join(base_path, path, file_name), os.path.join(self.remote_base_path, path))
