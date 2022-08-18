import logging

logger = logging.getLogger('server_dist')


class PortDescriptor:

    def __get__(self, instance, owner):
        return instance.__dict__[self.my_attr]

    def __set__(self, instance, value):
        if not 1023 < value < 65536:
            logger.critical(
                f'Given {value} port number. Available addresses: 1024 - 65535.')
            exit(1)
        instance.__dict__[self.my_attr] = value

    def __set_name__(self, owner, my_attr):
        self.my_attr = '_' + my_attr


class SocketDescriptor:
    def __get__(self, instance, owner):
        return instance.__dict__[self.my_attr]

    def __set__(self, instance, value):
        if str(value.family) != 'AddressFamily.AF_INET' or str(value.type) != 'SocketKind.SOCK_STREAM':
            logger.critical('Socket protocol is not TCP')
            exit(1)
        instance.__dict__[self.my_attr] = value

    def __set_name__(self, owner, my_attr):
        self.my_attr = my_attr
