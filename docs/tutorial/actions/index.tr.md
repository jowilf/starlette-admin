# İşlemler

Starlette-admin'de işlemler, veritabanı kayıtlarınızla etkileşim kurmanın ve toplu silme, özel toplu güncelleme, e-posta gönderme vb. gibi çeşitli işlemleri gerçekleştirmenin kolay bir yolunu sağlar.

## Toplu İşlemler

Normalde bir nesneyi güncellemek için liste sayfasında seçip güncellemelisiniz. Bu çoğu durumda iyi çalışır.
Ancak, eğer aynı değişikliği birçok nesneye aynı anda yapmanız gerekiyorsa, bu iş akışı oldukça can sıkıcı olabilir.

Bu durumda birçok nesneyi aynı anda güncellemek için bir *özelleştirilmiş toplu işlem* yazabilirsiniz.

!!! note "Not"
    *starlette-admin* varsayılan olarak birçok nesneyi aynı anda silmek için bir toplu işlem sunar.

[ModelView][starlette_admin.views.BaseModelView]inize varsayılan silme işlemi dışında başka toplu işlemler eklemek için, istediğiniz mantığı uygulayan bir fonksiyon tanımlayabilir ve [@action][starlette_admin.actions.action] dekoratörü ile sarabilirsiniz (Flask-Admin'den esinlenilmiştir).

!!! warning "Uyarı"

    Toplu işlem adı, ModelView içinde benzersiz olmalıdır.

## Örnek

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

## Satır İşlemleri

Satır işlemleri, bir liste görünümü içindeki bireysel öğeler üzerinde işlem yapmanıza olanak tanır.

!!! note "Not"

    Starlette-admin, varsayılan olarak üç (03) satır işlemi içerir:

    - `view`: Öğenin ayrıntı sayfasına yönlendirir
    - `edit`: Öğenin düzenleme sayfasına yönlendirir
    - `delete`: Seçilen öğeyi siler

[ModelView][starlette_admin.views.BaseModelView]inize varsayılan satır işlemi dışında başka satır işlemleri eklemek için, istediğiniz mantığı uygulayan bir fonksiyon tanımlayabilir ve [@row_action][starlette_admin.actions.row_action] dekoratörü ile sarabilirsiniz.

Satır işlemlerinin bir sayfaya yönlendirme yapması gerektiği durumlarda, [@link_row_action][starlette_admin.actions.link_row_action] dekoratörünü kullanmak tercih edilir. Temel fark, `link_row_action`'ın işlem API'ını çağırmaya ihtiyaç duymamasıdır. Bunun yerine, bağlantı doğrudan oluşturulan html öğesinin href özniteliğine dahil edilir (ör. `<a href='https://example.com/?pk=4' ...>`).

!!! warning "Uyarı"

    Satır işlemlerinin (hem [@row_action][starlette_admin.actions.row_action] hem de [@link_row_action][starlette_admin.actions.link_row_action]) adı, bir ModelView içinde benzersiz olmalıdır.

### Örnek

```python
from typing import Any

from starlette.datastructures import FormData
from starlette.requests import Request

from starlette_admin._types import RowActionsDisplayType
from starlette_admin.actions import link_row_action, row_action
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.exceptions import ActionFailed


class ArticleView(ModelView):
    ...
    row_actions = ["view", "edit", "go_to_example", "make_published",
                   "delete"]  # edit, view and delete varsayılan olarak sağlanır
    row_actions_display_type = RowActionsDisplayType.ICON_LIST  # RowActionsDisplayType.DROPDOWN

    @row_action(
        name="make_published",
        text="Mark as published",
        confirmation="Are you sure you want to mark this article as published ?",
        icon_class="fas fa-check-circle",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
        action_btn_class="btn-info",
        form="""
        <form>
            <div class="mt-3">
                <input type="text" class="form-control" name="example-text-input" placeholder="Enter value">
            </div>
        </form>
        """,
    )
    async def make_published_row_action(self, request: Request, pk: Any) -> str:
        # Kendi işlemlerinizi buraya yazın

        data: FormData = await request.form()
        user_input = data.get("example-text-input")

        if ...:
            # Anlamlı bir hata mesajı döndürün
            raise ActionFailed("Sorry, We can't proceed this action now.")
        # Başarılı mesajı döndürün
        return "The article was successfully marked as published"

    @link_row_action(
        name="go_to_example",
        text="Go to example.com",
        icon_class="fas fa-arrow-up-right-from-square",
    )
    def go_to_example_row_action(self, request: Request, pk: Any) -> str:
        return f"https://example.com/?pk={pk}"

```

### Liste Derleme

`RowActionsDisplayType`, satır işlemlerinin list görünümünde nasıl görüntüleneceğini belirlemek için için seçenekler sağlar.

#### RowActionsDisplayType.ICON_LIST

```python hl_lines="5"
from starlette_admin._types import RowActionsDisplayType


class ArticleView(ModelView):
    row_actions_display_type = RowActionsDisplayType.ICON_LIST
```

<img width="1262" alt="Screenshot 2023-10-21 at 4 39 58 PM" src="https://github.com/jowilf/starlette-admin/assets/31705179/670371b1-7c28-4106-964f-b7136e7268ea">

#### RowActionsDisplayType.DROPDOWN

```python hl_lines="5"
from starlette_admin._types import RowActionsDisplayType


class ArticleView(ModelView):
    row_actions_display_type = RowActionsDisplayType.DROPDOWN
```

<img width="1262" alt="Screenshot 2023-10-21 at 4 48 06 PM" src="https://github.com/jowilf/starlette-admin/assets/31705179/cf58efff-2744-4e4f-8e67-fc24fec8746b">
