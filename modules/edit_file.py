import os
from modules.__syncsmith_module import SyncsmithModule
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

        source_file = SyncsmithModule._find_file(self, "", config.get("file", ""))
        output_file = SyncsmithModule._find_file(
            self,
            config.get("output", ""),
            config.get("file", "")
        )

        with open(source_file, "r") as f:
            content = f.read()
            for modification in config.get("modifications", []):
                if "add" in modification:
                    text = modification.get("add", "")
                    if text in content:                        
                        print(f"Text already exists, skipping add: {text}")
                        continue
                    print(f"Adding line: {text}")
                    content += "\n" + text
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
        
        print(f"Finish editing file {source_file}")

    def rollback(self, config, dry_run=False):
        super().rollback(config, dry_run=dry_run)

        target_file = SyncsmithModule._find_file(
            self,
            config.get("file", ""),
            config.get("output", "")
        )
        
        if dry_run:
            print(f"[DRY RUN] Would remove edited file at {target_file}")
            return
        
        if os.path.exists(target_file):
            os.remove(target_file)