import os
from modules.__syncsmith_module import SyncsmithModule
from utils.paths import get_syncsmith_root
from globals import COMPILED_FILES_DIR, FILES_DIR

metadata = {
    "name": "edit_file",
    "description": "Edit files using custom rules",
    "single_instance": False,
}

class EditFile(SyncsmithModule):
    def __init__(self, modulename=None):
        super().__init__(modulename)

    def apply(self, config, dry_run=False):
        super().apply(config, dry_run=dry_run)

        source_file = os.path.join(FILES_DIR, config.get("file", ""))
        if "output" in config:
            if os.path.isabs(output_file):
                output_file = os.path.expanduser(output_file)
            else:
                output_file = os.path.join(COMPILED_FILES_DIR, config.get("output", ""))
        else:
            output_file = os.path.join(COMPILED_FILES_DIR, config.get("file", ""))
        
        with open(source_file, "r") as f:
            content = f.read()
            for modification in config.get("modifications", []):
                if "add" in modification:
                    print(f"Adding line: {modification.get('add', '')}")
                    content += "\n" + modification.get("add", "")
                elif "delete" in modification:
                    print(f"Deleting line: {modification.get('delete', '')}")
                    lines = content.splitlines()
                    lines = [line for line in lines if line.strip() != modification.get("delete", "").strip()]
                    content = "\n".join(lines)
                elif "replace" in modification:
                    print(f"Replacing '{modification.get('replace', '')}' with '{modification.get('with', '')}'")
                    content = content.replace(
                        modification.get("replace", ""),
                        modification.get("with", "")
                    )

        if not dry_run:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, "w") as f:
                f.write(content)
        
        print(f"Edited file {source_file}")