#!/usr/bin/env python3
import argparse, yaml, importlib, os, copy
import inspect
from modules.__syncsmith_module import SyncsmithModule
from pathlib import Path
from colorama import Fore, Style
from utils.system_info import get_os_release

CONFIG_DIR = Path(__file__).resolve().parent / "config"
LOCAL_CFG_DIR = Path(__file__).resolve().parent / "local_config"

def load_yaml(path):
    if not path.exists(): return {}
    with open(path) as f: return yaml.safe_load(f) or {}

def merge_configs(global_cfg, local_cfg):
    result = copy.deepcopy(global_cfg)

    for module, local_values in local_cfg.get("modules", {}).items():
        result.setdefault("modules", {})
        result["modules"].setdefault(module, {})

        # Handle add/remove for list values
        for action in ("add", "remove"):
            for key, values in local_values.get(action, {}):
                result["modules"][module].setdefault(key, [])
                if not isinstance(result["modules"][module][key], list):
                    raise ValueError(f"Expected list at modules[{module}][{key}]")
                
                for v in values:
                    if action == "add" and v not in result["modules"][module][key]:
                        result["modules"][module][key].append(v)
                    elif action == "remove" and v in result["modules"][module][key]:
                        result["modules"][module][key].remove(v)

        for key, value in local_values.items():
            if key not in ("add", "remove"):
                result["modules"][module][key] = value

    return result

def run_modules(config, dry_run=False):
    modules_cfg = config.get("modules", {})
    mod_path = Path(__file__).parent / "modules"
    env_data = config.get("env", {})

    for module_name in modules_cfg.keys():
        mod_file = mod_path / f"{module_name}.py"
        if not mod_file.exists():
            print(Fore.RED + f"[ERROR] Unknown module '{module_name}' — file not found." + Style.RESET_ALL)
            continue

        try:
            # Import the module dynamically
            module = importlib.import_module(f"modules.{module_name}")

            # Filter classes defined *in this file itself* (not imported ones)
            classes = [
                cls for _, cls in inspect.getmembers(module, inspect.isclass)
                if cls.__module__ == module.__name__
            ]
            if not classes:
                print(Fore.YELLOW + f"[WARN] No class found in {module_name}.py" + Style.RESET_ALL)
                continue

            # Prefer explicitly defined metadata name
            meta = getattr(module, "metadata", {"name": module_name})
            module_class = classes[0]
            instance = module_class()
            module_config = modules_cfg.get(module_name, {})

            if (module_config.get("enabled", True)):
                print(Fore.CYAN + f"==> Running module: {meta['name']}" + Style.RESET_ALL)
                instance.apply(modules_cfg.get(module_name, {}), dry_run=dry_run)
            else:
                print(Fore.YELLOW + f"==> Module '{meta['name']}' is disabled in config, skipping." + Style.RESET_ALL)

        except Exception as e:
            print(Fore.RED + f"[ERROR] Failed to run module '{module_name}': {e}" + Style.RESET_ALL)

def ensure_local_config(local_cfg_path, redo_auto_fill=False):
    LOCAL_CFG_DIR = Path(local_cfg_path).parent

    os_info = get_os_release()

    # Auto-filled envdata values
    auto_env = {
        "host": os.uname().nodename,
        "os": os_info.get("ID", "unknown"),
        "os_pretty": os_info.get("PRETTY_NAME", "Unknown"),
        "os_version": os_info.get("VERSION_ID", "unknown"),
        "desktop_environment": os.environ.get("DESKTOP_SESSION", "unknown").strip().lower(),
    }

    local_cfg = None
    if local_cfg_path.exists() and not redo_auto_fill:
        with open(local_cfg_path) as f:
            local_cfg = yaml.safe_load(f) or {}
    else:
        print(Fore.YELLOW + "[syncsmith] Creating or refreshing local config stub..." + Style.RESET_ALL)
        LOCAL_CFG_DIR.mkdir(parents=True, exist_ok=True)
        local_cfg = {"env": {}, "modules": {}}

    # --- Merge in auto-fill data (don’t overwrite user values) ---
    local_cfg.setdefault("env", {})
    for key, value in auto_env.items():
        if key not in local_cfg["env"]:
            local_cfg["env"][key] = value

    local_cfg.setdefault("modules", {})

    # --- Write back to disk ---
    with open(local_cfg_path, "w") as f:
        yaml.safe_dump(local_cfg, f, sort_keys=False)

    return local_cfg

def main():
    parser = argparse.ArgumentParser(description="Syncsmith — Keep your system configuration in sync")
    parser.add_argument("--dry-run", action="store_true", help="Show actions without applying")
    parser.add_argument("--apply", action="store_true", help="Apply changes")
    parser.add_argument("--yes", "-y", action="store_true", help="Use defaults noninteractively")
    parser.add_argument("--reset-local", action="store_true", help="Regenerate auto-filled local config values")
    args = parser.parse_args()

    global_cfg = load_yaml(CONFIG_DIR / "global.yaml")
    local_cfg_path = LOCAL_CFG_DIR / "local.yaml"
    local_cfg = load_yaml(local_cfg_path)
    merged = merge_configs(global_cfg, local_cfg)

    ensure_local_config(local_cfg_path, redo_auto_fill=args.reset_local)

    run_modules(merged, dry_run=args.dry_run)
    print(Fore.GREEN + "\n[syncsmith] Done." + Style.RESET_ALL)

if __name__ == "__main__":
    main()