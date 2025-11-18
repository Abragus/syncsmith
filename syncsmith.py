#!/usr/bin/env python3
import argparse, yaml, importlib, os
import inspect
from modules.__syncsmith_module import SyncsmithModule
from pathlib import Path
from colorama import Fore, Style
from utils.system_info import get_os_release
from utils.conditional_config import ConditionalConfig

ENV_FILE = Path("environment.yaml")
CONFIG_FILE = Path("config.yaml")

def load_yaml(path):
    if not path.exists(): return {}
    with open(path) as f: return yaml.safe_load(f) or {}

def run_modules(config, env, dry_run=False):
    modules = config.get("modules", {})
    module_path = Path(__file__).parent / "modules"
    initiated_modules = []

    for module_conf in modules:
        mod_file = module_path / f"{module_conf["name"]}.py"
        if not mod_file.exists():
            print(Fore.RED + f"[ERROR] Unknown module '{module_conf["name"]}' — file not found." + Style.RESET_ALL)
            continue

        try:
            # Import the module dynamically
            module = importlib.import_module(f"modules.{module_conf["name"]}")

            # Filter classes defined *in this file itself* (not imported ones)
            classes = [
                cls for _, cls in inspect.getmembers(module, inspect.isclass)
                if cls.__module__ == module.__name__
            ]
            if not classes:
                print(Fore.YELLOW + f"[WARN] No class found in {module_conf["name"]}.py" + Style.RESET_ALL)
                continue

            # Prefer explicitly defined metadata name
            meta = getattr(module, "metadata", {"name": module_conf["name"]})
            module_class = classes[0]
            instance = module_class()

            if (meta.get("single_instance", False) and meta['name'] in initiated_modules):
                print(Fore.YELLOW + f"[WARN] Module '{meta['name']}' is single-instance and has already been initiated, skipping." + Style.RESET_ALL)
                continue
            
            if (module_conf.get("enabled", True)):
                print(Fore.CYAN + f"==> Running module: {meta['name']}" + Style.RESET_ALL)
                instance.apply(module_conf, dry_run=dry_run)
                initiated_modules.append(meta['name'])
            else:
                print(Fore.YELLOW + f"==> Module '{meta['name']}' is disabled in config, skipping." + Style.RESET_ALL)

        except Exception as e:
            print(Fore.RED + f"[ERROR] Failed to run module '{module_conf["name"]}': {e}" + Style.RESET_ALL)

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
    parser.add_argument("--yes", "-y", action="store_true", help="Use defaults noninteractively")
    parser.add_argument("--reset-env", action="store_true", help="Reset the local environment configuration file")
    args = parser.parse_args()

    environment = ensure_local_env(ENV_FILE, reset=args.reset_env)
    raw_config = load_yaml(CONFIG_FILE)
    parsed_config = ConditionalConfig.parse(raw_config, environment)
    
    run_modules(parsed_config, environment, dry_run=args.dry_run)
    print(Fore.GREEN + "\n[syncsmith] Done." + Style.RESET_ALL)

if __name__ == "__main__":
    main()