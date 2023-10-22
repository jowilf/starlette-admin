# Toplu İşlemler

Normalde bir objeyi güncellemek için liste sayfasında seçip güncellemelisiniz. Bu çoğu durumda iyi çalışır.
Ancak, eğer aynı değişikliği birçok nesneye aynı anda yapmanız gerekiyorsa, bu iş akışı oldukça can sıkıcı olabilir.

Bu durumda birçok nesneyi aynı anda güncellemek için bir *özelleştirilmiş toplu işlem* yazabilirsiniz.

!!! note "Not"
    *starlette-admin* varsayılan olarak birçok nesneyi aynı anda silmek için bir toplu işlem ekler.

[ModelView][starlette_admin.views.BaseModelView]inize varsayılan silme işlemi dışında başka toplu işlemler eklemek için, istediğiniz mantığı uygulayan bir fonksiyon tanımlayabilir ve [@action][starlette_admin.actions.action] dekoratörü ile sarabilirsiniz (Flask-Admin'den esinlenilmiştir).

## Example

```python
from typing import List, Any

from starlette.datastructures import FormData
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from starlette_admin import action
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.exceptions import ActionFailed


class ArticleView(ModelView):
    actions = ["make_published", "redirect", "delete"] # `delete` fonksiyonu varsayılan olarak eklenir

    @action(
        name="make_published",
        text="Mark selected articles as published",
        confirmation="Are you sure you want to mark selected articles as published ?",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
        form="""
        <form>
            <div class="mt-3">
                <input type="text" class="form-control" name="example-text-input" placeholder="Enter value">
            </div>
        </form>
        """,
    )
    async def make_published_action(self, request: Request, pks: List[Any]) -> str:
        # Kendi işlemlerinizi buraya yazın

        data: FormData = await request.form()
        user_input = data.get("example-text-input")

        if ...:
            # Anlamlı bir hata mesajı döndürün
            raise ActionFailed("Sorry, We can't proceed this action now.")
        # Başarılı mesajı döndürün
        return "{} articles were successfully marked as published".format(len(pks))

    # Özelleştirilmiş cevap için
    @action(
        name="redirect",
        text="Redirect",
        custom_response=True,
        confirmation="Fill the form",
        form='''
        <form>
            <div class="mt-3">
                <input type="text" class="form-control" name="value" placeholder="Enter value">
            </div>
        </form>
        '''
     )
    async def redirect_action(self, request: Request, pks: List[Any]) -> Response:
        data = await request.form()
        return RedirectResponse(f"https://example.com/?value={data['value']}")
```
