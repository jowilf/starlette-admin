from datetime import datetime

from app import Post
from sqlalchemy.orm import Session

_FIXTURE = [
    (
        "His mother had always taught him",
        "His mother had always taught him not to ever think of himself as better "
        "than others. He'd tried to live by this motto. He never had.",
    ),
    (
        "Dave watched as the forest burned",
        "Dave watched as the forest burned up on the hill, only a few miles from "
        "her house. The car had been hastily packed and Marta was inside rounding "
        "up the pets.",
    ),
    (
        "All he wanted was a candy bar",
        "All he wanted was a candy bar. It didn't seem like a difficult request, "
        "but the clerk remained frozen and didn't seem to want to honor it.",
    ),
    (
        "Hopes and dreams were dashed that day",
        "Hopes and dreams were dashed that day. It should have been expected, but "
        "it still came as a shock. The warning signs had been ignored in plain "
        "sight.",
    ),
    (
        "There are different types of secrets",
        "There are different types of secrets. She had held onto plenty of them "
        "during her life, but this one was different. This one could change "
        "everything.",
    ),
    (
        "They rushed out the door",
        "They rushed out the door, grabbing anything and everything they could "
        "think of. Thirty minutes later they were safe, but they'd forgotten "
        "the most important thing.",
    ),
    (
        "The treasure map had been in her family",
        "The treasure map had been in her family for generations. No one had ever "
        "followed it, until now. She folded it carefully and set out at dawn.",
    ),
    (
        "One can cook on and with an open fire",
        "One can cook on and with an open fire. Cooking meat using a spit is a "
        "great way to evenly cook meat, slowly rotating it to avoid burning.",
    ),
]

# Two of the posts start in the trash so the trash view is non-empty on first run.
_DELETED_TITLES = {
    "Dave watched as the forest burned",
    "One can cook on and with an open fire",
}


def seed(session: Session) -> None:
    now = datetime.utcnow()
    for title, body in _FIXTURE:
        deleted_at = now if title in _DELETED_TITLES else None
        session.add(
            Post(
                title=title,
                body=body,
                created_at=now,
                deleted_at=deleted_at,
            )
        )
    session.commit()
