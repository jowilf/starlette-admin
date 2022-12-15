# Acciones por lotes

De forma predeterminada, para actualizar un objeto, debe seleccionarlo en la página de lista y actualizarlo. Esto funciona bien para la mayoría de casos de uso. Sin embargo, si necesita realizar el mismo cambio en muchos objetos a la vez, este flujo de trabajo puede resultar bastante tedioso.

En estos casos, puede escribir una *acción por lotes personalizada* para actualizar de forma masiva muchos objetos a la vez.

!!! nota
    *starlette-admin* agrega por defecto una acción para eliminar muchos objetos a la vez

Para agregar otras acciones por lotes a su [ModelView][starlette_admin.views.BaseModelView], además de la acción de eliminación predeterminada, puede definir una que implementa la lógica deseada y la envuelve con el decorador [@action][starlette_admin.actions.action] (muy inspirado en Flask-Admin).

## Ejemplo
```python
from typing import List, Any

from starlette.requests import Request

from starlette_admin import action
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.exceptions import ActionFailed


class ArticleView(ModelView):
    actions = ["make_published", "delete"] # `delete` function is added by default

    @action(
        name="make_published",
        text="Mark selected articles as published",
        confirmation="Are you sure you want to mark selected articles as published ?",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
    )
    async def make_published_action(self, request: Request, pks: List[Any]) -> str:
        # Write your logic here
        if ...:
            # Display meaningfully error
            raise ActionFailed("Sorry, We can't proceed this action now.")
        # Display successfully message
        return "{} articles were successfully marked as published".format(len(pks))
```
