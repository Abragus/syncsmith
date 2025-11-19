class SyncsmithModule:
    def __init__(self, name):
        self.name = name

    def apply(self, config=None, dry_run=False):        
        print(f"Applying module: {self.name} {('dry_run=true' if dry_run else '')}")

    def generate_config_stub(self, env):
        return {}