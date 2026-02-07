import os
from modules.__syncsmith_module import SyncsmithModule
from globals import COMPILED_FILES_DIR, FILES_DIR

metadata = {
    "name": "edit_file",
    "description": "Edit files using custom rules",
    "single_instance": False,
}

"""
Example config:
- name: edit_file
  file: example.txt
  modifications:
    - add: "This line will be added to the end of the file if it doesn't already exist."
    - delete: "This line will be removed from the file if it exists."
    - replace: "old text"
      with: "new text"
Notes:
- The `file` field specifies the target file to edit, relative to the files directory.
- The `modifications` list can contain any combination of `add`, `delete`, and `replace` operations.
- `add` will append the specified text to the end of the file if it doesn't already exist.
- `delete` will remove any lines that match the specified text.
- `replace` will replace all occurrences of the specified text with the new text.
- If `output` is specified, the modified content will be written to that path instead of overwriting the original file.
"""

class EditFile(SyncsmithModule):
    def __init__(self, modulename=None):
        super().__init__(modulename)

    def apply(self, config, dry_run=False):
        super().apply(config, dry_run=dry_run)

        file_name = config.get("file", "")
        if os.path.isabs(file_name):
            print(f"Editing file not in files dir not allowed, skipping: {config.get('file', '')}")
            return
        
        content = SyncsmithModule._read_file(self, file_name)
    
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
            SyncsmithModule._write_file(self, content, config.get("output", file_name))
            print(f"Finish editing file {config.get('file', '')}")
        else:
            print(f"[DRY RUN] Would write modified content to {config.get('output', file_name)}")

    def rollback(self, config, dry_run=False):
        super().rollback(config, dry_run=dry_run)

        target_file = SyncsmithModule._find_file(self, config.get("file", ""))
        
        if dry_run:
            print(f"[DRY RUN] Would remove edited file at {target_file}")
            return
        
        if os.path.exists(target_file):
            os.remove(target_file)