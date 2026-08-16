from dataclasses import dataclass

from starlette_admin.fields import HasOne


@dataclass
class BackwardHasOne(HasOne):
    """HasOne subclass used for Tortoise backward one-to-one relations.

    Kept as a distinct type so the filter registry can exclude it: unlike a
    forward relation, there is no raw key column on this model to null-check.
    """
