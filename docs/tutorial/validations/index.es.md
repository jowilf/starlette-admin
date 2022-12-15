# Validaciones de formularios

Por diseño, *Starlette-admin* no valida los datos que se envían a través de sus formularios. La validación dependerá del backend de la base de datos que se esté utilizando.

## SQLAlchemy

Cuando se trabaja con SQLAlchemy, es necesario escribir un código de validación propio para validar los datos enviados a través de los formularios.

!!!Ejemplo
    ```python
    from starlette_admin.contrib.sqla import ModelView
    from starlette_admin.exceptions import FormValidationError


    class PostView(ModelView):

        async def validate(self, request: Request, data: Dict[str, Any]) -> None:
            """Raise FormValidationError to display error in forms"""
            errors: Dict[str, str] = dict()
            _2day_from_today = date.today() + timedelta(days=2)
            if data["title"] is None or len(data["title"]) < 3:
                errors["title"] = "Ensure this value has at least 03 characters"
            if data["text"] is None or len(data["text"]) < 10:
                errors["text"] = "Ensure this value has at least 10 characters"
            if data["date"] is None or data["date"] < _2day_from_today:
                errors["date"] = "We need at least one day to verify your post"
            if data["publisher"] is None:
                errors["publisher"] = "Publisher is required"
            if data["tags"] is None or len(data["tags"]) < 1:
                errors["tags"] = "At least one tag is required"
            if len(errors) > 0:
                raise FormValidationError(errors)
            return await super().validate(request, data)
    ```

    ![SQLAlchemy Form Validations](../../images/validations/sqla.png)

??? info
    Ejemplo completo disponible [aquí](https://github.com/jowilf/starlette-admin/tree/main/examples/sqla)


## SQLModel

Para utilizar SQLModel, solo es necesario definir el modelo y los datos que se envían a través de los formularios serán validados automáticamente.

!!! Ejemplo
    ```python
    from sqlmodel import SQLModel, Field
    from pydantic import validator


    class Post(SQLModel, table=True):
        id: Optional[int] = Field(primary_key=True)
        title: str = Field()
        content: str = Field(min_length=10)
        views: int = Field(multiple_of=4)

        @validator('title')
        def title_must_contain_space(cls, v):
            if ' ' not in v:
                raise ValueError('title must contain a space')
            return v.title()
    ```

    ![SQLModel Form Validations](../../images/validations/sqlmodel.png)

??? info
    Ejemplo completo disponible [aquí](https://github.com/jowilf/starlette-admin/tree/main/examples/sqlmodel)



## Odmantic

Los datos enviados se validarán automáticamente de acuerdo con la definición de su modelo.

!!! Ejemplo
    ```python
    from typing import List, Optional

    from odmantic import EmbeddedModel, Field, Model
    from pydantic import EmailStr


    class Address(EmbeddedModel):
        street: str = Field(min_length=3)
        city: str = Field(min_length=3)
        state: Optional[str]
        zipcode: Optional[str]


    class Author(Model):
        first_name: str = Field(min_length=3)
        last_name: str = Field(min_length=3)
        email: Optional[EmailStr]
        addresses: List[Address] = Field(default_factory=list)

    ```

    ![SQLModel Form Validations](../../images/validations/odmantic.png)


??? info
    Ejemplo completo disponible [aquí](https://github.com/jowilf/starlette-admin/tree/main/examples/odmantic)


## MongoEngine

Los datos enviados se validarán automáticamente de acuerdo con la definición de su modelo.

!!! Ejemplo
    ```python
    import mongoengine as db

    class Comment(db.EmbeddedDocument):
        name = db.StringField(min_length=3, max_length=20, required=True)
        value = db.StringField(max_length=20)


    class Post(db.Document):
        name = db.StringField(max_length=20, required=True)
        value = db.StringField(max_length=20)
        inner = db.ListField(db.EmbeddedDocumentField(Comment))
        lols = db.ListField(db.StringField(max_length=20))
    ```

    ![SQLModel Form Validations](../../images/validations/mongoengine.png)

??? info
    Ejemplo completo disponible [aquí](https://github.com/jowilf/starlette-admin/tree/main/examples/mongoengine)
