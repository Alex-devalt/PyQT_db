import sys

sys.path.append('../')
from server_db import ServerDB
import unittest


class TestClass(unittest.TestCase):

    def setUp(self):
        self.db = ServerDB('sqlite+pysqlite:///:memory:')

    def test_user_login(self):
        self.db.user_login('name_test', '127.0.0.1', 6000)
        query = self.db.session.query(self.db.User).filter_by(username='name_test')
        query_active = self.db.session.query(self.db.ActiveUser).filter_by(id=1)
        query_history = self.db.session.query(self.db.UserHistory).filter_by(port=6000)

        self.assertEqual('name_test', query.first().username)
        self.assertEqual(1, query_active.first().id)
        self.assertEqual(6000, query_history.first().port)

    def test_user_logout(self):
        self.db.user_login('test', '127.0.0.2', 6010)
        self.db.user_logout('test')
        self.assertEqual(0, self.db.session.query(self.db.ActiveUser).count())


if __name__ == '__main__':
    unittest.main()
