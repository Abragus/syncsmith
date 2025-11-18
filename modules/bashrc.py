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


# from modules.__conf_file import ConfFile
# import os

# metadata = {
#     "name": "ssh_keys",
#     "description": "Sync SSH authorized_keys file"
# }

# class Ashkeys(ConfFile):
#     def __init__(self):
#         super().__init__(modulename="ssh_keys", sourcefile="files/ssh_keys", targetfile=os.path.expanduser("~/.ssh/authorized_keys"))