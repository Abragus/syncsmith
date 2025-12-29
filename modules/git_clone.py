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

        target_path = os.path.expanduser(config.get("path", ""))

        if os.path.exists(target_path) and os.path.isdir(os.path.join(target_path, ".git")):
            print(f"Repository already exists at {target_path}, pulling latest changes.")
            os.system(f"cd {target_path} && git pull")
            return

        clone_command = f"git clone {config['url']}"

        if "branch" in config:
            clone_command += f" -b {config['branch']}"

        if target_path:
            if not os.path.isabs(target_path):
                clone_command += str(COMPILED_FILES_DIR) + "/"

            clone_command += f" {target_path}"

        print(f"Executing: {clone_command}")
        os.system(clone_command)
    
    def rollback(self, config, dry_run=False):
        super().rollback(config, dry_run=dry_run)

        target_path = config.get("path", "")
        if not config.get("absolute_path", False):
            target_path = os.path.join(COMPILED_FILES_DIR, target_path)

        if dry_run:
            print(f"[DRY RUN] Would remove cloned repository at {target_path}")
            return
        
        if os.path.exists(target_path):
            os.system(f"rm -rf {target_path}")