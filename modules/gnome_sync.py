from modules.__syncsmith_module import SyncsmithModule
import os
from pathlib import Path
from globals import FILES_DIR, COMPILED_FILES_DIR
from colorama import Fore, Style

import configparser
import re

from io import StringIO


metadata = {
    "name": "gnome_sync",
    "description": "Sync Gnome configuration",
    "single_instance": True,
}

class GnomeSync(SyncsmithModule):
    def __init__(self):
        super().__init__(metadata["name"])
        global STORAGE_DIR
        global COMPILED_DIR
        STORAGE_DIR = Path(f"{FILES_DIR}/gnome_sync")
        COMPILED_DIR = Path(f"{COMPILED_FILES_DIR}/gnome_sync")

    def apply(self, config=None, dry_run=False):

        exceptions = config.get("shortcut_exceptions", [])

        conf_files = [
            "settings-daemon/plugins/media-keys",
            "desktop/wm/keybindings",
            "shell/keybindings",
            "mutter/keybindings",
            "mutter/wayland/keybindings",
        ]

        for conf_file in conf_files:
            global_path = STORAGE_DIR / conf_file.replace("/", "-")
            local_path = COMPILED_DIR / conf_file.replace("/", "-")

            if (os.path.exists(str(local_path) + '-local')):
                os.system(f"mv {str(local_path) + '-local'} {str(local_path) + '-local-previous'}")
                
            os.system(f"dconf dump /org/gnome/{conf_file}/ > {str(local_path) + '-local'}")

            local_keybindings = self._parse_gnome_keybindings(str(local_path) + '-local')
            local_keybindings_previous = self._parse_gnome_keybindings(str(local_path) + '-local-previous')
            global_keybindings = self._parse_gnome_keybindings(str(global_path))

            self._generate_gnome_keybindings(conf_file, local_keybindings, local_keybindings_previous, global_keybindings, exceptions)

            # Apply the compiled local config
            if not dry_run:
                os.system(f"dconf load /org/gnome/{conf_file}/ < {str(local_path) + '-local'}")
            
            # If first run (local_previous doesn't exist), backup current local
            if (not os.path.exists(str(local_path) + '-local-previous') and not os.path.exists(str(local_path) + '-local-backup')):
                os.system(f"cp {str(local_path) + '-local'} {str(local_path) + '-local-backup'}")

            if os.path.exists(str(local_path) + '-local-previous'):
                os.remove(str(local_path) + '-local-previous')

        print(f"Applied compiled Gnome keyboard shortcuts.")
        return super().apply(config, dry_run)
    
    def generate_config_stub(self, env):
        return {"shortcut_exceptions": []}

    def _parse_gnome_keybindings(self, path):
        config = configparser.ConfigParser()
        config.read(path)

        keybindings = {}

        for section in config.sections():
            if section == "/":
                # Root section: add all non-custom-keybindings entries
                for key, value in config[section].items():
                    if key != "custom-keybindings":
                        keybindings[key] = value
            else:
                # Custom keybinding section: add as dict
                entry = {
                    k: config[section][k]
                    for k in ("binding", "command", "name")
                    if k in config[section]
                }
                keybindings[section] = entry

        return keybindings

    def _generate_gnome_keybindings(self, conf_file, local_keybindings, local_keybindings_previous, global_keybindings, exceptions):
        config = configparser.ConfigParser()

        # Split root (normal) settings and custom sections for both local and global
        def split(kb_dict):
            normal = {}
            custom = {}
            for section, value in kb_dict.items():
                if section.startswith("custom-keybindings/"):
                    custom[section] = value
                else:
                    normal[section] = value
            return normal, custom

        local_normal, local_custom = split(local_keybindings)
        local_normal_previous, local_custom_previous = split(local_keybindings_previous)
        global_normal, global_custom = split(global_keybindings)

        # Build lookup dicts from the exceptions
        exceptions_by_binding = {ex["binding"]: ex for ex in exceptions if "binding" in ex}
        exceptions_by_name = {ex["name"]: ex for ex in exceptions if "name" in ex}

        # ---------------------------------------------------
        # Merge normal (root) settings with precedence:
        # 1) If name in exceptions -> use exceptions binding
        # 2) If binding (but not name) is in exceptions -> use local value
        # 3) Otherwise use global value
        # ---------------------------------------------------
        compiled_settings = {}
        new_global_normal = dict(global_normal)
        globals_changed = False

        for name in local_normal.keys():
            gbind = global_normal.get(name)
            lbind = local_normal.get(name)

            if name in exceptions_by_name.keys():
                # Use binding from exception (if present), otherwise fall back
                compiled_settings[name] = exceptions_by_name[name].get("binding", lbind or "@as []")
            elif (gbind in exceptions_by_binding.keys()) and (lbind is not None):
                # Binding (but not name) in exceptions -> prefer local
                compiled_settings[name] = lbind
            else:
                # If local and local_previous differ, prefer local, otherwise global
                lbind_prev = local_normal_previous.get(name)
                if lbind != lbind_prev and lbind is not None:
                    compiled_settings[name] = lbind
                    new_global_normal[name] = lbind
                    globals_changed = True
                else:
                    compiled_settings[name] = gbind if gbind is not None else (lbind or "")

            compiled_settings[name] = compiled_settings[name].strip("'[] ")
            if (compiled_settings[name] == "" or compiled_settings[name] == "@as"):
                compiled_settings[name] = "@as []"
            elif (not name == "volume-step"):
                compiled_settings[name] = f"['{compiled_settings[name]}']"
            
        # print("exceptions_by_name:", exceptions_by_name)
        # print("local_normal:", local_normal)
        # print("local_normal_previous:", local_normal_previous)
        # print("global_normal:", global_normal)
        # print("compiled_settings:", compiled_settings)

        # ---------------------------------------------------
        # Merge custom keybindings using the same precedence as normal bindings:
        # 1) If name in exceptions -> use exceptions binding
        # 2) If binding (but not name) is in exceptions -> use local value
        # 3) If local differs from previous -> prefer local and treat as change
        # 4) Otherwise use global value
        # ---------------------------------------------------
        # Map name -> entry (from global/local/previous).
        # IMPORTANT: use only the `name` field for identification; ignore any numeric indices
        # in the section names (custom<i>) — those will be rebuilt later.
        globs = {v.get("name"): v for v in global_custom.values() if v.get("name")}
        globs_new = dict(globs).copy()
        locs = {v.get("name"): v for v in local_custom.values() if v.get("name")}
        locals_prev = {v.get("name"): v for v in local_custom_previous.values() if v.get("name")}

        # Preserve input order by `name`: iterate local entries in their original order
        # (skipping entries that lack a name), then append any global-only names
        ordered_names = list(locs.keys()).copy()
        ordered_names.extend([name for name in globs.keys() if name not in ordered_names])
        ordered_names.extend([name for name in exceptions_by_name.keys() if name not in ordered_names and exceptions_by_name[name].get("command")])

        final_custom_entries = []
        for name in ordered_names:
            glob = globs.get(name, {})
            loc = locs.get(name, {})
            loc_prev = locals_prev.get(name, {})
                
            if name in locals_prev and name not in locs:
                # Was removed locally -> remove from global as well
                if name in exceptions_by_name:
                    print(Fore.YELLOW + f"[gnome_sync] Detected removal of custom keybinding '{name}' but it is in exceptions, preserving in global storage." + Style.RESET_ALL)
                else: 
                    print(Fore.YELLOW + f"[gnome_sync] Detected removal of custom keybinding '{name}', removing from global storage." + Style.RESET_ALL)
                    globs_new.pop(name, None)
                    globals_changed = True

            # exception (name or binding) -> use local
            elif name in exceptions_by_name or (loc.get("binding", "").replace("'", "") in exceptions_by_binding.keys()):
                final_custom_entries.append({
                    "name": name,
                    "binding": exceptions_by_name.get(name, {}).get("binding", loc.get("binding", "")),
                    "command": exceptions_by_name.get(name, {}).get("command", loc.get("command", "")),
                })

            # local changed -> use local and update global
            elif loc_prev != loc:
                print(Fore.YELLOW + f"[gnome_sync] Detected change in custom keybinding '{name}'; updating global storage file." + Style.RESET_ALL)
                final_custom_entries.append({
                    "name": name,
                    "binding": loc.get("binding", ""),
                    "command": loc.get("command", ""),
                })
                globs_new[name] = loc
                globals_changed = True

            # otherwise use global
            else:
                final_custom_entries.append({
                    "name": name,
                    "binding": glob.get("binding", ""),
                    "command": glob.get("command", ""),
                })

        # ---------------------------------------------------
        # Build config root + custom-keybindings index list for compiled output
        # ---------------------------------------------------
        root = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings"
        index_list = [f"{root}/custom{i}/" for i in range(len(final_custom_entries))]

        config["/"] = dict(compiled_settings)
        if len(index_list) > 0:
            config["/"]["custom-keybindings"] = str(index_list)

        # ---------------------------------------------------
        # Per-keybinding subsections for compiled output
        # ---------------------------------------------------
        for i, kb in enumerate(final_custom_entries):
            section = f"custom-keybindings/custom{i}"
            config[section] = {}
            for field in ("binding", "command", "name"):
                if kb.get(field, ""):
                    config[section][field] = kb[field]

        # ---------------------------------------------------
        # Persist global storage using `new_global_normal` and `globs_new`
        # - root values from `new_global_normal`
        # - custom sections rebuilt from `globs_new` (ignore compiled index_list)
        # ---------------------------------------------------
        try:
            # Build a fresh global config using only the merged in-memory data
            global_config = configparser.ConfigParser()

            # Assign root values directly from new_global_normal
            # Use a shallow copy to ensure we don't accidentally mutate the source
            global_config["/"] = dict(new_global_normal)

            # Build global index list from globs_new (names are keys)
            global_index_list = [f"{root}/custom{i}/" for i, name in enumerate(globs_new.keys())]
            if len(global_index_list) > 0:
                global_config["/"]["custom-keybindings"] = str(global_index_list)

            # Add per-keybinding sections from globs_new
            for i, name in enumerate(globs_new.keys()):
                entry = globs_new.get(name, {})
                section = f"custom-keybindings/custom{i}"
                # Assign only non-empty fields from the entry
                global_config[section] = {k: v for k, v in entry.items() if v}
            
            # Write updated global config (overwrite path)
            self._write_config(global_config, str(STORAGE_DIR / conf_file.replace("/", "-")))

            if globals_changed:
                print(Fore.YELLOW + f"[gnome_sync] Wrote updated global storage: {STORAGE_DIR / conf_file.replace('/', '-')}" + Style.RESET_ALL)
        
        except Exception as e:
            print(Fore.RED + f"[gnome_sync] Error writing updated global storage: {e}" + Style.RESET_ALL)

        return self._write_config(config, str(COMPILED_DIR / (conf_file.replace("/", "-") + "-local")))

    def _write_config(self, config, path):
        buffer = StringIO()
        config.write(buffer)
        content = buffer.getvalue()
        new_contents = [line.replace(" = ", "=", 1) for line in content.splitlines()]
        content = "\n".join(new_contents)
        self._write_file(content, path)
        return content