import user as usr
import unittest


class TestUser(unittest.TestCase):

    @unittest.skip("need rewrite")
    def test_is_outside(self):

        mock_config = 0

        inside = usr.User(id=0, pos=150)
        outside = usr.User(id=1, pos=201)

        self.assertEqual(inside.is_outside(mock_config), False)
        self.assertEqual(outside.is_outside(mock_config), True)
