import os
from modules.__syncsmith_module import SyncsmithModule
from utils.paths import get_syncsmith_root
from globals import FILES_DIR

metadata = {
    "name": "symlink",
    "description": "Sync any file using symbolic links",
    "single_instance": False,
}

class SymLink(SyncsmithModule):
    def __init__(self, modulename=None):
        super().__init__(modulename)

    def apply(self, config, dry_run=False):
        super().apply(config, dry_run=dry_run)

        source_file = os.path.join(FILES_DIR, config.get("source", ""))
        target_file = os.path.expanduser(config.get("target", ""))
        
        if dry_run:
            print(f"[DRY RUN] Would link from {source_file} to {target_file}")
            return
        
        # If file exists, back it up
        if os.path.exists(target_file) and not os.path.islink(target_file):
            backup_path = target_file + ".bak"
            print(f"Backing up existing file {target_file} to {backup_path}")
            os.rename(target_file, backup_path)
        else:
            if os.path.islink(target_file):
                os.unlink(target_file)
        
        print(f"Linking from {source_file} to {target_file}")
        os.symlink(source_file, target_file)