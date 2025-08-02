from typing import Type, Any, Optional
from pathlib import Path
import importlib.util
import sys

class ClassRegistry:
    def __init__(self):
        self.registry: dict[str, Type] = {}
        self._loaded_modules: dict[str, Any] = {}

    def pascal_case(self, snake_name: str) -> str:
        parts = snake_name.split('_')
        return ''.join(word.capitalize() for word in parts)

    def load_from_path(self, path_to_modules: str, base_class: Optional[Type] = None, package_name: str = "dynamic_modules"):
        path = Path(path_to_modules)
        if not path.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")

        if not path.is_dir():
            raise ValueError(f"Path must be a directory: {path}")

        for py_file in path.rglob('*.py'):
            if py_file.name.startswith('__'): continue

            self.load_module_from_file(py_file, base_class, package_name)

    def load_module_from_file(self, path: Path, base_class: Optional[Type], package_name: str):
        module_name = f"{package_name}.{path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, path)

        module = importlib.util.module_from_spec(spec)
        module.__path__ = sys.path.copy()
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        self._loaded_modules[module_name] = module

        main_class_name = self.pascal_case(path.stem)
        cls = getattr(module, main_class_name)

        if isinstance(cls, type) and base_class is None or (base_class != cls and issubclass(cls, base_class)):
            self.registry[main_class_name] = cls
            # print(f"Registered class {main_class_name} from {path}")

