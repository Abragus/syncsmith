import filecmp
import os
from typing import Callable, Iterable, List, Tuple

def _is_synced_file(src: str, dst: str) -> bool:
    """Check if dst is a symlink to src or a file with same contents."""
    if not os.path.exists(dst):
        return False
    
    if os.path.islink(dst):
        return os.readlink(dst) == src
    elif os.path.isfile(dst):
        return filecmp.cmp(src, dst)
    return False

def build_entries(module, raw_source: str, target: str) -> List[Tuple[str, str]]:
    """Return list of (src, dst) pairs for either single or contents mode.

    `module` must implement `_find_file(self, spec)` which returns an absolute path.
    """
    target = os.path.expanduser(target)
    contents_mode = raw_source.endswith("/*")
    source_spec = raw_source[:-2] if contents_mode else raw_source

    if contents_mode:
        source_dir = module._find_file(source_spec)
        if not os.path.isdir(source_dir):
            raise FileNotFoundError(f"Source for contents mode is not a directory: {source_dir}")
        os.makedirs(target, exist_ok=True)
        entries: List[Tuple[str, str]] = []
        for entry in sorted(os.listdir(source_dir)):
            src_entry = os.path.join(source_dir, entry)
            dst_entry = os.path.join(target, entry)
            entries.append((src_entry, dst_entry))
        return entries
    else:
        source_file = module._find_file(source_spec)
        return [(source_file, target)]


def apply_entries(entries: Iterable[Tuple[str, str]], apply_one: Callable[[str, str], None], dry_run: bool = False) -> bool:
    """Generic apply routine. `apply_one(src, dst)` performs the concrete action.

    Returns True if any changes were made.
    """
    changes_made = False
    for src_entry, dst_entry in entries:
        parent = os.path.dirname(dst_entry)
        if parent and not os.path.exists(parent):
            if dry_run:
                print(f"[DRY RUN] Would create parent directory {parent}")
            else:
                os.makedirs(parent, exist_ok=True)
        
        if dst_entry.endswith("/"):
            dst_entry = str(os.path.join(dst_entry, os.path.basename(src_entry)))

        if os.path.exists(dst_entry):
            if _is_synced_file(src_entry, dst_entry):
                continue 
            
            backup_path = dst_entry + ".bak"
            if dry_run:
                print(f"[DRY RUN] Would back up existing {dst_entry} to {backup_path}")
            else:
                print(f"Backing up existing file {dst_entry} to {backup_path}")
                os.rename(dst_entry, backup_path)

        if not os.path.exists(dst_entry):
            apply_one(src_entry, dst_entry, dry_run=dry_run)
            changes_made = True

    return changes_made


def rollback_entries(entries: Iterable[Tuple[str, str]], remove_one: Callable[[str], None] = None, dry_run: bool = False) -> None:
    """Generic rollback: remove created targets and restore backups.

    `remove_one(dst)` should remove the created object (e.g. unlink symlink or remove file).
    If `remove_one` is None a sensible default will be used.
    """
    if remove_one is None:
        def _default_remove(src: str, dst: str) -> None:
            if not _is_synced_file(src, dst):
                return
            
            if os.path.islink(dst):
                os.unlink(dst)
            elif os.path.isfile(dst):
                os.remove(dst)
            # do not remove real directories by default
        remove_one = _default_remove

    for src_entry, dst_entry in entries:
        if dry_run:
            print(f"[DRY RUN] Would remove {dst_entry} and restore backup if present")
            continue

        if os.path.exists(dst_entry):
            remove_one(src_entry, dst_entry)

        backup_path = dst_entry + ".bak"
        if os.path.exists(backup_path):
            os.rename(backup_path, dst_entry)
