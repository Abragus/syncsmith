import filecmp
import os
import shutil
from modules.__syncsmith_module import SyncsmithModule
from modules.__filesync_backbone import build_entries, apply_entries, rollback_entries

metadata = {
    "name": "copy",
    "description": "Sync any file by copying",
    "single_instance": False,
}

class Copy(SyncsmithModule):
    def __init__(self, modulename=None):
        super().__init__(modulename)

    def _apply_one(self, src, dst, dry_run=False):
        if dry_run:
            print(f"[DRY RUN] Would copy {src} to {dst}")
        else:
            print(f"Copying from {src} to {dst}")
            shutil.copy2(src, dst)
    
    def is_synced_file(self, src, dst):
        if os.path.isfile(dst):
            return filecmp.cmp(src, dst)
        return False

    def apply(self, config, dry_run=False):
        super().apply(config, dry_run=dry_run)

        changed = apply_entries(config, self._apply_one, self.is_synced_file, dry_run=dry_run)
        if not changed:
            print(f"Files already copied from {config.get('source', '')} to {config.get('target', '')}")

    def rollback(self, config, dry_run=False):
        super().rollback(config, dry_run=dry_run)

        try:
            entries = build_entries(config.get("source", ""), config.get("target", ""))
        except FileNotFoundError:
            # nothing to rollback if source missing
            entries = []
            return

        rollback_entries(entries, remove_one=self._remove_one, dry_run=dry_run)