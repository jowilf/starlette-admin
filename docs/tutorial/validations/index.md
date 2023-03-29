# Forms Validations

Starlette-admin is designed to be flexible and agnostic to your specific database backend. Therefore, it doesn't include
built-in data validation capabilities. Instead, data validation will depend on the validation mechanisms provided by
your chosen database backend.

## SQLAlchemy

There are several options available for validating your data:

### Pydantic

[Pydantic](https://github.com/pydantic/pydantic) is a widely used Python library that provides data validation
capabilities using Python's type hints.

To automatically validate submitted data with Pydantic, you only need to define a Pydantic model and
use `starlette_admin.contrib.sqla.ext.pydantic.ModelView`

!!!Example

    ```python
    from starlette_admin.contrib.sqla.ext.pydantic import ModelView


    class Post(Base):
        __tablename__ = "posts"

        id = Column(Integer, primary_key=True)
        title = Column(String)
        content = Column(Text)
        views = Column(Integer)


    class PostIn(BaseModel):
        id: Optional[int] = Field(primary_key=True)
        title: str = Field(min_length=3)
        content: str = Field(min_length=10)
        views: int = Field(multiple_of=4)

        @validator("title")
        def title_must_contain_space(cls, v):
            if " " not in v.strip():
                raise ValueError("title must contain a space")
            return v.title()


    # Add view
    admin.add_view(ModelView(Post, pydantic_model=PostIn))

    ```

### Custom Validation

You can also create your own validation functions to enforce specific data requirements.

!!!Example
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
    Full example available [here](https://github.com/jowilf/starlette-admin/tree/main/examples/sqla)


## SQLModel

With SQLModel, validating your data is made easy. Once you've defined your model, any data submitted to it will be
automatically validated.

!!! Example
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
    Full example available [here](https://github.com/jowilf/starlette-admin/tree/main/examples/sqlmodel)



## Odmantic

Validation of submitted data is handled seamlessly by Odmantic. Any data that you submit to your defined model will be
validated automatically.

!!! Example
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
    Full example available [here](https://github.com/jowilf/starlette-admin/tree/main/examples/odmantic)


## MongoEngine

The submitted data will be automatically validated according to your model definition.

!!! Example
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
    Full example available [here](https://github.com/jowilf/starlette-admin/tree/main/examples/mongoengine)
