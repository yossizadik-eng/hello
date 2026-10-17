import importlib
import pkgutil

__all__ = [name for _, name, is_pkg in pkgutil.iter_modules(__path__) if not is_pkg]
for module_name in __all__:
    importlib.import_module(f"{__name__}.{module_name}")
