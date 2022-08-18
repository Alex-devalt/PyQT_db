# -*- coding: utf-8 -*-
import sys
import json
import socket
import time
import dis
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

# Logger initialization
logger = logging.getLogger('client_dist')


# A class for creating and sending messages to server and user interaction
class ClientSender(threading.Thread, metaclass=ClientVerifier):
    sock = SocketDescriptor()

    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
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
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.account_name,
            DESTINATION: to,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        logger.debug(f'Message dict is created: {message_dict}')
        try:
            send_message(self.sock, message_dict)
            logger.info(f'Message sent to user {to}')
        except:
            logger.critical('Connection with the server is lost')
            exit(1)

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
                try:
                    send_message(self.sock, self.create_exit_message())
                except:
                    pass
                print('Closing connection...')
                logger.info('Shutting down on user\'s request.')
                # Delay's necessary for message to be sent
                time.sleep(0.5)
                break
            else:
                print('Unknown command, try again. help - to list available commands')

    def print_help(self):
        print('Available Commands:')
        print('message - send a message. Enter details later.')
        print('help - self explanatory')
        print('exit - self explanatory')


# Class reads messages and prints them in console
class ClientReader(threading.Thread):
    sock = SocketDescriptor()

    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()

    # Main loop of message receiver, receives messages and prints them out. Breaks out when connection is lost.
    def run(self):
        while True:
            try:
                message = get_message(self.sock)
                if ACTION in message and message[ACTION] == MESSAGE and SENDER in message and DESTINATION in message \
                        and MESSAGE_TEXT in message and message[DESTINATION] == self.account_name:
                    print(f'\nGot message from {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
                    logger.info(f'Got message from {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
                else:
                    logger.error(f'Wrong message format from the server - {message}')
            except IncorrectDataRecivedError:
                logger.error(f'Couldn\'t decode received message!')
            except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                logger.critical(f'Connection with the server is lost!')
                break


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


def main():
    print('Console manager. Client\'s module')

    server_address, server_port, client_name = arg_parser()

    if not client_name:
        client_name = input('Enter username: ')
    else:
        print(f'Client\'s module {client_name} started')

    logger.info(
        f'A client started with params: server address: {server_address} , '
        f'port: {server_port}, username: {client_name}')

    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
        # Starting listening to messages if connection to the server is established
        module_receiver = ClientReader(client_name, transport)
        module_receiver.daemon = True
        module_receiver.start()

        # Starting sending messages and interacting with the user
        module_sender = ClientSender(client_name, transport)
        module_sender.daemon = True
        module_sender.start()
        logger.debug('Starting processes')

        # Watchdog main loop, if one of threads is finished - connection is lost or user entered "exit"
        # Breaking out of the loop is enough because all events are handled in threads
        while True:
            time.sleep(1)
            if module_receiver.is_alive() and module_sender.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
