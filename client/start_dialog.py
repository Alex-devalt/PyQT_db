from PyQt5.QtWidgets import QDialog, QPushButton, QLineEdit, QApplication, QLabel, qApp
from PyQt5.QtCore import QEvent


# Start dialog with username selection
class UserNameDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.ok_pressed = False

        self.setWindowTitle('Hello Friend!')
        self.setFixedSize(300, 100)

        self.label = QLabel('Enter username:', self)
        self.label.move(105, 10)
        self.label.setFixedSize(250, 10)

        self.client_name = QLineEdit(self)
        self.client_name.setFixedSize(150, 20)
        self.client_name.move(70, 30)

        self.btn_ok = QPushButton('Start', self)
        self.btn_ok.move(64, 60)
        self.btn_ok.clicked.connect(self.click)

        self.btn_cancel = QPushButton('Exit', self)
        self.btn_cancel.move(153, 60)
        self.btn_cancel.clicked.connect(qApp.exit)

        self.show()

    # OK button handler, if the input field is not empty, set the flag and exit the application
    def click(self):
        if self.client_name.text():
            self.ok_pressed = True
            qApp.exit()


if __name__ == '__main__':
    app = QApplication([])
    dial = UserNameDialog()
    app.exec_()
