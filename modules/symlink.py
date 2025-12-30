import os
from modules.__syncsmith_module import SyncsmithModule
from modules.__filesync_backbone import build_entries, apply_entries, rollback_entries

metadata = {
    "name": "symlink",
    "description": "Sync any file using symbolic links",
    "single_instance": False,
}

class SymLink(SyncsmithModule):
    def __init__(self, modulename=None):
        super().__init__(modulename)

    def _apply_one(self, src, dst, dry_run=False):
        if dry_run:
            print(f"[DRY RUN] Would create symlink from {src} to {dst}")
        else:
            print(f"Creating symlink from {src} to {dst}")
            os.symlink(src, dst)

    def apply(self, config, dry_run=False):
        super().apply(config, dry_run=dry_run)
        raw_source = config.get("source", "")

        try:
            entries = build_entries(self, raw_source, config.get("target", ""))
        except FileNotFoundError as e:
            print(f"[ERROR] {e}")
            return

        changed = apply_entries(entries, self._apply_one, dry_run=dry_run)
        if not changed:
            print(f"Symlinks already exist from {raw_source} to {config.get('target', '')}")

    def rollback(self, config, dry_run=False):
        super().rollback(config, dry_run=dry_run)

        try:
            entries = build_entries(self, config.get("source", ""), config.get("target", ""))
        except FileNotFoundError:
            # nothing to rollback if source missing
            entries = []
            return

        rollback_entries(entries, remove_one=self._remove_one, dry_run=dry_run)