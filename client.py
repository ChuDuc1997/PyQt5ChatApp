from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import clientUi
import connectUi
import socket
import sys

HOST = "localhost"
PORT = 5555

class ReceiveThread(QThread):
    signal = pyqtSignal(str)

    def __init__(self, clientSocket):
        super(ReceiveThread, self).__init__()
        self.clientSocket = clientSocket

    def run(self):
        while True:
            try:
                self.receiveMessage()
            except:
                break

    def receiveMessage(self):
        data = self.clientSocket.recv(1024)
        message = data.decode("utf8")
        self.signal.emit(message)

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(QRect(600, 100, 800, 600))
        self.setWindowTitle("Chat App")
        self.connectWindow = QWidget(self)
        self.clientWindow = QWidget(self)

        self.clientUi = clientUi.Ui_Form()
        self.clientUi.setupUi(self.clientWindow)
        self.clientUi.sendButton.clicked.connect(self.sendMessage)
        self.clientWindow.setHidden(True)

        self.connectUi = connectUi.Ui_Form()
        self.connectUi.setupUi(self.connectWindow)
        self.connectUi.connectButton.clicked.connect(self.connectClick)
        self.soket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connectClick(self):
        host = self.connectUi.hostnameLine.text()
        port = self.connectUi.portLine.text()
        user = self.connectUi.usernameLine.text()

        if len(host) == 0:
            host = HOST
        if len(port) == 0:
            port = PORT
        else:
            try:
                port = int(port)
            except Exception as e:
                error = f"Invalid port number '{str(e)}'"
                self.showError("Port Number Error", error)
        
        if self.connect(user, host, port):
            self.connectWindow.setHidden(True)
            self.clientWindow.setVisible(True)
            self.receiveThread = ReceiveThread(self.soket)
            self.receiveThread.signal.connect(self.showMessage)
            self.receiveThread.start()

    def showMessage(self, message):
        self.clientUi.messageText.append(message)

    def connect(self, username, host = HOST, port = PORT):
        try:
            self.soket.connect((host, port))
            self.soket.send(bytes(username, 'utf8'))
            return True
        except Exception as e:
            error = f"Unable to connect to server '{str(e)}'"
            self.showError("Connection Error", error)
            self.connectUi.hostnameLine.clear()
            self.connectUi.portLine.clear()
            return False

    def sendMessage(self):
        message = self.clientUi.messageLine.text()
        if message:
            self.clientUi.messageText.append(f'<p dir="rtl"><b>Me:</b> {message}</p>')
            try:
                self.soket.send(bytes(message, 'utf8'))
            except Exception as e:
                error = f"Unable to send message '{str(e)}'"
                self.showError("Server Error", error)
            self.clientUi.messageLine.clear()

    def showError(self, errorType, message):
        errorDialog = QMessageBox()
        errorDialog.setText(message)
        errorDialog.setWindowTitle(errorType)
        errorDialog.setStandardButtons(QMessageBox.Ok)
        errorDialog.exec_()

    def closeEvent(self, event):
        if self.clientWindow.isVisible():
            message = f'disconnec'
            try:
                self.soket.send(bytes(message, 'utf8'))
            except Exception as e:
                error = f"Unable to send message '{str(e)}'"
                self.showError("Server Error", error)
            self.receiveThread.quit()
            self.soket.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())