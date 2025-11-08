import os

def get_syncsmith_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def get_files_dir():
    return os.path.join(get_syncsmith_root(), "files")