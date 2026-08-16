from tortoise import Tortoise


def mysql_tortoise_url(container) -> str:
    """Build a Tortoise-compatible db_url from a MySqlContainer."""
    host = container.get_container_host_ip()
    port = container.get_exposed_port(container.port)
    return f"mysql://{container.username}:{container.password}@{host}:{port}/{container.dbname}"


def postgres_tortoise_url(container) -> str:
    """Build a Tortoise-compatible db_url from a PostgresContainer."""
    host = container.get_container_host_ip()
    port = container.get_exposed_port(container.port)
    return (
        f"asyncpg://{container.username}:{container.password}@{host}:{port}"
        f"/{container.dbname}"
    )


async def tortoise_init(backend: str, db_url: str, models_module: str) -> None:
    """Init Tortoise with a connection named after the backend.

    Tortoise caches each model's generated insert/update SQL under a key of
    (connection_name, schema, table). The default db_url= shortcut always
    names the connection "default", so running the same model classes against
    sqlite, then MySQL, then PostgreSQL in one test process reuses the first
    backend's cached SQL (wrong placeholder style) for the other two. Naming
    the connection after the backend keeps the cache keys distinct.
    """
    await Tortoise.init(
        config={
            "connections": {backend: db_url},
            "apps": {
                "models": {"models": [models_module], "default_connection": backend}
            },
        }
    )


async def reset_schema(backend: str) -> None:
    """Wipe every table created by the test so the shared container is clean
    for the next test. SQLite runs in-memory and is discarded on close, so
    only MySQL and PostgreSQL (persistent containers) need this."""
    if backend == "sqlite":
        return
    conn = Tortoise.get_connection(backend)
    if backend == "postgres":
        await conn.execute_script("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    elif backend == "mysql":
        rows = await conn.execute_query_dict(
            "SELECT table_name AS tbl FROM information_schema.tables"
            " WHERE table_schema = DATABASE()"
        )
        if rows:
            tables = ", ".join(f"`{row['tbl']}`" for row in rows)
            # One script on one connection: dropping DROP/SET separately can pull
            # different pooled connections, so FOREIGN_KEY_CHECKS=0 would not be
            # in effect for the DROP and a FK-ordered drop can corrupt the
            # connection's protocol state for the rest of the session.
            await conn.execute_script(
                f"SET FOREIGN_KEY_CHECKS=0; DROP TABLE {tables}; SET FOREIGN_KEY_CHECKS=1;"
            )
