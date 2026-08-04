from typing import Any

from pydantic import BaseModel, ValidationError
from starlette.requests import Request
from starlette_admin.contrib.sqla.converters import BaseSQLAModelConverter
from starlette_admin.contrib.sqla.view import ModelView as BaseModelView
from starlette_admin.helpers import pydantic_error_to_form_validation_errors


class ModelView(BaseModelView):
    """A SQLAlchemy `ModelView` that validates form data with a Pydantic model.

    Example:

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


        admin.add_view(ModelView(Post, pydantic_model=PostIn))

        ```
    """

    def __init__(
        self,
        model: type[Any],
        pydantic_model: type[BaseModel],
        icon: str | None = None,
        display_name: str | None = None,
        menu_label: str | None = None,
        key: str | None = None,
        converter: BaseSQLAModelConverter | None = None,
    ):
        self.pydantic_model = pydantic_model
        super().__init__(model, icon, display_name, menu_label, key, converter)

    async def validate(self, request: Request, data: dict[str, Any]) -> None:
        try:
            self.pydantic_model(**data)
        except ValidationError as error:
            raise pydantic_error_to_form_validation_errors(error) from error
