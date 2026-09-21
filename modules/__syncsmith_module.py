import os
import json
import shutil

from jinja2 import DebugUndefined, Environment, TemplateSyntaxError

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

    @staticmethod
    def _find_file(filename):
        if os.path.isabs(filename):
            file_location = os.path.expanduser(filename)
        else:
            file_location = os.path.join(COMPILED_FILES_DIR, filename)
        if not os.path.exists(file_location):
            file_location = os.path.join(FILES_DIR, filename)
        
        return file_location
    
    @staticmethod
    def _get_environment(environment=None):
        if environment is not None:
            return environment

        serialized_environment = os.environ.get("SYNCSMITH_ENV", "{}")
        return json.loads(serialized_environment)

    @staticmethod
    def _is_managed_source(path):
        try:
            return os.path.commonpath((os.path.abspath(path), os.path.abspath(FILES_DIR))) == os.path.abspath(FILES_DIR)
        except ValueError:
            return False

    @staticmethod
    def _render_content(content, environment=None):
        if not any(marker in content for marker in ("{{", "{%", "{#")):
            return content

        template_environment = Environment(undefined=DebugUndefined)
        try:
            template = template_environment.from_string(content)
        except TemplateSyntaxError:
            return content

        return template.render(**SyncsmithModule._get_environment(environment))

    @staticmethod
    def _read_file(path, environment=None):
        file_location = SyncsmithModule._find_file(path)
        if not os.path.exists(file_location):
            raise FileNotFoundError(f"File not found: {path}")
        
        with open(file_location, "r") as f:
            content = f.read()

        if SyncsmithModule._is_managed_source(file_location):
            return SyncsmithModule._render_content(content, environment)
        return content

    @staticmethod
    def _render_file(path, environment=None):
        file_location = SyncsmithModule._find_file(path)
        if os.path.isdir(file_location):
            if not SyncsmithModule._is_managed_source(file_location):
                return file_location

            relative_path = os.path.relpath(file_location, FILES_DIR)
            rendered_location = os.path.join(COMPILED_FILES_DIR, relative_path)
            shutil.copytree(file_location, rendered_location, dirs_exist_ok=True)

            for root, _, filenames in os.walk(file_location):
                for filename in filenames:
                    source_file = os.path.join(root, filename)
                    relative_file = os.path.relpath(source_file, file_location)
                    rendered_file = os.path.join(rendered_location, relative_file)
                    try:
                        with open(source_file, "r", encoding="utf-8") as source:
                            content = source.read()
                    except (UnicodeDecodeError, OSError):
                        continue

                    rendered_content = SyncsmithModule._render_content(content, environment)
                    if rendered_content != content:
                        with open(rendered_file, "w", encoding="utf-8") as output:
                            output.write(rendered_content)

            return rendered_location

        if not os.path.isfile(file_location):
            return file_location

        if not SyncsmithModule._is_managed_source(file_location):
            return file_location

        with open(file_location, "r") as f:
            content = f.read()

        rendered_content = SyncsmithModule._render_content(content, environment)
        if rendered_content == content:
            return file_location

        relative_path = os.path.relpath(file_location, FILES_DIR)
        rendered_location = os.path.join(COMPILED_FILES_DIR, relative_path)
        os.makedirs(os.path.dirname(rendered_location), exist_ok=True)
        with open(rendered_location, "w") as f:
            f.write(rendered_content)
        return rendered_location
    
    @staticmethod
    def _write_file(content, output_path):
        if os.path.isabs(output_path):
            output_location = os.path.expanduser(output_path)
        else:
            output_location = os.path.join(COMPILED_FILES_DIR, output_path)

        os.makedirs(os.path.dirname(output_location), exist_ok=True)
        with open(output_location, "w") as f:
            f.write(content)
        return output_location