import os
from modules.__syncsmith_module import SyncsmithModule
from globals import COMPILED_FILES_DIR

metadata = {
    "name": "curl",
    "description": "Clone a git repository to a target location",
    "single_instance": False,
}

class Curl(SyncsmithModule):
    def __init__(self, modulename=None):
        super().__init__(modulename)

    def apply(self, config, dry_run=False):
        super().apply(config, dry_run=dry_run)

        if dry_run:
            print(f"[DRY RUN] Would curl {config['url']} to {config.get('path', '')}")
            return
        outfile = os.path.expanduser(config.get('path', ''))
        curl_command = f"curl -o {COMPILED_FILES_DIR if not os.path.isabs(outfile) else ''}{outfile} {config['url']}"

        print(f"Executing: {curl_command}")
        os.system(curl_command)
    
    def rollback(self, config, dry_run=False):
        super().rollback(config, dry_run=dry_run)

        target_path = os.path.expanduser(config.get("path", ""))
        if not os.path.isabs(target_path):
            target_path = os.path.join(COMPILED_FILES_DIR, target_path)

        if dry_run:
            print(f"[DRY RUN] Would remove file at {target_path}")
            return
        
        if os.path.exists(target_path):
            os.remove(target_path)