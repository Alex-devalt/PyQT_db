from pprint import pprint

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from common.variables import SERVER_DATABASE
import datetime


class ServerDB:
    Base = declarative_base()


class ServerDB:
    Base = declarative_base()

    class User(Base):
        __tablename__ = 'users'
        id = Column(Integer, primary_key=True)
        username = Column(String)
        last_login = Column(DateTime)

        def __init__(self, username):
            self.username = username
            self.last_login = datetime.datetime.now()

        def __repr__(self):
            return f'User {self.username}'

    class ActiveUser(Base):
        __tablename__ = 'active_users'
        id = Column(Integer, primary_key=True)
        user_id = Column(ForeignKey('users.id'))
        login_time = Column(DateTime)
        ip_address = Column(String)
        port = Column(Integer)

        def __init__(self, user_id, login_time, ip_address, port):
            self.user_id = user_id
            self.login_time = login_time
            self.ip_address = ip_address
            self.port = port

    class LoginHistory(Base):
        __tablename__ = 'user_history'
        id = Column(Integer, primary_key=True)
        user_id = Column(ForeignKey('users.id'))
        last_login = Column(DateTime)
        ip_address = Column(String)
        port = Column(Integer)

        def __init__(self, user_id, last_login, ip_address, port):
            self.user_id = user_id
            self.last_login = last_login
            self.ip_address = ip_address
            self.port = port

    class UsersContacts(Base):
        __tablename__ = 'users_contacts'
        id = Column(Integer, primary_key=True)
        user = Column(ForeignKey('users.id'))
        contact = Column('contact', ForeignKey('users.id'))

        def __init__(self, user, contact):
            self.id = None
            self.user = user
            self.contact = contact

    class UsersHistory(Base):
        __tablename__ = 'users_history'
        id = Column(Integer, primary_key=True)
        user = Column(ForeignKey('users.id'))
        sent = Column('sent', Integer)
        accepted = Column('accepted', Integer)

        def __init__(self, user):
            self.id = None
            self.user = user
            self.sent = 0
            self.accepted = 0

    def __init__(self, path):
        self.engine = create_engine(f'sqlite:///{path}', echo=False, pool_recycle=7200,
                                    connect_args={'check_same_thread': False})

        self.Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        # clearing active_users table every session
        self.session.query(self.ActiveUser).delete()
        self.session.commit()

    def user_login(self, username, ip_address, port):
        query = self.session.query(self.User).filter_by(username=username)

        if query.count() != 0:  # if user already in db
            user = query.first()
            user.last_login = datetime.datetime.now()
        else:  # if new user
            user = self.User(username)
            self.session.add(user)
            self.session.commit()
            user_in_history = self.UsersHistory(user.id)
            self.session.add(user_in_history)
        # adding user to active_users
        new_active_user = self.ActiveUser(user.id, datetime.datetime.now(), ip_address, port)
        self.session.add(new_active_user)
        # changing user_history
        history = self.LoginHistory(user.id, datetime.datetime.now(), ip_address, port)
        self.session.add(history)

        self.session.commit()

    def user_logout(self, username):
        # get user object that is logging out
        user = self.session.query(self.User).filter_by(username=username).first()

        # del the user from active_users table
        self.session.query(self.ActiveUser).filter_by(user_id=user.id).delete()

        self.session.commit()

    # changing count of sent and received messages
    def process_message(self, sender, recipient):
        sender = self.session.query(self.User).filter_by(username=sender).first().id
        recipient = self.session.query(self.User).filter_by(username=recipient).first().id
        sender_row = self.session.query(self.UsersHistory).filter_by(user=sender).first()
        sender_row.sent += 1
        recipient_row = self.session.query(self.UsersHistory).filter_by(user=recipient).first()
        recipient_row.accepted += 1

        self.session.commit()

    def add_contact(self, user, contact):
        user = self.session.query(self.User).filter_by(username=user).first()
        contact = self.session.query(self.User).filter_by(username=contact).first()

        if not contact or self.session.query(self.UsersContacts).filter_by(user=user.id, contact=contact.id).count():
            return

        contact_row = self.UsersContacts(user.id, contact.id)
        self.session.add(contact_row)
        self.session.commit()

    def remove_contact(self, user, contact):
        user = self.session.query(self.User).filter_by(username=user).first()
        contact = self.session.query(self.User).filter_by(username=contact).first()

        if not contact:
            return

        self.session.query(self.UsersContacts).filter(
            self.UsersContacts.user == user.id,
            self.UsersContacts.contact == contact.id
        ).delete()
        self.session.commit()

    def get_users(self):
        query = self.session.query(
            self.User.username,
            self.User.last_login,
        )
        return query.all()

    def get_active_users(self):
        query = self.session.query(
            self.User.username,
            self.ActiveUser.ip_address,
            self.ActiveUser.port,
            self.ActiveUser.login_time
        ).join(self.User)

        return query.all()

    def get_users_history(self, username=None):
        query = self.session.query(
            self.User.username,
            self.LoginHistory.last_login,
            self.LoginHistory.ip_address,
            self.LoginHistory.port
        ).join(self.User)

        if username:
            query = query.filter(self.User.username == username)

        return query.all()

    def get_contacts(self, username):
        user = self.session.query(self.User).filter_by(username=username).one()

        query = self.session.query(self.UsersContacts, self.User.username). \
            filter_by(user=user.id). \
            join(self.User, self.UsersContacts.contact == self.User.id)

        # return usernames only
        return [contact[1] for contact in query.all()]

    def message_history(self):
        query = self.session.query(
            self.User.username,
            self.User.last_login,
            self.UsersHistory.sent,
            self.UsersHistory.accepted
        ).join(self.User)
        return query.all()

    if __name__ == '__main__':
        # db = ServerDB()
        # db.user_login('test1', '127.0.0.1', 6000)
        # db.user_login('test2', '192.168.1.5', 7777)
        # db.user_login('test3', '192.168.1.5', 6001)
        # print(db.get_users_history(username='client_3'))
        # db.user_logout('test3')
        # print(db.get_active_users())
        # db.user_logout('test2')
        # print(db.get_users_history())

        test_db = ServerDB('_server_db.db3')
        test_db.user_login('1111', '192.168.1.113', 8080)
        test_db.user_login('McG2', '192.168.1.113', 8081)
        pprint(test_db.get_users())
        pprint(test_db.get_active_users())
        test_db.user_logout('McG2')
        pprint(test_db.get_users_history('re'))
        test_db.add_contact('test2', 'test1')
        test_db.add_contact('test1', 'test3')
        test_db.add_contact('test1', 'test6')
        test_db.remove_contact('test1', 'test3')
        test_db.process_message('McG2', '1111')
        pprint(test_db.message_history())
