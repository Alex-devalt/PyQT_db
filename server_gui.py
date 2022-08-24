import sys
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QLabel, QTableView, QDialog, QPushButton, \
    QLineEdit, QFileDialog, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt


# import os


# Creating QModel table for listing all active users
def gui_create_model(database):
    list_users = database.get_active_users()
    list_table = QStandardItemModel()
    list_table.setHorizontalHeaderLabels(['Username', 'IP Address', 'Port', 'Login Time'])
    for row in list_users:
        user, ip, port, time = row
        user = QStandardItem(user)
        user.setEditable(False)
        ip = QStandardItem(ip)
        ip.setEditable(False)
        port = QStandardItem(str(port))
        port.setEditable(False)
        # Cutting milliseconds - don't need them
        time = QStandardItem(str(time.replace(microsecond=0)))
        time.setEditable(False)
        list_table.appendRow([user, ip, port, time])
    return list_table


# Fills messages history table
def create_stat_model(database):
    # list from the database
    hist_list = database.message_history()

    list_table = QStandardItemModel()
    list_table.setHorizontalHeaderLabels(
        ['Username', 'Last Seen', 'Messages sent', 'Messages received'])
    for row in hist_list:
        user, last_seen, sent, received = row
        user = QStandardItem(user)
        user.setEditable(False)
        last_seen = QStandardItem(str(last_seen.replace(microsecond=0)))
        last_seen.setEditable(False)
        sent = QStandardItem(str(sent))
        sent.setEditable(False)
        received = QStandardItem(str(received))
        received.setEditable(False)
        list_table.appendRow([user, last_seen, sent, received])
    return list_table


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Exit button
        self.exitAction = QAction('Exit', self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.triggered.connect(qApp.quit)

        # Refresh client's list button
        self.refresh_button = QAction('Refresh list', self)

        # Messages history button
        self.show_history_button = QAction('Clients history', self)

        # Server settings button
        self.config_btn = QAction('Server Settings', self)

        # dock widget
        self.statusBar()

        self.toolbar = self.addToolBar('MainBar')
        self.toolbar.addAction(self.exitAction)
        self.toolbar.addAction(self.refresh_button)
        self.toolbar.addAction(self.show_history_button)
        self.toolbar.addAction(self.config_btn)

        self.setFixedSize(800, 600)
        self.setWindowTitle('Messaging Server alpha release')

        self.label = QLabel('Connected users:', self)
        self.label.setFixedSize(400, 15)
        self.label.move(10, 35)

        # Table with connected users list
        self.active_clients_table = QTableView(self)
        self.active_clients_table.move(10, 55)
        self.active_clients_table.setFixedSize(780, 400)

        self.show()


class HistoryWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Clients Stats')
        self.setFixedSize(600, 700)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.close_button = QPushButton('Close', self)
        self.close_button.move(250, 650)
        self.close_button.clicked.connect(self.close)

        # Table with history list
        self.history_table = QTableView(self)
        self.history_table.move(10, 10)
        self.history_table.setFixedSize(580, 620)

        self.show()


# Settings window class
class ConfigWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setFixedSize(365, 260)
        self.setWindowTitle('Server Settings')

        self.db_path_label = QLabel('Path to database file: ', self)
        self.db_path_label.move(10, 10)
        self.db_path_label.setFixedSize(240, 15)

        # Line containing path to the database
        self.db_path = QLineEdit(self)
        self.db_path.setFixedSize(250, 20)
        self.db_path.move(10, 30)
        self.db_path.setReadOnly(True)

        # Choose path button
        self.db_path_select = QPushButton('Open...', self)
        self.db_path_select.move(275, 28)

        # Path button event handler
        def open_file_dialog():
            global dialog
            dialog = QFileDialog(self)
            path = dialog.getExistingDirectory()
            path = path.replace('/', '\\')
            self.db_path.insert(path)

        self.db_path_select.clicked.connect(open_file_dialog)

        self.db_file_label = QLabel('Database file name: ', self)
        self.db_file_label.move(10, 68)
        self.db_file_label.setFixedSize(180, 15)

        # Enter file name line
        self.db_file = QLineEdit(self)
        self.db_file.move(200, 66)
        self.db_file.setFixedSize(150, 20)

        self.port_label = QLabel('Port number for connection: ', self)
        self.port_label.move(10, 108)
        self.port_label.setFixedSize(180, 15)

        # Enter port number line
        self.port = QLineEdit(self)
        self.port.move(200, 108)
        self.port.setFixedSize(150, 20)

        self.ip_label = QLabel('Accepting connections from IP: ', self)
        self.ip_label.move(10, 148)
        self.ip_label.setFixedSize(180, 15)

        self.ip_label_note = QLabel('leave empty to\n accept connections from any IP', self)
        self.ip_label_note.move(10, 168)
        self.ip_label_note.setFixedSize(500, 30)

        # Enter ip line
        self.ip = QLineEdit(self)
        self.ip.move(200, 148)
        self.ip.setFixedSize(150, 20)

        self.save_btn = QPushButton('Save', self)
        self.save_btn.move(190, 220)

        # Close window button
        self.close_button = QPushButton('Close', self)
        self.close_button.move(275, 220)
        self.close_button.clicked.connect(self.close)

        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.statusBar().showMessage('Test Statusbar Message')
    test_list = QStandardItemModel(main_window)
    test_list.setHorizontalHeaderLabels(['Username', 'IP Address', 'Port', 'Login Time'])
    test_list.appendRow(
        [QStandardItem('test1'), QStandardItem('192.198.0.5'), QStandardItem('23544'), QStandardItem('16:20:34')])
    test_list.appendRow(
        [QStandardItem('test2'), QStandardItem('192.198.0.8'), QStandardItem('33245'), QStandardItem('16:22:11')])
    main_window.active_clients_table.setModel(test_list)
    main_window.active_clients_table.resizeColumnsToContents()
    app.exec_()
