import logging

DEFAULT_PORT = 7000
# default ip address for client connection
DEFAULT_IP_ADDRESS = '127.0.0.1'
MAX_CONNECTIONS = 5
MAX_PACKAGE_LENGTH = 1024
ENCODING = 'utf-8'
LOGGING_LEVEL = logging.DEBUG
# Server database
SERVER_DATABASE = 'sqlite+pysqlite:///_server_db.db3'

# JIM protocol, main keys:
ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account_name'
SENDER = 'from'
DESTINATION = 'to'

# other keys:
PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'
MESSAGE = 'message'
MESSAGE_TEXT = 'mess_text'
EXIT = 'exit'
GET_CONTACTS = 'get_contacts'
LIST_INFO = 'data_list'
REMOVE_CONTACT = 'remove'
ADD_CONTACT = 'add'
USERS_REQUEST = 'get_users'

# Response dicts:
RESPONSE_200 = {RESPONSE: 200}
RESPONSE_202 = {RESPONSE: 202,
                LIST_INFO: None
                }
RESPONSE_400 = {
    RESPONSE: 400,
    ERROR: None
}
