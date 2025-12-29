from globals import FILES_DIR
from modules.symlink import SymLink
import os

metadata = {
    "name": "ssh_keys",
    "description": "Sync SSH authorized_keys file",
    "single_instance": True,
}

class SSHKeys(SymLink):
    def __init__(self):
        super().__init__(modulename="ssh_keys")

    def apply(self, config=None, dry_run=False):
        return super().apply({"source": os.path.join(FILES_DIR, "ssh_keys"), "target": os.path.expanduser("~/.ssh/authorized_keys")}, dry_run=dry_run)
    
    def rollback(self, config=None, dry_run=False):
        return super().rollback({"source": os.path.join(FILES_DIR, "ssh_keys"), "target": os.path.expanduser("~/.ssh/authorized_keys")}, dry_run=dry_run)