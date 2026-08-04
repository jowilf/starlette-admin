"""Integration tests for starlette_admin.contrib.sqla.filters.

Exercises every filter's apply() against a real in-memory SQLite session so we
get true SQL compilation and execution. Relationship branches are covered via
Item.category (scalar many-to-one) and Category.items (collection one-to-many).

Custom filter section at the bottom demonstrates how to subclass built-in
filters and how to filter on a relation field using SQLAlchemy's has()/any().
"""

import datetime
import enum
from typing import Any
from unittest.mock import MagicMock

import pytest
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    create_engine,
    select,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship
from starlette_admin.contrib.sqla.filters import (
    BetweenFilter,
    ContainsFilter,
    DateBetweenFilter,
    DateEqualFilter,
    DateInFutureFilter,
    DateInPastFilter,
    DateTimeBetweenFilter,
    DateTimeEqualFilter,
    EndsWithFilter,
    EqualFilter,
    GreaterThanFilter,
    GreaterThanOrEqualFilter,
    InFilter,
    IsFalseFilter,
    IsNotNullFilter,
    IsNullFilter,
    IsTrueFilter,
    LessThanFilter,
    LessThanOrEqualFilter,
    NotContainsFilter,
    NotEqualFilter,
    NotInFilter,
    NumericEqualFilter,
    NumericNotEqualFilter,
    StartsWithFilter,
    TimeBetweenFilter,
    TimeEqualFilter,
    _build_rule_clause,
    build_filter_clause,
)
from starlette_admin.fields import NumberField, RelationField, StringField
from starlette_admin.filters import FilterApplyContext, FilterGroup, FilterRule
from starlette_admin.filters.registry import FilterRegistry

# ── SA models ─────────────────────────────────────────────────────────────────


class Base(DeclarativeBase):
    pass


class ItemStatus(enum.StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Category(Base):
    __tablename__ = "sqla_filter_int_category"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    items: Mapped[list["Item"]] = relationship("Item", back_populates="category")


class Item(Base):
    __tablename__ = "sqla_filter_int_item"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    count: Mapped[int] = mapped_column(Integer)
    price: Mapped[float] = mapped_column(Float)
    is_available: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime)
    available_on: Mapped[datetime.date] = mapped_column(Date)
    available_from: Mapped[datetime.time] = mapped_column(Time)
    status: Mapped[ItemStatus] = mapped_column(Enum(ItemStatus))
    category_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sqla_filter_int_category.id"), nullable=True
    )
    category: Mapped["Category"] = relationship("Category", back_populates="items")


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture()
def seeded_session(engine):
    """Session pre-loaded with a Category and two Items for filter assertions."""
    with Session(engine) as s:
        cat = Category(name="Widgets")
        s.add(cat)
        s.flush()
        s.add(
            Item(
                name="Alpha",
                description="First item",
                count=10,
                price=9.99,
                is_available=True,
                created_at=datetime.datetime(2024, 3, 1, 12, 0),
                available_on=datetime.date(2024, 3, 1),
                available_from=datetime.time(8, 0),
                status=ItemStatus.ACTIVE,
                category_id=cat.id,
            )
        )
        s.add(
            Item(
                name="Beta",
                description="Second item",
                count=20,
                price=19.99,
                is_available=False,
                created_at=datetime.datetime(2024, 6, 1, 18, 0),
                available_on=datetime.date(2024, 6, 1),
                available_from=datetime.time(18, 0),
                status=ItemStatus.INACTIVE,
                category_id=None,
            )
        )
        s.commit()
        yield s
        s.query(Item).delete()
        s.query(Category).delete()
        s.commit()


# ── View stubs ────────────────────────────────────────────────────────────────


class _ItemView:
    model = Item


class _CategoryView:
    model = Category


def _ctx(
    field_name: str,
    value: Any = None,
    value2: Any = None,
    view_cls=None,
) -> FilterApplyContext:
    return FilterApplyContext(
        query=None,
        field_name=field_name,
        value=value,
        value2=value2,
        request=None,
        view=(view_cls or _ItemView)(),
    )


# ── Generic: equal / not-equal ────────────────────────────────────────────────


def test_equal_filter(seeded_session):
    clause = EqualFilter().apply(_ctx("name", "Alpha"))
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Alpha"]


def test_not_equal_filter(seeded_session):
    clause = NotEqualFilter().apply(_ctx("name", "Alpha"))
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Beta"]


# ── Generic: null checks on a plain column ────────────────────────────────────


def test_is_null_on_column_matches(seeded_session):
    clause = IsNullFilter().apply(_ctx("category_id"))
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Beta"]


def test_is_not_null_on_column_matches(seeded_session):
    clause = IsNotNullFilter().apply(_ctx("category_id"))
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Alpha"]


# ── Null checks on relationships ──────────────────────────────────────────────


def test_is_null_on_scalar_relationship(seeded_session):
    clause = IsNullFilter().apply(_ctx("category"))
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Beta"]


def test_is_not_null_on_scalar_relationship(seeded_session):
    clause = IsNotNullFilter().apply(_ctx("category"))
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Alpha"]


def test_is_null_on_collection_relationship(seeded_session):
    # Widgets has Alpha, so no category has zero items
    clause = IsNullFilter().apply(_ctx("items", view_cls=_CategoryView))
    rows = seeded_session.execute(select(Category).where(clause)).scalars().all()
    assert rows == []


def test_is_not_null_on_collection_relationship(seeded_session):
    clause = IsNotNullFilter().apply(_ctx("items", view_cls=_CategoryView))
    rows = seeded_session.execute(select(Category).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Widgets"]


# ── String filters ────────────────────────────────────────────────────────────


def test_contains_filter(seeded_session):
    clause = ContainsFilter().apply(_ctx("name", "lph"))
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Alpha"]


def test_not_contains_filter(seeded_session):
    clause = NotContainsFilter().apply(_ctx("name", "lph"))
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Beta"]


def test_starts_with_filter(seeded_session):
    clause = StartsWithFilter().apply(_ctx("name", "Al"))
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Alpha"]


def test_ends_with_filter(seeded_session):
    clause = EndsWithFilter().apply(_ctx("name", "ta"))
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Beta"]


# ── Numeric filters ───────────────────────────────────────────────────────────


def test_numeric_equal_filter(seeded_session):
    clause = NumericEqualFilter().apply(_ctx("count", 10))
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Alpha"]


def test_numeric_not_equal_filter(seeded_session):
    clause = NumericNotEqualFilter().apply(_ctx("count", 10))
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Beta"]


def test_greater_than_filter(seeded_session):
    clause = GreaterThanFilter().apply(_ctx("count", 15))
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Beta"]


def test_less_than_filter(seeded_session):
    clause = LessThanFilter().apply(_ctx("count", 15))
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Alpha"]


def test_greater_than_or_equal_filter(seeded_session):
    # Boundary value equal to Alpha's count (10) is included, unlike ">".
    clause = GreaterThanOrEqualFilter().apply(_ctx("count", 10))
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Alpha", "Beta"]


def test_less_than_or_equal_filter(seeded_session):
    # Boundary value equal to Alpha's count (10) is included, unlike "<".
    clause = LessThanOrEqualFilter().apply(_ctx("count", 10))
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Alpha"]


def test_between_filter(seeded_session):
    clause = BetweenFilter().apply(_ctx("count", 5, 15))
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Alpha"]


# ── Date filters ──────────────────────────────────────────────────────────────


def test_date_equal_filter(seeded_session):
    clause = DateEqualFilter().apply(_ctx("available_on", datetime.date(2024, 3, 1)))
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Alpha"]


def test_datetime_equal_filter(seeded_session):
    clause = DateTimeEqualFilter().apply(
        _ctx("created_at", datetime.datetime(2024, 3, 1, 12, 0))
    )
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Alpha"]


def test_time_equal_filter(seeded_session):
    clause = TimeEqualFilter().apply(_ctx("available_from", datetime.time(8, 0)))
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Alpha"]


def test_date_between_filter(seeded_session):
    clause = DateBetweenFilter().apply(
        _ctx("available_on", datetime.date(2024, 1, 1), datetime.date(2024, 4, 1))
    )
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Alpha"]


def test_datetime_between_filter(seeded_session):
    clause = DateTimeBetweenFilter().apply(
        _ctx(
            "created_at",
            datetime.datetime(2024, 1, 1),
            datetime.datetime(2024, 4, 1),
        )
    )
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Alpha"]


def test_time_between_filter(seeded_session):
    clause = TimeBetweenFilter().apply(
        _ctx("available_from", datetime.time(7, 0), datetime.time(9, 0))
    )
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Alpha"]


def test_datetime_equal_filter_with_timezone_conversion(seeded_session):
    from starlette_admin.i18n import (
        _current_database_timezone,
        _current_timezone,
        _timezone_conversion_enabled,
        set_database_timezone,
        set_timezone,
    )

    original_tz = _current_timezone.get()
    original_db_tz = _current_database_timezone.get()
    original_enabled = _timezone_conversion_enabled.get()
    try:
        set_timezone("America/New_York")
        set_database_timezone("UTC")
        # Alpha.created_at is 2024-03-01 12:00 UTC.
        # 07:00 NYC (UTC-5 in early March) == 12:00 UTC.
        value = DateTimeEqualFilter().parse_value("2024-03-01T07:00:00")
        clause = DateTimeEqualFilter().apply(_ctx("created_at", value))
        rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
        assert [r.name for r in rows] == ["Alpha"]
    finally:
        _current_timezone.set(original_tz)
        _current_database_timezone.set(original_db_tz)
        _timezone_conversion_enabled.set(original_enabled)


def test_datetime_between_filter_with_timezone_conversion(seeded_session):
    from starlette_admin.i18n import (
        _current_database_timezone,
        _current_timezone,
        _timezone_conversion_enabled,
        set_database_timezone,
        set_timezone,
    )

    original_tz = _current_timezone.get()
    original_db_tz = _current_database_timezone.get()
    original_enabled = _timezone_conversion_enabled.get()
    try:
        set_timezone("America/New_York")
        set_database_timezone("UTC")
        # Filter 06:00 to 08:00 NYC -> 11:00 to 13:00 UTC, catches Alpha at 12:00.
        value = DateTimeBetweenFilter().parse_value("2024-03-01T06:00:00")
        value2 = DateTimeBetweenFilter().parse_value("2024-03-01T08:00:00")
        clause = DateTimeBetweenFilter().apply(_ctx("created_at", value, value2))
        rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
        assert [r.name for r in rows] == ["Alpha"]
    finally:
        _current_timezone.set(original_tz)
        _current_database_timezone.set(original_db_tz)
        _timezone_conversion_enabled.set(original_enabled)


def test_date_in_past_filter(seeded_session):
    # Both dates are in the past relative to now
    clause = DateInPastFilter().apply(_ctx("available_on"))
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert len(rows) == 2


def test_date_in_future_filter(seeded_session):
    clause = DateInFutureFilter().apply(_ctx("available_on"))
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert len(rows) == 0


# ── Boolean filters ───────────────────────────────────────────────────────────


def test_is_true_filter(seeded_session):
    clause = IsTrueFilter().apply(_ctx("is_available"))
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Alpha"]


def test_is_false_filter(seeded_session):
    clause = IsFalseFilter().apply(_ctx("is_available"))
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Beta"]


# ── Enum filters ──────────────────────────────────────────────────────────────


def test_in_filter(seeded_session):
    clause = InFilter().apply(_ctx("status", ["active"]))
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Alpha"]


def test_not_in_filter(seeded_session):
    clause = NotInFilter().apply(_ctx("status", ["active"]))
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Beta"]


# ── build_filter_clause (session-backed paths) ────────────────────────────────


def _sqla_registry() -> FilterRegistry:
    registry = FilterRegistry()
    registry.register(StringField, ContainsFilter, EqualFilter)
    registry.register(NumberField, GreaterThanFilter, BetweenFilter)
    return registry


def test_build_filter_clause_single_rule(seeded_session):
    clause = build_filter_clause(
        FilterGroup(
            logic="and",
            rules=[FilterRule(field="name", filter="contains", value="lph")],
        ),
        {"name": StringField("name")},
        _sqla_registry(),
        _ItemView(),
        MagicMock(),
    )
    assert clause is not None
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Alpha"]


def test_build_filter_clause_and_logic(seeded_session):
    clause = build_filter_clause(
        FilterGroup(
            logic="and",
            rules=[
                FilterRule(field="name", filter="contains", value="lph"),
                FilterRule(field="name", filter="contains", value="ph"),
            ],
        ),
        {"name": StringField("name")},
        _sqla_registry(),
        _ItemView(),
        MagicMock(),
    )
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Alpha"]


def test_build_filter_clause_or_logic(seeded_session):
    clause = build_filter_clause(
        FilterGroup(
            logic="or",
            rules=[
                FilterRule(field="name", filter="contains", value="lph"),
                FilterRule(field="name", filter="contains", value="eta"),
            ],
        ),
        {"name": StringField("name")},
        _sqla_registry(),
        _ItemView(),
        MagicMock(),
    )
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert {r.name for r in rows} == {"Alpha", "Beta"}


def test_build_filter_clause_nested_group(seeded_session):
    clause = build_filter_clause(
        FilterGroup(
            logic="and",
            rules=[
                FilterGroup(
                    logic="or",
                    rules=[
                        FilterRule(field="name", filter="contains", value="lph"),
                        FilterRule(field="name", filter="contains", value="eta"),
                    ],
                ),
                FilterRule(field="name", filter="eq", value="Alpha"),
            ],
        ),
        {"name": StringField("name")},
        _sqla_registry(),
        _ItemView(),
        MagicMock(),
    )
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Alpha"]


def test_build_filter_clause_empty_nested_group_skipped(seeded_session):
    """An empty nested FilterGroup is skipped and does not break the parent."""
    clause = build_filter_clause(
        FilterGroup(
            logic="and",
            rules=[
                FilterGroup(logic="or", rules=[]),
                FilterRule(field="name", filter="contains", value="lph"),
            ],
        ),
        {"name": StringField("name")},
        _sqla_registry(),
        _ItemView(),
        MagicMock(),
    )
    assert clause is not None
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Alpha"]


def test_build_rule_clause_normal_path(seeded_session):
    rule = FilterRule(field="name", filter="contains", value="lph")
    clause = _build_rule_clause(
        rule,
        {"name": StringField("name")},
        _sqla_registry(),
        _ItemView(),
        MagicMock(),
    )
    assert clause is not None
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Alpha"]


# ── Custom filter: subclass ───────────────────────────────────────────────────


class DiscountedPriceGreaterThanFilter(GreaterThanFilter):
    """Custom filter that compares a 20%-discounted price against a threshold.

    Demonstrates subclassing a built-in filter to inject domain logic into
    apply() while reusing the inherited parse_value() and name/label metadata.
    """

    name = "discounted_price_gt"
    label = "Discounted price greater than"

    def apply(self, ctx: FilterApplyContext) -> Any:
        from sqlalchemy.orm import InstrumentedAttribute

        col: InstrumentedAttribute = getattr(ctx.view.model, ctx.field_name)
        return col * 0.8 > ctx.value


def test_custom_filter_subclass(seeded_session):
    """DiscountedPriceGreaterThanFilter applies a 20% discount before comparing.

    Alpha: 9.99 * 0.8 = 7.99   → not > 8
    Beta:  19.99 * 0.8 = 15.99 → > 8  ✓
    """
    clause = DiscountedPriceGreaterThanFilter().apply(_ctx("price", 8.0))
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Beta"]


def test_custom_filter_parse_value_inherited():
    """Inherited parse_value() still converts strings to numeric."""
    assert DiscountedPriceGreaterThanFilter().parse_value("8") == 8
    assert isinstance(DiscountedPriceGreaterThanFilter().parse_value("8"), int)


# ── Custom filter: relation field ─────────────────────────────────────────────


class CategoryNameContainsFilter(ContainsFilter):
    """Custom filter that filters Items by their associated Category.name.

    This is the canonical pattern for filtering on a relation field: instead
    of operating on a scalar column, apply() traverses the relationship using
    SQLAlchemy's has() (scalar/many-to-one) or any() (collection/one-to-many)
    and matches on an attribute of the related model.

    Registered against RelationField so the admin can surface it for any
    HasOne / HasMany field backed by a Category relationship.
    """

    name = "category_name_contains"
    label = "Category name contains"

    def apply(self, ctx: FilterApplyContext) -> Any:
        return Item.category.has(Category.name.ilike(f"%{ctx.value}%"))


def test_custom_relation_filter_matches(seeded_session):
    """Filter returns only items whose category name contains the search term."""
    clause = CategoryNameContainsFilter().apply(_ctx("category", "idget"))
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    # Alpha belongs to 'Widgets', Beta has no category
    assert [r.name for r in rows] == ["Alpha"]


def test_custom_relation_filter_no_match(seeded_session):
    """No items match when no category name contains the term."""
    clause = CategoryNameContainsFilter().apply(_ctx("category", "zzz"))
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert rows == []


def test_custom_relation_filter_registered_in_registry(seeded_session):
    """CategoryNameContainsFilter can be wired into a FilterRegistry and
    discovered from a RelationField, then used end-to-end via build_filter_clause.
    """
    custom_registry = FilterRegistry()
    custom_registry.register(StringField, ContainsFilter, EqualFilter)
    custom_registry.register(RelationField, CategoryNameContainsFilter)

    clause = build_filter_clause(
        FilterGroup(
            logic="and",
            rules=[
                FilterRule(
                    field="category",
                    filter="category_name_contains",
                    value="idget",
                )
            ],
        ),
        {"category": RelationField("category")},
        custom_registry,
        _ItemView(),
        MagicMock(),
    )
    assert clause is not None
    rows = seeded_session.execute(select(Item).where(clause)).scalars().all()
    assert [r.name for r in rows] == ["Alpha"]
