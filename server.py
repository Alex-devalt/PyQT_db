import socket
import sys
import argparse
import json
import logging
import select
import time
import logs.config_server_log
from descriptors import PortDescriptor
from metaclasses import ServerVerifier
from errors import IncorrectDataRecivedError
from common.variables import *
from common.utils import *
from decos import log

# Server logger initialization
logger = logging.getLogger('server_dist')


# Command line args parser
@log
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    return listen_address, listen_port


class Server(metaclass=ServerVerifier):
    port = PortDescriptor()

    def __init__(self, listen_address, listen_port):
        # Connection parameters
        self.addr = listen_address
        self.port = listen_port

        # Connected clients list
        self.clients = []

        # List of messages to send
        self.messages = []

        # Dict of names and corresponding sockets
        self.names = dict()

    def init_socket(self):
        # logger.info(
        #     f'Start server, port for connections: {self.port},  address to connect to: {self.addr}. If address not '
        #     f'specified- connections from any address are allowed')
        # Getting socket ready
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((self.addr, self.port))
        transport.settimeout(0.5)

        # Start listening to socket
        self.sock = transport
        self.sock.listen()

    def main_loop(self):

        self.init_socket()

        # main loop
        while True:
            # Waiting for connection, if timeout is out - raising exception
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                # logger.info(f'Connection established with {client_address}')
                logger.info(f' ')
                self.clients.append(client)

            recv_data_lst = []
            send_data_lst = []
            err_lst = []
            # Check for waiting clients
            try:
                if self.clients:
                    recv_data_lst, send_data_lst, err_lst = select.select(self.clients, self.clients, [], 0)
            except OSError:
                pass

            # receiving messages, if an error - excluding client from list
            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.process_client_message(get_message(client_with_message), client_with_message)
                    except:
                        logger.info(f'Client {client_with_message.getpeername()} disconnected from server')
                        self.clients.remove(client_with_message)

            # If messages - processing them
            for message in self.messages:
                try:
                    self.process_message(message, send_data_lst)
                except Exception as e:
                    logger.info(f'Connection with client '
                                f'{message[DESTINATION]} was lost, '
                                f' error {e}')
                    self.clients.remove(self.names[message[DESTINATION]])
                    del self.names[message[DESTINATION]]
            self.messages.clear()

    # Func sending message to a specific client
    # Accepts message as dict, list of registered users and listening sockets
    def process_message(self, message, listen_socks):
        if message[DESTINATION] in self.names and \
                self.names[message[DESTINATION]] in listen_socks:
            send_message(self.names[message[DESTINATION]], message)
            logger.info(f'A message sent to user {message[DESTINATION]} '
                        f'from user {message[SENDER]}.')
        elif message[DESTINATION] in self.names \
                and self.names[message[DESTINATION]] not in listen_socks:
            raise ConnectionError
        else:
            logger.error(
                f'User {message[DESTINATION]} is not registered '
                f'Can not send message.')

    # Checks if incoming message is correctly formatted and
    # sends dict response if needed
    def process_client_message(self, message, client):
        logger.debug(f'Processing message from client : {message}')
        # If a PRESENSE message - accept and respond
        if ACTION in message and message[ACTION] == PRESENCE \
                and TIME in message and USER in message:
            # Register user if new
            # Otherwise send the response and close the connection
            if message[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[message[USER][ACCOUNT_NAME]] = client
                send_message(client, RESPONSE_200)
            else:
                response = RESPONSE_400
                response[ERROR] = 'User with this name already exists.'
                send_message(client, response)
                self.clients.remove(client)
                client.close()
            return
        # If a message - add it to message queue, no response needed
        elif ACTION in message \
                and message[ACTION] == MESSAGE \
                and DESTINATION in message \
                and TIME in message \
                and SENDER in message \
                and MESSAGE_TEXT in message:
            self.messages.append(message)
            return
        # If a client exits
        elif ACTION in message \
                and message[ACTION] == EXIT \
                and ACCOUNT_NAME in message:
            self.clients.remove(self.names[ACCOUNT_NAME])
            self.names[ACCOUNT_NAME].close()
            del self.names[ACCOUNT_NAME]
            return
        # Otherwise return Bad request
        else:
            response = RESPONSE_400
            response[ERROR] = 'Bad request.'
            send_message(client, response)
            return


def main():
    # Parsing command line args, if not provided - use default.
    listen_address, listen_port = arg_parser()

    server = Server(listen_address, listen_port)
    server.main_loop()


if __name__ == '__main__':
    main()
