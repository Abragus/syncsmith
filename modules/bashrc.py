from modules.__conf_file import ConfFile
import os

metadata = {
    "name": "bashrc",
    "description": "Sync .bashrc file",
    "single_instance": True,
}

class BashRC(ConfFile):
    def __init__(self):
        super().__init__(modulename="bashrc", sourcefile="files/.bashrc", targetfile=os.path.expanduser("~/.bashrc"))
    
    def apply(self, config=None, dry_run=False):
        result = super().apply(config, dry_run=dry_run)
        os.system(f"source {os.path.expanduser('~/.bashrc')}")
        return result