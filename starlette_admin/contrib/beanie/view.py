import io
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional, Sequence, Type, Union

import starlette_admin.fields as sa
from beanie import Document
from beanie.operators import In, Or
from bson import ObjectId
from devtools import debug
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from PIL import Image
from pydantic import ValidationError
from pymongo.errors import DuplicateKeyError
from starlette.requests import Request
from starlette_admin.contrib.beanie._file import File, FileGfs
from starlette_admin.contrib.beanie.beanie_expr import Expr, Where
from starlette_admin.contrib.beanie.helpers import (
    convert_beanie_field_to_admin_field,
    normalize_list,
    pymongo_error_to_form_validation_errors,
)
from starlette_admin.contrib.beanie.pyd import Attrs
from starlette_admin.contrib.beanie.sort import build_order_clauses
from starlette_admin.helpers import (
    prettify_class_name,
    pydantic_error_to_form_validation_errors,
    slugify_class_name,
)
from starlette_admin.views import BaseModelView


# not using....
async def populate_link(field_model):
    field_class = type(field_model)
    if hasattr(field_class, "get_link_fields"):
        field_links = field_class.get_link_fields()
        if len(field_links):
            await field_model.fetch_all_links()


# not using....
async def populate_links(search_result):
    for item in search_result:
        # cada item es una tupla
        for _field_name, field_value in item:
            field_class = type(field_value)

            if issubclass(field_class, List):
                # field_value es una lista, la recorro
                for _item in field_value:
                    await populate_link(_item)
            else:
                await populate_link(item)


class ModelView(BaseModelView):
    def __init__(
        self,
        document: Type[Document],
        icon: Optional[str] = None,
        name: Optional[str] = None,
        label: Optional[str] = None,
        identity: Optional[str] = None,
    ):
        self.document = document
        self.identity = identity or slugify_class_name(self.document.__name__)
        self.label = label or prettify_class_name(self.document.__name__) + "s"
        self.name = name or prettify_class_name(self.document.__name__)
        self.icon = icon
        self.pk_attr = "id"

        if self.fields is None or len(self.fields) == 0:
            # _all_list tiene los nombres de los campos del modelo (class)
            _all_list = list(document.__fields__)
            self.fields = _all_list  # type: ignore[override]

        attr_list = Attrs(document)

        converted_fields = []
        for value in self.fields:
            field_meta = document.__fields__.get(str(value))

            # get field information from pydantic class
            attr = attr_list.get_field_info(str(value))

            if isinstance(value, sa.BaseField):
                converted_fields.append(value)
            else:
                if isinstance(value, str) and hasattr(document, value):
                    field = value
                else:
                    raise ValueError(f"Can't find field with key {value}")

                # tengo que buscar la manera de obtener en benie el tipo de cada campo de la class Document
                # para esto utilizo document.__annotations__[field]
                # ejemplo:
                # document.__annotations__: {
                # } (dict) len=4

                annotations = document.__annotations__.get(field, None)

                # if field not in [
                #   "revision_id",
                #   "id",
                #   "created_at",
                #   "updated_at",
                # ]:
                converted_fields.append(
                    convert_beanie_field_to_admin_field(
                        field, annotations, attr, field_meta, identity
                    )
                )

        self.fields = converted_fields
        self.exclude_fields_from_list = normalize_list(self.exclude_fields_from_list)  # type: ignore
        self.exclude_fields_from_detail = normalize_list(self.exclude_fields_from_detail)  # type: ignore
        self.exclude_fields_from_create = normalize_list(self.exclude_fields_from_create)  # type: ignore
        self.exclude_fields_from_edit = normalize_list(self.exclude_fields_from_edit)  # type: ignore
        self.searchable_fields = normalize_list(self.searchable_fields)
        self.sortable_fields = normalize_list(self.sortable_fields)
        self.export_fields = normalize_list(self.export_fields)
        self.fields_default_sort = normalize_list(
            self.fields_default_sort, is_default_sort_list=True
        )
        super().__init__()

    async def count(
        self,
        request: Request,
        where: Union[Dict[str, Any], str, None] = None,
    ) -> int:
        print(where)
        if where is None:
            return await self.document.count()
        q = await self.build_full_text_search_query(request=request, term=where)
        return await self.document.find_many(q).count()

    def _build_query(
        self, request: Request, where: Union[Dict[str, Any], str, None] = None
    ) -> Any:
        if where is None:
            return {}
        if isinstance(where, dict):
            return Where(**where).builder()
        return None

    async def find_all(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        where: Union[Dict[str, Any], str, None] = None,
        order_by: Optional[List[str]] = None,
    ) -> Sequence[Any]:
        query_sort = build_order_clauses(order_by)

        if where is None:
            r = await self.document.find_many(
                skip=skip,
                limit=limit,
                sort=query_sort,
                fetch_links=True,
            ).to_list()
            return r

        if isinstance(where, dict):
            w = Where(where)
            q = w.builder()
            rq = await self.document.find_many(
                q,
                skip=skip,
                limit=limit,
                sort=query_sort,
                fetch_links=True,
            ).to_list()
        else:
            q = await self.build_full_text_search_query(request=request, term=where)
            rq = await self.document.find_many(
                q,
                skip=skip,
                limit=limit,
                sort=query_sort,
                fetch_links=True,
            ).to_list()

        return rq

    async def find_by_pk(self, request: Request, pk: Any) -> Optional[Document]:
        try:
            r = await self.document.get(pk, fetch_links=True)
            return r
        except Exception:
            return None

    async def find_by_pks(self, request: Request, pks: List[Any]) -> Sequence[Document]:
        return await self.document.find(
            In(self.document.id, [ObjectId(i) for i in pks]),
            fetch_links=False,
        ).to_list()

    def is_type_of(self, field_name: str, class_type: Type) -> bool:
        for field in self.fields:
            if field.name == field_name and isinstance(field, class_type):
                return True
        return False

    def _type_of(self, field_name: str):
        for field in self.fields:
            if field.name == field_name:
                debug(field)

    def _get_field(self, field_name: str):
        for field in self.fields:
            if field.name == field_name:
                return field
        return None

    async def _put_thumbnail(self, thumbnail, format, db, **kwargs):
        bucket_name = "fs_files"
        gfs = AsyncIOMotorGridFSBucket(db, bucket_name=bucket_name)

        # re-size
        size = 128, 128
        thumbnail.thumbnail(size)
        w, h = thumbnail.size

        io = BytesIO()
        thumbnail.save(io, format)
        io.seek(0)

        metadata = {
            "format": format,
            "width": w,
            "height": h,
        }

        return await gfs.upload_from_stream(
            filename="thumbnail",
            source=io,
            metadata=metadata,
        )

    async def populate_FileField(self, data: Dict, object_old: Document = None):  # noqa
        bucket_name = "fs_files"
        db = self.document.get_settings().motor_db
        gfs = AsyncIOMotorGridFSBucket(db, bucket_name=bucket_name)

        # genero un nuevo dict basado en 'data' para poder instanciar un objeto
        # con los valores por default sin que me error
        # ese objeto unicamente lo necesito para obtener de beanie 'motor_db'
        # ...pendiente

        # 'data', tengo que verificar si el field es un FileField (es un caso especial)
        # para ello buscar en  self.fields
        # venga un Dict con una Tuple con [UploadFile,bool] tomo que es un 'File'
        for key, _value in data.items():
            f = self._get_field(key)
            if (
                hasattr(f, "field")
                and isinstance(f.field, sa.HasMany)
                and _value is not None
            ):
                # convert id str as ObjectId
                lst = [ObjectId(v) for v in _value[0]]
                data[key] = lst

            thumb_id = None
            if self.is_type_of(key, sa.FileField):
                # creo un objeto vacio, con los valores por default

                # 1° elemento de la Tuple, es el objeto UploadFile
                upload = data[key][0]

                # 2° elemento de la Tuple, checkbox es Delete? (True/False)
                delete = data[key][1]

                # si upload esta vacio, quiere decir que el campo es opcional
                # y el usuario no cargo nada o bien pudo seleccionar el checkbox delete?
                # en ese caso, borro y paso a buscar el proximo field
                if upload is None:
                    # si estoy en edit, tiene cargado un file pero en la edicion
                    # no se pone nada mantengo el file anterior
                    f = None
                    if object_old is not None:
                        f = getattr(object_old, key)
                    if f:
                        # si habia un valor anterior y el flag 'delete' es True lo borro
                        if delete:
                            data[key] = None
                            # tambien lo tengo que borrar de gfs
                            gfs.delete(file_id=f.file_name.gfs_id)

                        else:
                            data[key] = f
                    else:
                        data[key] = None
                    continue
                else:  # noqa
                    # si habia un valor anterior, y lo cambie, tengo que borrar el 'fs' anterior
                    #
                    if object_old is not None:
                        f = getattr(object_old, key)
                        if f:
                            gfs.delete(file_id=f.file_name.gfs_id)

                filename = upload.filename  # str
                contents = await upload.read()  # bytes
                content_type = upload.content_type  # str

                # 2° elemento de la Tuple es ...averiguar
                # ...

                # obtengo informacion de la imagen y la gaurdo en gridfs

                metadata = {"contentType": content_type}
                try:
                    with Image.open(io.BytesIO(contents)) as img:
                        thumbnail = img.copy()
                        thumb_id = await self._put_thumbnail(thumbnail, img.format, db)
                        metadata = {
                            "contentType": content_type,
                            "format": img.format,
                            "width": img.size[0],
                            "height": img.size[1],
                            "mode": img.mode,
                            "thumbnail_id": thumb_id,
                        }

                except OSError:
                    pass

                id = await gfs.upload_from_stream(
                    filename=filename,
                    source=contents,
                    metadata=metadata,
                )

                fgfs = FileGfs(
                    gfs_id=id,
                    filename=filename,
                    content_type=content_type,
                    thumbnail_id=thumb_id,
                    db_name=db.name,
                )
                tmp = File(file_name=fgfs)

                # reemplazo el 'key' del dict de UploadFile a FileGFs
                data[key] = tmp

        return data

    async def create(self, request: Request, data: Dict[str, Any]) -> Any:
        data = await self.populate_FileField(data=data)
        doc = self.document(**data)
        try:
            return await doc.create()
        except Exception as e:
            self.handle_exception(e)

    async def edit(self, request: Request, pk: Any, data: Dict[str, Any]) -> Any:
        try:
            r = await self.document.get(pk)
            data = await self.populate_FileField(data=data, object_old=r)
            tmp = self.document(**data)
            # no utilizo 'update' porque me agrega las key que no existen
            # realizo el update
            # si no hacia esto, los campos por ejemplo password, se guardan sin hashing
            temp = tmp.dict()
            for key in data:
                if key in temp:
                    data[key] = temp[key]

            # if no errors, then save
            # solo actualizo los campos que vienen en 'data'
            # por eso utilizo set y no save
            await r.set(data)
            await r.set({"updated_at": datetime.utcnow()})
            return r
        except Exception as e:
            self.handle_exception(e)

    async def delete(self, request: Request, pks: List[Any]) -> Optional[int]:
        # convierto los id str en id ObjectId
        ids = []
        for pk in pks:
            ids.append(ObjectId(pk))
        try:
            r = await self.document.find({"_id": {"$in": ids}}).delete()
            if r is not None:
                return r.deleted_count
            return 0
        except Exception as e:
            self.handle_exception(e)

    def handle_exception(self, exc: Exception) -> None:
        if isinstance(exc, ValidationError):
            raise pydantic_error_to_form_validation_errors(exc)

        if isinstance(exc, DuplicateKeyError):
            raise pymongo_error_to_form_validation_errors(exc)

        raise exc  # pragma: no cover

    async def build_full_text_search_query(self, request: Request, term: str):
        queries = []
        for field in self.fields:
            if (
                field.searchable
                and field.name != "id"
                and type(field)
                in [
                    sa.StringField,
                    sa.TextAreaField,
                    sa.EmailField,
                    sa.URLField,
                    sa.PhoneField,
                    sa.ColorField,
                ]
            ):
                queries.append(Expr(current_field=field.name).regex(term).get_query())

        return Or(*queries)
