import os, shutil
from modules.__syncsmith_module import SyncsmithModule
from utils.paths import get_syncsmith_root
from globals import FILES_DIR

metadata = {
    "name": "copy",
    "description": "Sync any file by copying",
    "single_instance": False,
}

class Copy(SyncsmithModule):
    def __init__(self, modulename=None):
        super().__init__(modulename)

    def apply(self, config, dry_run=False):
        super().apply(config, dry_run=dry_run)

        source_file = os.path.join(FILES_DIR, config.get("source", ""))
        target_file = os.path.expanduser(config.get("target", ""))

        if target_file.endswith('/'):
            target_file = os.path.join(target_file, os.path.basename(source_file))

        if dry_run:
            print(f"[DRY RUN] Would copy {source_file} to {target_file}")
            return
        
        # If file exists, back it up
        if os.path.exists(target_file) and not os.path.exists(target_file + ".bak"):
            backup_path = target_file + ".bak"
            print(f"Backing up existing file {target_file} to {backup_path}")
            os.rename(target_file, backup_path)
        
        print(f"Copying from {source_file} to {target_file}")
        os.system(f"cp {source_file} {target_file}")

        if config.get("ownership"):
            print(f"Setting ownership of {target_file} to {config['ownership']}")
            os.system(f"chown {config['ownership']} '{target_file}'")

        if config.get("permissions"):
            print(f"Setting permissions of {target_file} to {config['permissions']}")
            os.system(f"chmod {config['permissions']} '{target_file}'")