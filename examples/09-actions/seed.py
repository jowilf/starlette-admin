import random

from app import Article, Status
from sqlalchemy.orm import Session

_FIXTURE = [
    (
        "His mother had always taught him",
        "His mother had always taught him not to ever think of himself as better "
        "than others. He'd tried to live by this motto.",
    ),
    (
        "He was an expert but not in a discipline",
        "He was an expert but not in a discipline that anyone could fully appreciate. "
        "He knew how to hold the cone just right so that soft-serve ice-cream fell perfectly.",
    ),
    (
        "Dave watched as the forest burned up on the hill",
        "Dave watched as the forest burned up on the hill, only a few miles from her "
        "house. The car had been hastily packed and Marta was inside rounding up the pets.",
    ),
    (
        "All he wanted was a candy bar",
        "All he wanted was a candy bar. It didn't seem like a difficult request, but "
        "the clerk remained frozen and didn't seem to want to honor it.",
    ),
    (
        "Hopes and dreams were dashed that day",
        "Hopes and dreams were dashed that day. It should have been expected, but it "
        "still came as a shock. The warning signs had been ignored.",
    ),
    (
        "Dave wasn't exactly sure how he had ended up",
        "Dave wasn't exactly sure how he had ended up in this predicament. He ran "
        "through all the events that had led to this current situation.",
    ),
    (
        "This is important to remember",
        "This is important to remember. Love isn't like pie. You don't need to divide "
        "it among all your friends and loved ones.",
    ),
    (
        "One can cook on and with an open fire",
        "One can cook on and with an open fire. Cooking meat using a spit is a great "
        "way to evenly cook meat, slowly rotating it to avoid burning.",
    ),
    (
        "There are different types of secrets",
        "There are different types of secrets. She had held onto plenty of them during "
        "her life, but this one was different.",
    ),
    (
        "They rushed out the door",
        "They rushed out the door, grabbing anything and everything they could think "
        "of. Thirty minutes later they were safe, but they'd forgotten the most important thing.",
    ),
]


def seed(session: Session) -> None:
    for title, body in _FIXTURE:
        session.add(
            Article(
                title=title,
                body=body,
                status=random.choice(list(Status)),
                views=random.randint(0, 1000),
            )
        )
    session.commit()
