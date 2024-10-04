from typing import Any, Dict, Optional

from imagination.decorator.service import Service
from jinja2 import Environment, PackageLoader, select_autoescape


@Service()
class TemplateRenderer:
    def __init__(self):
        self._env = Environment(
            loader=PackageLoader("midp"),
            autoescape=select_autoescape()
        )

    def render(self, template_path: str, context: Optional[Dict[str, Any]] = None):
        template = self._env.get_template(template_path)
        return template.render(**context) if context else template.render()
