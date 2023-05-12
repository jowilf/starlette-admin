import inspect
from typing import Dict, List, Optional, Type, TypeVar

from beanie import Document
from pydantic import BaseModel, ConstrainedStr

BaseModelT = TypeVar("BaseModelT", bound=Document)


class Attr(BaseModel):
    name: str
    required: bool = False
    min_length: int = None
    max_length: int = None
    description: Optional[str]
    model_class: Optional[Type[BaseModel]]
    linked: Dict = None


class Attrs:
    attributes: List[Attr] = []

    def __init__(self, model: Type[BaseModelT]):
        """
        initialize class based in pydantic class definition
        """

        # if the model (class Beanie Document), has no 'Link' fields
        # returns empty, even if a field is of another class that does have Link fields
        # that's why, for class composition, I have to get the information from 'links'
        # example:
        # self.document.get_link_fields(): {
        #     'principals': LinkInfo(
        #         model_class=<class 'examples.beanie.user.user.Principal'>,
        #         link_type=<LinkTypes.OPTIONAL_LIST: 'OPTIONAL_LIST'>,
        #     ),
        # } (dict) len=1

        linked = model.get_link_fields()  # return a Dict
        self.linked = linked

        for name, field in model.__fields__.items():
            # if the field is a 'composition' of another pydantic model
            # I search if that field has any 'Link'
            # since I'm going to need it to be able to assign the 'identity' field
            # of the HasMany or HasOne class
            field_model = model.__fields__.get(str(name))
            field_class = getattr(field_model, "type_", None)
            field_links = {}
            if hasattr(field_class, "get_link_fields"):
                field_links = field_class.get_link_fields()
                self.linked = field_links

            if linked is None:
                linked = {}

            model_class = None
            if linked is not None and name in linked:
                model_class = linked[name].model_class
            if field_links is not None and name in field_links:  # type: ignore
                model_class = linked[name].model_class
                self.linked = field_links

            attr = Attr(
                required=getattr(field, "required", False),
                name=name,
                min_length=field.field_info.min_length,
                max_length=field.field_info.max_length,
                description=field.field_info.description,
                model_class=model_class,
                linked=self.linked,
            )
            self.attributes.append(attr)

        # update attr if const family
        for name, field in model.__annotations__.items():
            if inspect.isclass(field) and issubclass(field, ConstrainedStr):
                min_length = getattr(field, "min_length", None)
                max_length = getattr(field, "max_length", None)
                self.update_by_name(name, min_length, max_length)

    def update_by_name(self, name, min_length, max_length):
        for attr in self.attributes:
            if attr.name is name:
                attr.min_length = min_length
                attr.max_length = max_length

    def get_field_info(self, name: str):
        for attr in self.attributes:
            if attr.name is name:
                return attr
        return None

    def __repr__(self):
        d = []
        for attr in self.attributes:
            d.append(attr.json())
        return "\n".join(d)
