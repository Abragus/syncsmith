#!/usr/bin/env python3
import os, argparse, yaml, importlib, inspect
from colorama import Fore, Style
from utils.system_info import get_os_release
from utils.conditional_config import ConditionalConfig
from globals import ROOT_DIR, ENV_FILE, CONFIG_FILE, COMPILED_FILES_DIR

def load_yaml(path):
    if not path.exists(): return {}
    with open(path) as f: return yaml.safe_load(f) or {}

def run_modules(config, env, dry_run=False):
    modules = config.get("modules", {})
    module_path = ROOT_DIR / "modules"
    initiated_modules = []

    if not COMPILED_FILES_DIR.exists():
        COMPILED_FILES_DIR.mkdir(parents=True, exist_ok=True)

    for module_conf in modules:
        mod_file = module_path / f"{module_conf['name']}.py"
        if not mod_file.exists():
            print(Fore.RED + f"[ERROR] Unknown module '{module_conf['name']}' — file not found." + Style.RESET_ALL)
            continue
        
        if (not module_conf.get("enabled", True)):
            print(Fore.YELLOW + f"==> Module '{module_conf['name']}' is disabled in config, skipping." + Style.RESET_ALL)
            continue
            
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
        
        if not (COMPILED_FILES_DIR / module_conf['name']).exists():
            os.mkdir(COMPILED_FILES_DIR / module_conf['name'])
        
        print(Fore.CYAN + f"==> Running module: {module_conf['name']}" + Style.RESET_ALL)
        module_class = classes[0]
        instance = module_class()
        instance.apply(module_conf, dry_run=dry_run)
        initiated_modules.append(module_conf['name'])

        # Delete module's compiled files if empty
        compiled_module_dir = COMPILED_FILES_DIR / module_conf['name']
        if compiled_module_dir.exists() and not any(compiled_module_dir.iterdir()):
            compiled_module_dir.rmdir()

def ensure_local_env(env_file, reset=False):
    os_info = get_os_release()

    # Auto-filled envdata values
    default_env = {
        "host": os.uname().nodename,
        "os": os_info.get("ID", "unknown"),
        "os_pretty": os_info.get("PRETTY_NAME", "Unknown"),
        "os_version": os_info.get("VERSION_ID", "unknown"),
        "desktop_environment": os.environ.get("DESKTOP_SESSION", "unknown").strip().lower(),
        "install_dir": str(ROOT_DIR),
        "tags": [],
    }

    # Check if on proxmox host using `os.path.isdir("/etc/pve")` and append 'proxmox' tag
    if os.path.isdir("/etc/pve"):
        default_env["tags"].append("proxmox")
    # Check if on a laptop using `os.path.exists("/sys/class/power_supply/BAT*")` and append 'laptop' tag
    # Check not only BAT0 but any BAT* to cover more hardware variations
    # Use a os.system command to do it more slimly
    if os.system("ls /sys/class/power_supply/BAT* >/dev/null 2>&1") == 0:
        default_env["tags"].append("laptop")

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

    # --- Merge tags ---
    new_env["tags"] = (new_env.get("tags") or [])
    new_env["tags"].extend(default_env["tags"])
    new_env["tags"] = list(dict.fromkeys(new_env["tags"]))

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

    environment = ensure_local_env(ENV_FILE, reset=args.reset_env)
    raw_config = load_yaml(CONFIG_FILE)
    parsed_config = ConditionalConfig.parse(raw_config, environment)
    
    run_modules(parsed_config, environment, dry_run=args.dry_run)
    print(Fore.GREEN + "\n[syncsmith] Done." + Style.RESET_ALL)

if __name__ == "__main__":
    main()