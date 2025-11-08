import os
from modules.__syncsmith_module import SyncsmithModule
from utils.paths import get_syncsmith_root

class ConfFile(SyncsmithModule):
    def __init__(self, modulename=None, sourcefile=None, targetfile=None):
        super().__init__(modulename)
        self.sourcefile = os.path.join(get_syncsmith_root(), sourcefile)
        self.targetfile = targetfile

    def apply(self, config, dry_run=False):
        super().apply(config, dry_run=dry_run)
        
        if dry_run:
            print(f"[DRY RUN] Would link from {self.sourcefile} to {self.targetfile}")
            return
        
        # If file exists, back it up
        if os.path.exists(self.targetfile) and not os.path.islink(self.targetfile):
            backup_path = self.targetfile + ".bak"
            print(f"Backing up existing file {self.targetfile} to {backup_path}")
            os.rename(self.targetfile, backup_path)
        else:
            if os.path.islink(self.targetfile):
                os.unlink(self.targetfile)
        
        print(f"Linking from {self.sourcefile} to {self.targetfile}")
        os.symlink(self.sourcefile, self.targetfile)