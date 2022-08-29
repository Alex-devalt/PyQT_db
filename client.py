import sys
import json
import socket
import time
import argparse
import logging
import threading
import logs.config_client_log
from common.variables import *
from common.utils import *
from descriptors import SocketDescriptor
from errors import IncorrectDataRecivedError, ReqFieldMissingError, ServerError
from decos import log
from metaclasses import ClientVerifier
from client_db import ClientDatabase

# Logger initialization
logger = logging.getLogger('client_dist')

sock_lock = threading.Lock()
database_lock = threading.Lock()


# A class for creating and sending messages to server and user interaction
class ClientSender(threading.Thread, metaclass=ClientVerifier):
    sock = SocketDescriptor()

    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()

    def create_exit_message(self):
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.account_name
        }

    def create_message(self):
        to = input('Enter message recipient: ')
        message = input('Enter your message: ')

        # Cgeck if user exists
        with database_lock:
            if not self.database.check_user(to):
                logger.error(f'Attempt to send a message to '
                             f'unknown user: {to}')
                return

        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.account_name,
            DESTINATION: to,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        logger.debug(f'Message dict is created: {message_dict}')

        # saving message for message history
        with database_lock:
            self.database.save_message(self.account_name, to, message)

        with sock_lock:
            try:
                send_message(self.sock, message_dict)
                logger.info(f'Message sent to user {to}')
            except OSError as err:
                if err.errno:
                    logger.critical('Connection with the server is lost')
                    exit(1)
                else:
                    logger.error('Unable to send message. Connection timeout.')

    # interacts with the user, asks for instructions and sends messages
    def run(self):
        self.print_help()
        while True:
            command = input('Enter a command: ')
            if command == 'message':
                self.create_message()
            elif command == 'help':
                self.print_help()
            elif command == 'exit':
                with sock_lock:
                    try:
                        send_message(self.sock, self.create_exit_message())
                    except Exception as e:
                        print(e)
                    print('Closing connection.')
                    logger.info('Exiting at user request.')
                # timeout necessary for exit message to be sent
                time.sleep(0.5)
                break

            # contacts list
            elif command == 'contacts':
                with database_lock:
                    contacts_list = self.database.get_contacts()
                for contact in contacts_list:
                    print(contact)

            # edit contacts
            elif command == 'edit':
                self.edit_contacts()

            # messages history
            elif command == 'history':
                self.print_history()

            else:
                print('Команда не распознана, попробойте снова. '
                      'help - вывести поддерживаемые команды.')

    def print_help(self):
        print('Available Commands:')
        print('message - send a message. Enter details later.')
        print('history - messages history')
        print('contacts - contacts list')
        print('edit - edit contacts')
        print('help - print help')
        print('exit - exit program')

    # Функция выводящяя историю сообщений
    def print_history(self):
        ask = input('Показать входящие сообщения - in, исходящие - out, все - просто Enter: ')
        with database_lock:
            if ask == 'in':
                history_list = self.database.get_history(to_who=self.account_name)
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]} '
                          f'от {message[3]}:\n{message[2]}')
            elif ask == 'out':
                history_list = self.database.get_history(from_who=self.account_name)
                for message in history_list:
                    print(f'\nСообщение пользователю: {message[1]} '
                          f'от {message[3]}:\n{message[2]}')
            else:
                history_list = self.database.get_history()
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]},'
                          f' пользователю {message[1]} '
                          f'от {message[3]}\n{message[2]}')

    def edit_contacts(self):
        ans = input('"del" to delete, "add" to add: ')
        if ans == 'del':
            edit = input('Enter username to delete')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    logger.error('Attempt deleting not existing user')
        elif ans == 'add':
            # check if adding such a user is possible
            edit = input('Enter username: ')
            if self.database.check_user(edit):
                with database_lock:
                    self.database.add_contact(edit)
                with sock_lock:
                    try:
                        add_contact(self.sock, self.account_name, edit)
                    except ServerError:
                        logger.error('Unable to send info to the server.')


# Class reads messages and prints them in console
class ClientReader(threading.Thread):
    sock = SocketDescriptor()

    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()

    # Main loop of message receiver, receives messages and prints them out. Breaks out when connection is lost.
    def run(self):
        while True:
            time.sleep(1)
            with sock_lock:
                try:
                    message = get_message(self.sock)

                except IncorrectDataRecivedError:
                    logger.error(f'Unable to decode incoming message.')
                # Connection timed out if errno = None, else - connection broke
                except OSError as err:
                    if err.errno:
                        logger.critical(f'Lost connection to the server.')
                        break
                except (ConnectionError,
                        ConnectionAbortedError,
                        ConnectionResetError,
                        json.JSONDecodeError):
                    logger.critical(f'Unable to connect to the server.')
                    break
                # if message is correct - print it and write to the database
                else:
                    if ACTION in message and message[ACTION] == MESSAGE \
                            and SENDER in message \
                            and DESTINATION in message \
                            and MESSAGE_TEXT in message \
                            and message[DESTINATION] == self.account_name:
                        print(f'\n Got message from user '
                              f'{message[SENDER]}:\n{message[MESSAGE_TEXT]}')
                        # locking database thread and saving message in the db
                        with database_lock:
                            try:
                                self.database.save_message(message[SENDER],
                                                           self.account_name,
                                                           message[MESSAGE_TEXT])
                            except Exception as e:
                                print(e)
                                logger.error('Database error.')

                        logger.info(f'Got message from user '
                                    f'{message[SENDER]}:\n{message[MESSAGE_TEXT]}')
                    else:
                        logger.error(f'Got message from the server: {message}')


@log
def create_presence(account_name):
    out = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }
    logger.debug(f'Created {PRESENCE} message for user {account_name}')
    return out


# Processes server's response on message of presence
@log
def process_response_ans(message):
    logger.debug(f'Разбор приветственного сообщения от сервера: {message}')
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        elif message[RESPONSE] == 400:
            raise ServerError(f'400 : {message[ERROR]}')
    raise ReqFieldMissingError(RESPONSE)


# Command line arguments parser
@log
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name

    if not 1023 < server_port < 65536:
        logger.critical(
            f'Tried to start a client with wrong port address: {server_port}. '
            f'Should be 1024 - 65535. Shutting down the client')
        exit(1)

    return server_address, server_port, client_name


def contacts_list_request(sock, name):
    logger.debug(f'Requesting contacts list for user {name}')
    req = {
        ACTION: GET_CONTACTS,
        TIME: time.time(),
        USER: name
    }
    logger.debug(f'Request is formed {req}')
    send_message(sock, req)
    ans = get_message(sock)
    logger.debug(f'Got answer {ans}')
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[LIST_INFO]
    else:
        raise ServerError


# adding user to contacts list
def add_contact(sock, username, contact):
    logger.debug(f'Adding contact {contact}')
    req = {
        ACTION: ADD_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Error adding contact.')
    print('Contact added.')


def user_list_request(sock, username):
    logger.debug(f'Requesting contacts list for user {username}')
    req = {
        ACTION: USERS_REQUEST,
        TIME: time.time(),
        ACCOUNT_NAME: username
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[LIST_INFO]
    else:
        raise ServerError


def remove_contact(sock, username, contact):
    logger.debug(f'Deleting contact {contact}')
    req = {
        ACTION: REMOVE_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Error deleting client')
    print('Contact deleted.')


# database initializer
# loads data from the server to the database
def database_load(sock, database, username):
    try:
        users_list = user_list_request(sock, username)
    except ServerError:
        logger.error('Error requesting list of known users.')
    else:
        database.add_users(users_list)

    # loading contacts list
    try:
        contacts_list = contacts_list_request(sock, username)
    except ServerError:
        logger.error('Error loading contacts list.')
    else:
        for contact in contacts_list:
            database.add_contact(contact)


def main():
    print('Console manager. Client\'s module')

    # Loading command line params
    server_address, server_port, client_name = arg_parser()

    # If client name not given, asking user for one
    if not client_name:
        client_name = input('Enter username: ')
    else:
        print(f'Client\'s module {client_name} started')

    logger.info(
        f'A client started with params: server address: {server_address} , '
        f'port: {server_port}, username: {client_name}')

    # Socket init and message to the server about new client
    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # timeout is necessary to release socket
        transport.settimeout(1)
        transport.connect((server_address, server_port))
        send_message(transport, create_presence(client_name))
        answer = process_response_ans(get_message(transport))
        logger.info(f'Connection with the server is established. Server answer: {answer}')
        print(f'Connection with the server is established.')
    except json.JSONDecodeError:
        logger.error('Couldn\'t decode Json string.')
        exit(1)
    except ServerError as error:
        logger.error(f'Server returned an error {error.text} trying to connect')
        exit(1)
    except ReqFieldMissingError as missing_error:
        logger.error(f'Missing field in server\'s answer: {missing_error.missing_field}')
        exit(1)
    except (ConnectionRefusedError, ConnectionError):
        logger.critical(
            f'Couldn\'t connect to the server: {server_address}:{server_port}, '
            f'Connection refused.')
        exit(1)
    else:
        # db initialization
        database = ClientDatabase(client_name)
        database_load(transport, database, client_name)

        # Starting sending messages and interacting with the user
        module_sender = ClientSender(client_name, transport, database)
        module_sender.daemon = True
        module_sender.start()
        logger.debug('Starting processes')

        # Starting listening to messages if connection to the server is established
        module_receiver = ClientReader(client_name, transport, database)
        module_receiver.daemon = True
        module_receiver.start()

        # Watchdog main loop, if one of threads is finished - connection is lost or user entered "exit"
        # Breaking out of the loop is enough because all events are handled in threads
        while True:
            time.sleep(1)
            if module_receiver.is_alive() and module_sender.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
