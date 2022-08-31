from sqlalchemy import create_engine, Table, Column, Integer, String, Text, MetaData, DateTime
from sqlalchemy.orm import mapper, sessionmaker
import os
import sys

sys.path.append('..')
from common.variables import *
import datetime


# Class - server database
class ClientDatabase:
    # Class - displaying a table of known users.
    class KnownUsers:
        def __init__(self, user):
            self.id = None
            self.username = user

    # Class - displaying the message history table
    class MessageHistory:
        def __init__(self, contact, direction, message):
            self.id = None
            self.contact = contact
            self.direction = direction
            self.message = message
            self.date = datetime.datetime.now()

    # Class - displaying a list of contacts
    class Contacts:
        def __init__(self, contact):
            self.id = None
            self.name = contact

    # Class constructor:
    def __init__(self, name):
        # We create a database engine, since multiple clients are allowed at the same time,
        # then everyone should have their own database.
        # Since the client is multi-threaded,
        # then you need to disable checks for connections from different streams,
        # other sqlite3.ProgrammingError
        path = os.path.dirname(os.path.realpath(__file__))
        filename = f'client_{name}.db3'
        self.database_engine = create_engine(f'sqlite:///{os.path.join(path, filename)}',
                                             echo=False,
                                             pool_recycle=7200,
                                             connect_args={'check_same_thread': False})

        # Create a MetaData object
        self.metadata = MetaData()

        # Create a table of known users
        users = Table('known_users', self.metadata,
                      Column('id', Integer, primary_key=True),
                      Column('username', String)
                      )

        # Create a message history table
        history = Table('message_history', self.metadata,
                        Column('id', Integer, primary_key=True),
                        Column('contact', String),
                        Column('direction', String),
                        Column('message', Text),
                        Column('date', DateTime)
                        )

        # Create a contact table
        contacts = Table('contacts', self.metadata,
                         Column('id', Integer, primary_key=True),
                         Column('name', String, unique=True)
                         )

        # Create tables
        self.metadata.create_all(self.database_engine)

        # Creating Displays
        mapper(self.KnownUsers, users)
        mapper(self.MessageHistory, history)
        mapper(self.Contacts, contacts)

        # Create a session
        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

        # It is necessary to clear the contact table, because at startup, they are loaded from the server.
        self.session.query(self.Contacts).delete()
        self.session.commit()

    # Add contacts function
    def add_contact(self, contact):
        if not self.session.query(self.Contacts).filter_by(name=contact).count():
            contact_row = self.Contacts(contact)
            self.session.add(contact_row)
            self.session.commit()

    # Delete contact function
    def del_contact(self, contact):
        self.session.query(self.Contacts).filter_by(name=contact).delete()
        self.session.commit()

    # Feature to add known users.
    # Users are obtained only from the server, so the table is cleared.
    def add_users(self, users_list):
        self.session.query(self.KnownUsers).delete()
        for user in users_list:
            user_row = self.KnownUsers(user)
            self.session.add(user_row)
        self.session.commit()

    # Function that saves messages
    def save_message(self, contact, direction, message):
        message_row = self.MessageHistory(contact, direction, message)
        self.session.add(message_row)
        self.session.commit()

    # A function that returns contacts
    def get_contacts(self):
        return [contact[0] for contact in self.session.query(self.Contacts.name).all()]

    # A function that returns a list of known users
    def get_users(self):
        return [user[0] for user in self.session.query(self.KnownUsers.username).all()]

    # A function that checks for the presence of a user in known
    def check_user(self, user):
        if self.session.query(self.KnownUsers).filter_by(username=user).count():
            return True
        else:
            return False

    # A function that checks if the user has contacts
    def check_contact(self, contact):
        if self.session.query(self.Contacts).filter_by(name=contact).count():
            return True
        else:
            return False

    # Function that returns the history of correspondence
    def get_history(self, contact):
        query = self.session.query(self.MessageHistory).filter_by(contact=contact)
        return [(history_row.contact, history_row.direction,
                 history_row.message, history_row.date)
                for history_row in query.all()]


# debugging
if __name__ == '__main__':
    test_db = ClientDatabase('test1')
    for i in ['test3', 'test4', 'test5']:
        test_db.add_contact(i)
    test_db.add_contact('test4')
    test_db.add_users(['test1', 'test2', 'test3', 'test4', 'test5'])
    test_db.save_message('test2', 'in',
                         f'Привет! я тестовое сообщение от {datetime.datetime.now()}!')
    test_db.save_message('test2', 'out',
                         f'Привет! я другое тестовое сообщение от {datetime.datetime.now()}!')
    print(test_db.get_contacts())
    print(test_db.get_users())
    print(test_db.check_user('test1'))
    print(test_db.check_user('test10'))
    print(sorted(test_db.get_history('test2'), key=lambda item: item[3]))
    test_db.del_contact('test4')
    print(test_db.get_contacts())
