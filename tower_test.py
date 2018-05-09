import unittest
from tower import Tower
import user as usr


class TestTower(unittest.TestCase):

    @unittest.skip("incomplete test")
    def test_connect(self):
        tower = Tower(50, 57, 30, 1000)
        user = usr.User(1)
        tower.connect(user)

        self.assertEqual(tower.num_users(), 1)
        print(tower.users)
        self.assertTrue(tower.users[id])
