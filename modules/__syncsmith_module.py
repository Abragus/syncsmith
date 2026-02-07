import os

from globals import FILES_DIR, COMPILED_FILES_DIR


class SyncsmithModule:
    def __init__(self, name):
        self.name = name

    def apply(self, config=None, dry_run=False):        
        return

    def rollback(self, config=None, dry_run=False):
        return
    
    def generate_config_stub(self, env):
        return {}

    def _find_file(self, filename):
        if os.path.isabs(filename):
            file_location = os.path.expanduser(filename)
        else:
            file_location = os.path.join(COMPILED_FILES_DIR, filename)
        if not os.path.exists(file_location):
            file_location = os.path.join(FILES_DIR, filename)
        
        return file_location
    
    def _read_file(self, path):
        if os.path.isabs(path):
            file_location = os.path.expanduser(path)
        else:
            file_location = os.path.join(COMPILED_FILES_DIR, path)
            if not os.path.exists(file_location):
                file_location = os.path.join(FILES_DIR, path)
        
        if not os.path.exists(file_location):
            raise FileNotFoundError(f"File not found: {path}")
        
        with open(file_location, "r") as f:
            return f.read()
        
    def _write_file(self, content, output_path):
        if os.path.isabs(output_path):
            output_location = os.path.expanduser(output_path)
        else:
            output_location = os.path.join(COMPILED_FILES_DIR, output_path)

        os.makedirs(os.path.dirname(output_location), exist_ok=True)
        with open(output_location, "w") as f:
            f.write(content)
        return output_location