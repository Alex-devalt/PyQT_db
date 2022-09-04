Client module documentation
=================================================

Messaging client application. Supports sending messages to users who are online,
messages are encrypted using the RSA algorithm with a key length of 2048 bit.
Supports command line arguments:

``python client.py {server name} {port} -n or --name {username} -p or -password {password }``

1. {server name} - message server address.
2. {port} - port on which connections are accepted.
3. -n or --name - the username with which the system will be logged in.
4. -p or --password - user password.

All command line options are optional, but the username and password must be used in pairs.

Examples of using:

* ``python client.py``

*Launch the app with default settings.*

* ``python client.py ip_address some_port``

*Launching the application with instructions to connect to the server at ip_address:port*

* ``python -n test1 -p 123``

*Run application with user test1 and password 123*

* ``python client.py ip_address some_port -n test1 -p 123``

*Launching the application with the user test1 and password 123 and specifying to connect to the server at ip_address:port*

client.py
~~~~~~~~~

A executable module that contains a command line argument parser and application initialization functionality.

client. **arg_parser** ()
    Command line argument parser, returns a tuple of 4 elements:

	* server address
	* port
	* username
	* password

    Performs validation of the port number.


database.py
~~~~~~~~~~~~~~

.. autoclass:: client.database.ClientDatabase
	:members:

transport.py
~~~~~~~~~~~~~~

.. autoclass:: client.transport.ClientTransport
	:members:

main_window.py
~~~~~~~~~~~~~~

.. autoclass:: client.main_window.ClientMainWindow
	:members:

start_dialog.py
~~~~~~~~~~~~~~~

.. autoclass:: client.start_dialog.UserNameDialog
	:members:


add_contact.py
~~~~~~~~~~~~~~

.. autoclass:: client.add_contact.AddContactDialog
	:members:


del_contact.py
~~~~~~~~~~~~~~

.. autoclass:: client.del_contact.DelContactDialog
	:members:
