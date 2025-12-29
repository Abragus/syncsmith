from modules.symlink import SymLink
import os
from globals import FILES_DIR

metadata = {
    "name": "bashrc",
    "description": "Sync .bashrc file",
    "single_instance": True,
}

class BashRC(SymLink):
    def __init__(self):
        super().__init__(modulename="bashrc")
    
    def apply(self, config=None, dry_run=False):
        result = super().apply({"source": os.path.join(FILES_DIR, ".bashrc"), "target": os.path.expanduser("~/.bashrc")}, dry_run=dry_run)
        return result
    
    def rollback(self, config=None, dry_run=False):
        return super().rollback({"source": os.path.join(FILES_DIR, ".bashrc"), "target": os.path.expanduser("~/.bashrc")}, dry_run=dry_run)