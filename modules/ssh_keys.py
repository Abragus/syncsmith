from modules.__conf_file import ConfFile
import os

metadata = {
    "name": "ssh_keys",
    "description": "Sync SSH authorized_keys file",
    "single_instance": True,
}

class SSHKeys(ConfFile):
    def __init__(self):
        super().__init__(modulename="ssh_keys", sourcefile="files/ssh_keys", targetfile=os.path.expanduser("~/.ssh/authorized_keys"))