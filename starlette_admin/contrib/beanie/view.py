import io
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional, Sequence, Tuple, Type, Union

import starlette_admin.fields as sa
from beanie import Document, PydanticObjectId
from beanie.odm.enums import SortDirection
from beanie.operators import In, Or
from bson import ObjectId
from devtools import debug
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorGridFSBucket
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
# async def populate_link(field_model):
#     if hasattr(field_class, "get_link_fields"):
#         if len(field_links):


# # not using....
# async def populate_links(search_result):
#     for item in search_result:
#         # each item is a tuple
#         for _field_name, field_value in item:

#             if issubclass(field_class, List):
#                 # field_value is a list, I loop through it
#                 for _item in field_value:


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
            # _all_list has the names of the model fields (class)
            _all_list = list(document.__fields__)
            self.fields = _all_list

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

                # I have to find a way to obtain in beanie the type of each field of the Document class
                # for this I use document.__annotations__[field]
                # example:
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
        if where is None:
            return await self.document.count()

        if isinstance(where, dict):
            w = Where(where)
            q = w.builder()
            return await self.document.find_many(q).count()
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
        query_sort: Union[
            None, str, List[Tuple[str, SortDirection]]
        ] = build_order_clauses(order_by)

        if where is None:
            r = await self.document.find_many(
                skip=skip,
                limit=limit,
                sort=query_sort,
                fetch_links=True,
            ).to_list()
            return r

        debug(where)
        if isinstance(where, dict):
            w = Where(where)
            q = w.builder()
            debug(q)
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

    def _type_of(self, field_name: str) -> None:
        for field in self.fields:
            if field.name == field_name:
                debug(field)

    def _get_field(self, field_name: str) -> Union[None, Any]:
        for field in self.fields:
            if field.name == field_name:
                return field
        return None

    async def _put_thumbnail(
        self, thumbnail: Image.Image, format: Union[str, None], db: AsyncIOMotorDatabase
    ) -> PydanticObjectId:
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

    async def populate_file_field(
        self, data: Dict, object_old: Union[Document, None] = None
    ) -> Dict:
        bucket_name = "fs_files"
        db = self.document.get_settings().motor_db
        gfs = AsyncIOMotorGridFSBucket(db, bucket_name=bucket_name)

        # generate a new dict based on 'data' so I can instantiate an object
        # with default values without error
        # I only need that object to get from the 'motor_db' beanie

        # 'data', I have to check if the field is a FileField (it's a special case)
        # to do this search in self.fields
        # get a Dict with a Tuple with [UploadFile,bool] take that it is a 'File'

        for key, _value in data.items():
            # get starlette-admin Field, example: StringField, ImageField, ...etc
            f = self._get_field(key)

            if (
                f is not None
                and hasattr(f, "field")
                and isinstance(f.field, sa.HasMany)
                and _value is not None
            ):
                # convert id str as ObjectId
                lst = [ObjectId(v) for v in _value[0]]
                data[key] = lst

            thumb_id = None
            if self.is_type_of(key, sa.FileField):
                # 1st) element of the tuple, is the UploadFile object
                upload = data[key][0]

                # 2nd) element of the tuple, checkbox is Delete? (True/False)
                delete = data[key][1]

                if object_old is None and upload is None:
                    data[key] = None
                    continue

                # if upload is empty, it means that the field is optional
                # and the user did not load anything or was able to select the delete checkbox?
                # in that case, delete and go to look for the next field

                # cases:
                # case a) load a file and replace old file
                if object_old is not None:
                    file_old = getattr(object_old, key, None)
                    if file_old and upload:
                        gfs.delete(file_id=file_old.file_name.gfs_id)
                    # case b) previuos file exist, but not loaded and delete is set
                    if file_old and upload is None and delete:
                        gfs.delete(
                            file_id=file_old.file_name.gfs_id
                        )  # I also have to delete it from gfs
                        data[key] = None
                        continue
                # case c) not previus file, but upload file
                if upload:
                    # ------
                    filename = upload.filename  # str
                    contents = await upload.read()  # bytes
                    content_type = upload.content_type  # str

                    metadata = await self.get_image_metadata(content_type, contents, db)

                    id = await gfs.upload_from_stream(
                        filename=filename,
                        source=contents,
                        metadata=metadata,
                    )

                    db_name = getattr(db, "name", "fastapi_admin")
                    fgfs = FileGfs(
                        gfs_id=id,
                        filename=filename,
                        content_type=content_type,
                        thumbnail_id=thumb_id,
                        db_name=db_name,
                    )
                    tmp = File(file_name=fgfs)

                    # replace the 'key' of the UploadFile dict to FileGFs
                    data[key] = tmp

        return data

    async def create(self, request: Request, data: Dict[str, Any]) -> Any:
        data = await self.populate_file_field(data=data)
        doc = self.document(**data)
        try:
            return await doc.create()
        except Exception as e:
            self.handle_exception(e)

    async def edit(self, request: Request, pk: Any, data: Dict[str, Any]) -> Any:
        try:
            r = await self.document.get(pk)
            data = await self.populate_file_field(data=data, object_old=r)
            tmp = self.document(**data)
            # I don't use 'update' because it adds keys that don't exist
            # if you don't do this, the fields, for example password, are saved without hashing
            temp = tmp.dict()
            for key in data:
                if key in temp:
                    data[key] = temp[key]

            # if no errors, then save
            # only update the fields that come in 'data'
            # that's why I use set and not save
            if r is not None:
                await r.set(data)
            if r is not None:
                await r.set({"updated_at": datetime.utcnow()})
            return r
        except Exception as e:
            self.handle_exception(e)

    async def delete(self, request: Request, pks: List[Any]) -> Optional[int]:
        # convert the id str to id ObjectId
        ids = []
        for pk in pks:
            ids.append(ObjectId(pk))
        try:
            r = await self.document.find({"_id": {"$in": ids}}).delete()
            if r is not None:
                return r.deleted_count
        except Exception as e:
            self.handle_exception(e)
        return 0

    def handle_exception(self, exc: Exception) -> None:
        if isinstance(exc, ValidationError):
            raise pydantic_error_to_form_validation_errors(exc)

        if isinstance(exc, DuplicateKeyError):
            raise pymongo_error_to_form_validation_errors(exc)

        raise exc  # pragma: no cover

    async def build_full_text_search_query(
        self,
        request: Request,
        term: Union[Dict[str, Any], str, None],
    ) -> Or:
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

    async def get_image_metadata(
        self, content_type: str, contents: Any, db: Union[Any, None]
    ) -> Dict:
        """get information from the image"""

        # default value
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
                    "thumbnail_id": str(thumb_id),
                }

        except OSError:
            pass
        return metadata
