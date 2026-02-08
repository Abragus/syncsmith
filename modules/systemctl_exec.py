import subprocess
import shlex
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

        raw_command = config.get("command", "").strip()
        parts = shlex.split(raw_command)
        
        if not parts:
            return

        allowed_actions = ["start", "stop", "restart", "reload", "enable", "disable", "daemon-reload"]
        action = parts[0]
        
        if action not in allowed_actions:
            print(f"[ERROR] Action '{action}' is not allowed.")
            return

        full_cmd = ["systemctl"] + parts

        if dry_run:
            print(f"[DRY RUN] Would run: {' '.join(full_cmd)}")
            return

        try:
            print(f"Executing: {' '.join(full_cmd)}")
            subprocess.run(full_cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] systemctl failed: {e}")