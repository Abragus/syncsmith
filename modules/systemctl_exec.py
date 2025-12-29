import os
from modules.__syncsmith_module import SyncsmithModule
from globals import COMPILED_FILES_DIR

metadata = {
    "name": "systemctl_exec",
    "description": "Execute systemctl commands",
    "single_instance": False,
}

class SystemctlExec(SyncsmithModule):
    def __init__(self, modulename=None):
        super().__init__(modulename)

    def apply(self, config, dry_run=False):
        super().apply(config, dry_run=dry_run)

        command = "systemctl " + config.get("command", "")
        if dry_run:
            print(f"[DRY RUN] Would run {command}")
            return

        print(f"Executing: {command}")
        os.system(command)
    