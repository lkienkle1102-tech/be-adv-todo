import unittest

from app.core.db import engine, get_asyncpg_url


class GetAsyncpgUrlTests(unittest.TestCase):
    def test_converts_sslmode_to_asyncpg_ssl_option(self) -> None:
        url = get_asyncpg_url(
            "postgresql+asyncpg://user:password@localhost/todo"
            "?sslmode=require&application_name=adv-todo"
        )

        self.assertEqual(url.query["ssl"], "require")
        self.assertEqual(url.query["application_name"], "adv-todo")
        self.assertNotIn("sslmode", url.query)

        _, connect_args = engine.dialect.create_connect_args(url)
        self.assertEqual(connect_args["ssl"], "require")
        self.assertNotIn("sslmode", connect_args)

    def test_keeps_url_without_sslmode_unchanged(self) -> None:
        database_url = "postgresql+asyncpg://user:password@localhost/todo"

        url = get_asyncpg_url(database_url)

        self.assertEqual(url.render_as_string(hide_password=False), database_url)

    def test_prefers_explicit_asyncpg_ssl_option(self) -> None:
        url = get_asyncpg_url(
            "postgresql+asyncpg://user:password@localhost/todo"
            "?ssl=verify-full&sslmode=require"
        )

        self.assertEqual(url.query["ssl"], "verify-full")
        self.assertNotIn("sslmode", url.query)


if __name__ == "__main__":
    unittest.main()
