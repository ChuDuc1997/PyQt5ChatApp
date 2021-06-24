import mysql.connector
import threading
import socket
import signal
import sys

HOST = "localhost"
PORT = 5555

class Database(object):
    def __init__(self):
        self.mydb = mysql.connector.connect(
            host="localhost", 
            user="yourusername", 
            password="yourpassword",
            database="mydatabase"
        )
        self.mycursor = self.mydb.cursor()
        self.mycursor.execute("DROP TABLE IF EXISTS messages")
        self.mycursor.execute("CREATE TABLE messages (username VARCHAR(255), message VARCHAR(1023))")

    def execute(self, sql, val):
        self.mycursor.execute(sql, val)
        

class Server(object):
    clients = {}
    cursors = {}

    def __init__(self, host = HOST, port = PORT):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.database = Database()
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen()
        print(f"Server runing on {host} : {port}")
        self.running()

    def running(self):
        signal.signal(signal.SIGINT, self.signalHandler)

        while True:
            conn, addr = self.server.accept()
            username = conn.recv(1024)
            username = username.decode('utf8')

            self.clients[username] = conn
            self.cursors[username] = self.database.mydb.cursor()

            self.loadMessages(username)
            self.sendJoinStatus(username)

            threading.Thread(target=self.receiveMessage, args=(conn, username), daemon=True).start()

            print(f"Connecting from {addr[0]} : {addr[1]} : {username}")

    def signalHandler(self, signal, frame):
        print()
        sys.exit(0)

    def loadMessages(self, username):
        self.cursors[username].execute("SELECT * FROM messages")
        data = self.database.mycursor.fetchall()
        if data:
            for item in data:
                msg = f'<p dir="ltr"><b>{item[0]}:</b> {item[1]}</p>'
                self.clients[username].send(bytes(msg, 'utf8'))


    def receiveMessage(self, conn, username):
        while True:
            try:
                message = conn.recv(1024)
                message = message.decode("utf8")
                if message == 'disconnec':
                    raise Exception
                
                self.sendMessage(username, message)
                self.cursors[username].execute("INSERT INTO messages (username, message) VALUES (%s, %s)", (username, message))
                print(username + ": " + message)
            except:
                conn.close()
                del (self.clients[username])
                break
            
        print(username + " disconnected")
        self.sendDisconectStatus(username)

    def sendMessage(self, sender, message):
        if len(self.clients) > 0:
            msg = f'<p dir="ltr"><b>{sender}:</b> {message}</p>'
            for username in self.clients:
                if(sender != username):
                    self.clients[username].send(bytes(msg, 'utf8'))

    def sendJoinStatus(self, user):
        if len(self.clients) > 0:
            msg = ""
            for username in self.clients:
                if(user != username):
                    msg = f'<p style="text-align:center;"><b>{user}</b> has joined the group</p>'
                else:
                    msg = f'<p style="text-align:center;">Welcome to the group</p>'

                self.clients[username].send(bytes(msg, 'utf8'))

    def sendDisconectStatus(self, user):
        if len(self.clients) > 0:
            msg = f'<p style="text-align:center;"><b>{user}</b> disconnected</p>'
            for username in self.clients:
                self.clients[username].send(bytes(msg, 'utf8'))

if __name__ == "__main__":
    s = Server()