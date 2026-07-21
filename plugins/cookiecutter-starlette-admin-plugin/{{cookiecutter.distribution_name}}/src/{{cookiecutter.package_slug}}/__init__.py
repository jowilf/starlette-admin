__version__ = "{{ cookiecutter.version }}"

{% if cookiecutter.include_example_field == "yes" %}
from .fields import {{ cookiecutter.class_prefix }}RatingField as {{ cookiecutter.class_prefix }}RatingField
{% endif %}
from .plugin import {{ cookiecutter.class_prefix }}Config as {{ cookiecutter.class_prefix }}Config
from .plugin import {{ cookiecutter.class_prefix }}Plugin as {{ cookiecutter.class_prefix }}Plugin
