#!/usr/bin/env python3
import os, sys
vendor = os.path.join(os.path.dirname(__file__), "vendor")
if os.path.isdir(vendor):
    sys.path.insert(0, vendor)

from colorama import Fore, Style
import argparse, yaml, importlib, inspect
from modules.__syncsmith_module import SyncsmithModule
from pathlib import Path
from utils.system_info import get_os_release
from utils.conditional_config import ConditionalConfig

ROOT_DIR = Path(__file__).parent
ENV_FILE = ROOT_DIR / "environment.yaml"
CONFIG_FILE = ROOT_DIR / "config.yaml"

def load_yaml(path):
    if not path.exists(): return {}
    with open(path) as f: return yaml.safe_load(f) or {}

def run_modules(config, env, dry_run=False):
    modules = config.get("modules", {})
    module_path = ROOT_DIR / "modules"
    initiated_modules = []

    for module_conf in modules:
        mod_file = module_path / f"{module_conf['name']}.py"
        if not mod_file.exists():
            print(Fore.RED + f"[ERROR] Unknown module '{module_conf['name']}' — file not found." + Style.RESET_ALL)
            continue
        
        if (not module_conf.get("enabled", True)):
            print(Fore.YELLOW + f"==> Module '{module_conf['name']}' is disabled in config, skipping." + Style.RESET_ALL)
            continue
            
        try:
            # Import the module dynamically
            module = importlib.import_module(f"modules.{module_conf['name']}")

            # Filter classes defined *in this file itself* (not imported ones)
            classes = [
                cls for _, cls in inspect.getmembers(module, inspect.isclass)
                if cls.__module__ == module.__name__
            ]
            if not classes:
                print(Fore.YELLOW + f"[WARN] No class found in {module_conf['name']}.py" + Style.RESET_ALL)
                continue

            meta = getattr(module, "metadata", {"name": module_conf["name"]})

            if (meta.get("single_instance", True) and module_conf['name'] in initiated_modules):
                print(Fore.YELLOW + f"[WARN] Module '{module_conf['name']}' is single-instance and has already been initiated, skipping." + Style.RESET_ALL)
                continue
            
            print(Fore.CYAN + f"==> Running module: {module_conf['name']}" + Style.RESET_ALL)
            module_class = classes[0]
            instance = module_class()
            instance.apply(module_conf, dry_run=dry_run)
            initiated_modules.append(module_conf['name'])

        except Exception as e:
            print(Fore.RED + f"[ERROR] Failed to run module '{module_conf['name']}': {e}" + Style.RESET_ALL)

def ensure_local_env(env_file, reset=False):
    os_info = get_os_release()

    # Auto-filled envdata values
    default_env = {
        "host": os.uname().nodename,
        "os": os_info.get("ID", "unknown"),
        "os_pretty": os_info.get("PRETTY_NAME", "Unknown"),
        "os_version": os_info.get("VERSION_ID", "unknown"),
        "desktop_environment": os.environ.get("DESKTOP_SESSION", "unknown").strip().lower(),
        "tags": [],
    }

    new_env = None
    if env_file.exists() and not reset:
        with open(env_file) as f:
            new_env = yaml.safe_load(f) or {}
    else:
        print(Fore.YELLOW + "[syncsmith] Creating or refreshing environment file..." + Style.RESET_ALL)
        new_env = {}

    # --- Merge in auto-fill data (don’t overwrite user values) ---
    for key, value in default_env.items():
        if key not in new_env:
            new_env[key] = value

    # --- Write back to disk ---
    with open(env_file, "w") as f:
        yaml.safe_dump(new_env, f, sort_keys=False)

    return new_env

def main():
    parser = argparse.ArgumentParser(description="Syncsmith — Keep your system configuration in sync")
    parser.add_argument("--dry-run", action="store_true", help="Show actions without applying")
    parser.add_argument("--apply", action="store_true", help="Apply changes")
    parser.add_argument("--yes", "-y", "--auto", action="store_true", help="Use defaults noninteractively")
    parser.add_argument("--reset-env", action="store_true", help="Reset the local environment configuration file")
    args = parser.parse_args()

    print(Fore.GREEN + "[syncsmith] Getting latest changes from repo..." + Style.RESET_ALL)
    os.system(f"cd {ROOT_DIR} && git pull")

    environment = ensure_local_env(ENV_FILE, reset=args.reset_env)
    raw_config = load_yaml(CONFIG_FILE)
    parsed_config = ConditionalConfig.parse(raw_config, environment)
    
    run_modules(parsed_config, environment, dry_run=args.dry_run)
    print(Fore.GREEN + "\n[syncsmith] Done." + Style.RESET_ALL)

if __name__ == "__main__":
    main()