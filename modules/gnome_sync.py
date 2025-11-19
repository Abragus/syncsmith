from modules.__syncsmith_module import SyncsmithModule
import os
from pathlib import Path

metadata = {
    "name": "gnome_sync",
    "description": "Sync Gnome configuration",
    "single_instance": True,
}

class GnomeSync(SyncsmithModule):
    def __init__(self):
        super().__init__(metadata["name"])

    def apply(self, config=None, dry_run=False):
        STORAGE_DIR = Path("files/gnome_sync")
        os.system(f"dconf dump /org/gnome/settings-daemon/plugins/media-keys/ > {STORAGE_DIR}/settings-daemon-plugins-media-keys")
        os.system(f"dconf dump /org/gnome/desktop/wm/keybindings/ > {STORAGE_DIR}/desktop-wm-keybindings")
        os.system(f"dconf dump /org/gnome/shell/keybindings/ > {STORAGE_DIR}/shell-keybindings")
        os.system(f"dconf dump /org/gnome/mutter/keybindings/ > {STORAGE_DIR}/mutter-keybindings")
        os.system(f"dconf dump /org/gnome/mutter/wayland/keybindings/ > {STORAGE_DIR}/mutter-wayland-keybindings")
        return super().apply(config, dry_run)
    
    def generate_config_stub(self, env):
        return {"keyboard_shortcuts": {"add": "[]", "remove": "[]"}}