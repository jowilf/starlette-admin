"""Seed script to populate initial sample articles for the authentication example."""

import random

from sqlalchemy import Engine
from sqlalchemy.orm import Session

ARTICLES = [
    (
        "His mother had always taught him",
        "His mother had always taught him not to ever think of himself as better than others. He'd tried to live by this motto. He never looked down on those who were less fortunate or who had less money than him. But the stupidity of the group of people he was talking to made him change his mind.",
    ),
    (
        "He was an expert but not in a discipline",
        "He was an expert but not in a discipline that anyone could fully appreciate. He knew how to hold the cone just right so that the soft serve ice-cream fell into it at the precise angle to form a perfect cone each and every time. It had taken years to perfect and he could now do it without even putting any thought behind it.",
    ),
    (
        "Dave watched as the forest burned up on the hill",
        "Dave watched as the forest burned up on the hill, only a few miles from her house. The car had been hastily packed and Marta was inside trying to round up the last of the pets. Dave went through his mental list of the most important papers and documents that they couldn't leave behind.",
    ),
    (
        "All he wanted was a candy bar",
        "All he wanted was a candy bar. It didn't seem like a difficult request to comprehend, but the clerk remained frozen and didn't seem to want to honor the request. It might have had something to do with the gun pointed at his face.",
    ),
    (
        "Hopes and dreams were dashed that day",
        "Hopes and dreams were dashed that day. It should have been expected, but it still came as a shock. The warning signs had been ignored in favor of the possibility, however remote, that it could actually happen.",
    ),
    (
        "Dave wasn't exactly sure how he had ended up",
        "Dave wasn't exactly sure how he had ended up in this predicament. He ran through all the events that had lead to this current situation and it still didn't make sense. He wanted to spend some time to try and make sense of it all, but he had higher priorities at the moment.",
    ),
    (
        "This is important to remember",
        "This is important to remember. Love isn't like pie. You don't need to divide it among all your friends and loved ones. No matter how much love you give, you can always give more. It doesn't run out, so don't try to hold back giving it as if it may one day run out.",
    ),
    (
        "One can cook on and with an open fire",
        "One can cook on and with an open fire. These are some of the ways to cook with fire outside. Cooking meat using a spit is a great way to evenly cook meat. In order to keep meat from burning, it's best to slowly rotate it.",
    ),
    (
        "There are different types of secrets",
        "There are different types of secrets. She had held onto plenty of them during her life, but this one was different. She found herself holding onto the worst type: the kind that could gnaw away at your insides if you didn't tell someone about it.",
    ),
    (
        "They rushed out the door",
        "They rushed out the door, grabbing anything and everything they could think of they might need. There was no time to double-check to make sure they weren't leaving something important behind. Everything was thrown into the car and they sped off.",
    ),
]


def seed_articles(engine: Engine) -> None:
    from app import Article, ArticleStatus

    with Session(engine) as session:
        if session.query(Article).count() > 0:
            return

        random.seed(42)
        for title, body in ARTICLES:
            session.add(
                Article(
                    title=title,
                    body=body,
                    status=random.choice(list(ArticleStatus)),
                )
            )
        session.commit()
