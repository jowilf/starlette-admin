# Özelleştirilmiş Alanlar (Fields)

*Starlette-Admin* halihazırda birçok yerleşik [alan][starlette_admin.fields.BaseField] içerir. Ancak, ihtiyacınıza göre alanı geçersiz kılabilir veya kendi alanınızı oluşturabilirsiniz.

!!! important "Önemli"
    Yeni bir alan oluşturmadan önce, mevcut olanları genişletmeyi deneyin. Çoğu duruma uyacak kadar esnektirler.

Yeni bir nesne tanımlamak için ilk adım, [BaseField][starlette_admin.fields.BaseField] veya diğer alanlardan türetilmiş bir sınıf tanımlamaktır.

```python
from starlette_admin import BaseField
from dataclasses import dataclass

@dataclass
class CustomField(BaseField):
    pass
```

## Liste Derleme

*Starlette-Admin* listeleri derlemek için [Datatables](https://datatables.net/) kullanır. Varsayılan olarak, tüm alanlar <abbr title="text">metin</abbr> alanı olarak derlenir. Bu davranışı özelleştirmek için, datatable içinde sütununuzu derleyecek bir JavaScript fonksiyonu yazmanız gerekir. Kendi fonksiyonunuzu nasıl yazabileceğinizle ilgili daha fazla bilgi için [Datatables documentation](https://datatables.net/reference/option/columns.render) sayfasından faydalanabilirsiniz.

* Öncelikle ilave derleme fonksiyonunun bulunduğu javascript dosyanızın bağlantısını `admin` sınıfını geçersiz kılarak sağlamanız gerekiyor.

!!! example "Örnek"
    SQLAlchemy arayüzü ile basit bir örnek görelim.

    ```python
    from starlette_admin.contrib.sqla import Admin as BaseAdmin

    class Admin(BaseAdmin):
        def custom_render_js(self, request: Request) -> Optional[str]:
            return request.url_for("statics", path="js/custom_render.js")

    admin = Admin(engine)
    admin.add_view(...)
    ```

    ```js title="statics/js/custom_render.js"
    Object.assign(render, {
      mycustomkey: function render(data, type, full, meta, fieldOptions) {
            ...
      },
    });
    ```

!!! note "Not"
    `fieldOptions`, alanınızı, javascript nesnesi olarak temsil eder. Alan özellikleriniz, dataclass `asdict` fonksiyonu kullanılarak javascript nesnesine dönüştürülür.

* Sonrasında `render_function_key` değerini atayın.

```python
from starlette_admin import BaseField
from dataclasses import dataclass

@dataclass
class CustomField(BaseField):
    render_function_key: str = "mycustomkey"
```

## Form

Form derlemeleri için şablonlarınızın bulunduğu dizinde `forms` klasörü altında yeni bir html dosyası oluşturmanız gerekir.

Varolan Jinja2 değişkenleri şunlardır:

* `field`: alan örneği.
* `error`: `FormValidationError`dan gelen hata mesajı.
* `data`: geçerli değer. Düzenlerken veya doğrulama hatası oluştuğunda kullanılabilir.
* `action`: `EDIT` veya `CREATE`

!!! example "Örnek"

    ```html title="forms/custom.html"
    <div class="{%if error%}is-invalid{%endif%}">
        <input id="{{field.id}}" name="{{field.id}}" ... />
        {% if field.help_text %}
        <small class="form-hint">{{field.help_text}}</small>
        {%endif%}
    </div>
    {%if error %}
    <div class="invalid-feedback">{{error}}</div>
    {%endif%}
    ```

```python
from starlette_admin import BaseField
from dataclasses import dataclass

@dataclass
class CustomField(BaseField):
    render_function_key: str = "mycustomkey"
    form_template: str = "forms/custom.html"
```

## Detay Görünümü

Alanınızı detaylar görünümünde derlemek için şablonlarınızın bulunduğu dizininizde `displays` klasörü altında yeni bir html dosyası oluşturmanız gerekiyor.

Varolan Jinja2 değişkenleri şunlardır:

* `field`: alan örneği.
* `data`: görüntülenecek değer.

!!! example "Örnek"

    ```html title="displays/custom.html"
    <span>Hello {{data}}</span>
    ```

```python
from starlette_admin import BaseField
from dataclasses import dataclass

@dataclass
class CustomField(BaseField):
    render_function_key: str = "mycustomkey"
    form_template: str = "forms/custom.html"
    display_template: str = "displays/custom.html"
```

## Veri İşleme

Veri işleme için şu iki metodu geçersiz kılmanız gerekir:

* `process_form_data`: Alan değerini, Python sözlük nesnesine dönüştürürken çağrılacaktır.
* `serialize_field_value`: API üzerinden gönderilmiş veriyi serileştirmek için çağrılacaktır. Bu, *derleme* metodunuzda alacağınız aynı veridir.

```python
from dataclasses import dataclass
from typing import Any, Dict

from requests import Request
from starlette.datastructures import FormData
from starlette_admin import BaseField


@dataclass
class CustomField(BaseField):
    render_function_key: str = "mycustomkey"
    form_template: str = "forms/custom.html"
    display_template: str = "displays/custom.html"

    async def parse_form_data(self, request: Request, form_data: FormData) -> Any:
        return form_data.get(self.name)

    async def serialize_value(self, request: Request, value: Any, action: RequestAction) -> Any:
        return value

    def dict(self) -> Dict[str, Any]:
        return super().dict()

```

!!! important "Önemli"
    JavaScript tarafında kullanılabilen seçeneklerin kontrolünü ele geçirmek için `dict` fonksiyonunu geçersiz kılın.
