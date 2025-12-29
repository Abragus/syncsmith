import os
from modules.__syncsmith_module import SyncsmithModule
from globals import COMPILED_FILES_DIR

metadata = {
    "name": "git_clone",
    "description": "Clone a git repository to a target location",
    "single_instance": False,
}

class GitClone(SyncsmithModule):
    def __init__(self, modulename=None):
        super().__init__(modulename)

    def apply(self, config, dry_run=False):
        super().apply(config, dry_run=dry_run)

        if dry_run:
            print(f"[DRY RUN] Would clone into {config['url']}")
            return
        
        clone_command = f"git clone {config['url']}"

        if "branch" in config:
            clone_command += f" -b {config['branch']}"

        if not config.get("absolute_path", False):
            clone_command += COMPILED_FILES_DIR
        
        if "path" in config:
            clone_command += f" {config['path']}"

        print(f"Executing: {clone_command}")
        os.system(clone_command)