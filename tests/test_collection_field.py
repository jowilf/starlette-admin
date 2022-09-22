from dataclasses import dataclass

from tests.dummy_model_view import DummyBaseModel, DummyModelView


class DBConfig:
    host: str
    username: str
    password: str


@dataclass
class Settings(DummyBaseModel):
    db_Config: DBConfig
    nested_config: dict


class SettingsView(DummyModelView):
    model = Settings
    # fields = (
    #     IntegerField("id"),
    #     StringField("title"),
    #     TextAreaField("content"),
    #     IntegerField("views"),
    #     TagsField("tags"),
    # )


class TestCollectionField:
    pass
