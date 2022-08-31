import sys
import logging
from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QPushButton, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem

sys.path.append('../')

logger = logging.getLogger('client_dist')


# Dialog for selecting a contact to delete
class DelContactDialog(QDialog):
    def __init__(self, database):
        super().__init__()
        self.database = database

        self.setFixedSize(350, 120)
        self.setWindowTitle('Выберите контакт для удаления:')
        # Delete the dialog if the window was closed prematurely
        self.setAttribute(Qt.WA_DeleteOnClose)
        # Making this window modal (i.e. on top of others
        self.setModal(True)

        self.selector_label = QLabel('Выберите контакт для удаления:', self)
        self.selector_label.setFixedSize(200, 20)
        self.selector_label.move(10, 0)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(200, 20)
        self.selector.move(10, 30)
        # contact placeholder to delete
        self.selector.addItems(sorted(self.database.get_contacts()))

        self.btn_ok = QPushButton('Удалить', self)
        self.btn_ok.setFixedSize(100, 30)
        self.btn_ok.move(230, 20)

        self.btn_cancel = QPushButton('Отмена', self)
        self.btn_cancel.setFixedSize(100, 30)
        self.btn_cancel.move(230, 60)
        self.btn_cancel.clicked.connect(self.close)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    from database import ClientDatabase

    database = ClientDatabase('test1')
    window = DelContactDialog(database)
    # when connected, contacts are deleted and then added from the server
    # therefore, to check ourselves, manually add a contact for the deletion list
    database.add_contact('test1')
    database.add_contact('test2')
    database.add_contact('test5')
    database.add_contact('test6')
    print(database.get_contacts())
    window.selector.addItems(sorted(database.get_contacts()))
    window.show()
    app.exec_()
