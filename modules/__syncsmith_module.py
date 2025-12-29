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

    def _find_file(self, filename, output_path=None):
        if output_path and os.path.isabs(output_path):
            file_location = os.path.expanduser(output_path)
        else:
            file_location = os.path.join(COMPILED_FILES_DIR, output_path or filename)
        if not os.path.exists(file_location):
            file_location = os.path.join(FILES_DIR, output_path or filename)
        
        return file_location