import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from common.variables import SERVER_DATABASE


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

    class UserHistory(Base):
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

    def __init__(self, filename=SERVER_DATABASE):
        self.engine = create_engine(filename, echo=False, future=True, pool_recycle=7200)

        self.Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        self.session.query(self.ActiveUser).delete()
        self.session.commit()

    def user_login(self, username, ip_address, port):
        query = self.session.query(self.User).filter_by(username=username)

        if query.count() != 0:
            user = query.first()
            user.last_login = datetime.datetime.now()
        else:
            user = self.User(username)
            self.session.add(user)
            self.session.commit()

        new_active_user = self.ActiveUser(user.id, datetime.datetime.now(), ip_address, port)
        self.session.add(new_active_user)

        history = self.UserHistory(user.id, datetime.datetime.now(), ip_address, port)
        self.session.add(history)

        self.session.commit()

    def user_logout(self, username):
        # get user object that is logging out
        user = self.session.query(self.User).filter_by(username=username).first()

        self.session.query(self.ActiveUser).filter_by(user_id=user.id).delete()

        self.session.commit()

    def get_users(self):
        query = self.session.query(
            self.User.username,
            self.User.last_login,
        )
        return [{'name': el[0], 'last_login': el[1]} for el in query.all()]

    def get_active_users(self):
        query = self.session.query(
            self.User.username,
            self.ActiveUser.login_time,
            self.ActiveUser.ip_address,
            self.ActiveUser.port
        ).join(self.User)

        return [{'name': el[0], 'login_time': el[1], 'ip': el[2], 'port': el[3]} for el in query.all()]

    def get_users_history(self, username=None):
        query = self.session.query(
            self.User.username,
            self.UserHistory.last_login,
            self.UserHistory.ip_address,
            self.UserHistory.port
        ).join(self.User)

        if username:
            query = query.filter(self.User.username == username)

        return [{'name': el[0], 'last_login': el[1], 'ip': el[2], 'port': el[3]} for el in query.all()]

    if __name__ == '__main__':
        db = ServerDB()
        db.user_login('test1', '127.0.0.1', 6000)
        db.user_login('test2', '192.168.1.5', 7777)
        db.user_login('test3', '192.168.1.5', 6001)
        print(db.get_users_history(username='client_3'))
        db.user_logout('test3')
        print(db.get_active_users())
        db.user_logout('test2')
        print(db.get_users_history())
