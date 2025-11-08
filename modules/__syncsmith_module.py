class SyncsmithModule:
    def __init__(self, name):
        self.name = name

    def apply(self, config=None, dry_run=False):
        if not config.get("enabled", False):
            return
        
        print(f"Applying module: {self.name} with config: {config} {("dry_run=true" if dry_run else "")}")

    def generate_config_stub(self):
        return {}