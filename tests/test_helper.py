import context  # noqa: F401, isort:skip

import os
import unittest

from dups import helper, user


class Test_helper(unittest.TestCase):
    def test_escape_pattern(self):
        paths = [
            (
                # Ensure whitelist
                r'aA01,._+@%/\-*\\{}',
                r'aA01,._+@%/\-*\\{}',
            ),
            (
                # Ensure unicode escape
                r'¢©«»°±·×',
                r'\¢\©\«\»\°\±\·\×',
            ),
            (
                # Pattern with special chars
                r'test \* folder/*',
                r'test\ \*\ folder/*',
            ),
        ]

        for pattern, expected in paths:
            with self.subTest(pattern=pattern, expected=expected):
                self.assertEqual(expected, helper.escape_pattern(pattern))


if __name__ == '__main__':
    unittest.main(exit=False)
