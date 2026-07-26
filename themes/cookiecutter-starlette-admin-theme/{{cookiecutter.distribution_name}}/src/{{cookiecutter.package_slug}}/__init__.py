__version__ = "{{ cookiecutter.version }}"

from .classes import {{ cookiecutter.class_prefix }}Classes as {{ cookiecutter.class_prefix }}Classes
from .icons import {{ cookiecutter.class_prefix }}Icons as {{ cookiecutter.class_prefix }}Icons
from .theme import {{ cookiecutter.class_prefix }}Config as {{ cookiecutter.class_prefix }}Config
from .theme import {{ cookiecutter.class_prefix }}Theme as {{ cookiecutter.class_prefix }}Theme
