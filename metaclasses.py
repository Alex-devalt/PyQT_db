import dis


class ServerVerifier(type):
    def __init__(cls, class_name, class_parents, class_attrs):
        methods = []  # list of methods inside class functions
        attributes = []  # list of attributes inside class functions
        for attr in class_attrs:
            if callable(class_attrs[attr]):
                print(attr)
                instructions = dis.get_instructions(class_attrs[attr])
                for i in instructions:
                    # opname - operation name
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            methods.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in attributes:
                            attributes.append(i.argval)
        print(methods)
        print(attributes)
        if 'connect' in methods:
            raise TypeError('Use of connect method is not allowed in Server class!')
        # TCP protocol check
        if not ('SOCK_STREAM' in attributes and 'AF_INET' in attributes):
            raise TypeError('Wrong socket initialization!')

        super(ServerVerifier, cls).__init__(class_name,
                                            class_parents,
                                            class_attrs)


class ClientVerifier(type):
    def __init__(cls, class_name, class_parents, class_attrs):
        methods = []  # list of methods inside class functions
        for attr in class_attrs:
            if callable(class_attrs[attr]):
                instructions = dis.get_instructions(class_attrs[attr])
                for i in instructions:

                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            methods.append(i.argval)
        for command in ('accept', 'listen', 'socket'):
            if command in methods:
                raise TypeError('A forbidden method is used in the class!')

        super(ClientVerifier, cls).__init__(class_name,
                                            class_parents,
                                            class_attrs)
