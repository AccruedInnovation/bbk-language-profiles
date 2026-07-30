from unittest import TestCase

from fixture_pkg import greet


class GreetingTests(TestCase):
    def test_greet(self) -> None:
        self.assertEqual(greet("Ada").message, "Hello, Ada!")
