import unittest

from pydantic import ValidationError

from app.features.auth.schemas import UserCreate


def create_user(username: str) -> UserCreate:
    return UserCreate(
        username=username,
        email="unicode@example.com",
        password="correct-horse-battery-staple",
    )


class UsernameValidationTests(unittest.TestCase):
    def test_accepts_and_normalizes_international_username(self) -> None:
        user = create_user("  Nguye\u0302̃n Minh Anh  ")

        self.assertEqual(user.username, "Nguyễn Minh Anh")
        self.assertEqual(len(user.username), 15)

    def test_accepts_non_latin_names(self) -> None:
        for username in ("李小龍", "أحمد محمود", "अनन्या शर्मा", "김민준"):
            with self.subTest(username=username):
                self.assertEqual(create_user(username).username, username)

    def test_rejects_blank_and_short_username(self) -> None:
        for username in ("   ", "李小"):
            with self.subTest(username=username):
                with self.assertRaises(ValidationError):
                    create_user(username)

    def test_rejects_username_longer_than_fifty_unicode_characters(self) -> None:
        with self.assertRaises(ValidationError):
            create_user("界" * 51)

    def test_rejects_control_characters(self) -> None:
        with self.assertRaises(ValidationError):
            create_user("Valid\nName")
if __name__ == "__main__":
    unittest.main()
