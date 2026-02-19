import subprocess
import filecmp
import os
import shutil
from typing import Callable, Iterable, List, Tuple
from modules.__syncsmith_module import SyncsmithModule

def _is_synced_file(src: str, dst: str) -> bool:
    """Check if dst is a symlink to src or a file with same contents."""
    if not os.path.exists(dst):
        return False
    
    if os.path.islink(dst):
        return os.readlink(dst) == src
    elif os.path.isfile(dst):
        return filecmp.cmp(src, dst)
    return False

def build_entries(raw_source: str, target: str) -> List[Tuple[str, str]]:
    """Return list of (src, dst) pairs for either single or contents mode.
    In contents mode (source ends with /*), all entries in the source directory are synced to target directory.
    """
    target = os.path.expanduser(target)
    contents_mode = raw_source.endswith("/*")
    source = raw_source[:-2] if contents_mode else raw_source

    if contents_mode:
        source_dir = SyncsmithModule._find_file(source)
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
        source_file = SyncsmithModule._find_file(source)
        return [(source_file, target)]
    
def set_permissions(filepath, config, dry_run=False):
    expected_ownership = config.get("ownership", None)
    expected_permissions = config.get("permissions", None)
    
    changes_made = False
    stat_info = os.stat(filepath)

    # Check and set permissions
    if expected_permissions:
        current_perms = oct(stat_info.st_mode & 0o777)
        expected_perms = oct(int(expected_permissions, 8) & 0o777)
        
        if current_perms != expected_perms:
            if dry_run:
                print(f"[DRY RUN] Would set permissions of {filepath} to {expected_permissions}")
            else:
                print(f"Updating permissions of {filepath} to {expected_permissions}")
                os.chmod(filepath, int(expected_permissions, 8))
            changes_made = True
            stat_info = os.stat(filepath)
    
    # Check and set ownership
    if expected_ownership:
        uid, gid = expected_ownership.split(":")
        uid_int = int(uid) if uid.isdigit() else shutil._get_uid(uid)
        gid_int = int(gid) if gid.isdigit() else shutil._get_gid(gid)
        
        if stat_info.st_uid != uid_int or stat_info.st_gid != gid_int:
            if dry_run:
                print(f"[DRY RUN] Would set ownership of {filepath} to {uid_int}:{gid_int}")
            else:
                os.chown(filepath, uid_int, gid_int)
            changes_made = True
            stat_info = os.stat(filepath)
    
    # Check and restore SELinux context if restorecon is available and SELinux is enabled
    restorecon_bin = shutil.which("restorecon")
    if restorecon_bin:
        is_enabled = subprocess.run(["selinuxenabled"], capture_output=True).returncode == 0
        
        if is_enabled:
            check = subprocess.run(["matchpathcon", "-Vq", str(filepath)])
            if check.returncode != 0:
                print(f"Restoring SELinux context for {filepath} using {restorecon_bin}")
                if not dry_run:
                    subprocess.run(["sudo", restorecon_bin, "-F", str(filepath)], 
                                   capture_output=True)
                changes_made = True
    
    return changes_made

def apply_entries(config: dict, apply_one: Callable[[str, str], None], is_synced_file: Callable[[str, str], bool], dry_run: bool = False) -> bool:
    """Generic apply routine. `apply_one(src, dst)` performs the concrete action.

    Returns True if any changes were made.
    """

    try:
        entries = build_entries(config.get("source", ""), config.get("target", ""))
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        return
    
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

        if os.path.exists(dst_entry) and not is_synced_file(src_entry, dst_entry):
            backup_path = dst_entry + ".bak"
            if dry_run:
                print(f"[DRY RUN] Would back up existing {dst_entry} to {backup_path}")
            else:
                print(f"Backing up existing file {dst_entry} to {backup_path}")
                os.rename(dst_entry, backup_path)

        if not os.path.exists(dst_entry):
            apply_one(src_entry, dst_entry, dry_run=dry_run)
            changes_made = True

        if set_permissions(dst_entry, config, dry_run=dry_run):
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
