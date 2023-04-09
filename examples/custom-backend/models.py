import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, TypedDict

from tinydb import Query
from tinydb.table import Document


class Comment(TypedDict):
    username: str
    body: str


@dataclass
class Post:
    title: str
    body: str
    tags: List[str]
    comments: List[Comment] = field(default_factory=list)
    id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if k != "id"}

    def to_document(self) -> Document:
        return Document(self.to_dict(), doc_id=self.id)

    def update(self, data: Dict) -> None:
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @classmethod
    def from_document(cls, doc: Document) -> "Post":
        return cls(**doc, id=doc.doc_id)

    @classmethod
    def search_query(cls, term: str):
        q = Query()
        return (
            q.title.search(term, flags=re.IGNORECASE)
            | q.body.search(term, flags=re.IGNORECASE)
            | q.tags.test(
                lambda tags: any(re.match(term, tag, re.IGNORECASE) for tag in tags)
            )
        )
