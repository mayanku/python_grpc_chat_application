import threading
from tkinter import *
from tkinter import simpledialog

import grpc

import helloworld_pb2 as chat
import helloworld_pb2_grpc as rpc

address = 'localhost'
port = 11912


class Client:

    def __init__(self, u: str):
        # the frame to put ui components on
        # create a gRPC channel + stub
        channel = grpc.insecure_channel(address + ':' + str(port))
        self.conn = rpc.ChatServerStub(channel)
        # create new listening thread for when new message streams come in

    def __listen_for_messages(self):
        """
        This method will be ran in a separate thread as the main/ui thread, because the for-in call is blocking
        when waiting for new messages
        """
        for note in self.conn.ChatStream(chat.Empty()):  # this line will wait for new messages from the server!
            print("R[{}] {}".format(note.name, note.message))  # debugging statement
            # self.chat_list.insert(END, "[{}] {}\n".format(note.name, note.message))  # add the message to the UI

    def __listen_for_user_messages(self, login_username, user_to_chat):
        """
               This method will be ran in a separate thread as the main/ui thread, because the for-in call is blocking
               when waiting for new messages
               """
        for note in self.conn.ChatStreamUser(chat.Empty()):  # this line will wait for new messages from the server!
            if(note.name==user_to_chat):
                print("R[{}] {}".format(note.name, note.message))  # debugging statement
            # self.chat_list.insert(END, "[{}] {}\n".format(note.name, note.message))  # add the message to the UI

    def receivemessages(self):
        threading.Thread(target=self.__listen_for_messages, daemon=True).start()

    def receiveusermessages(self, login_username, user_to_chat):
        threading.Thread(target=self.__listen_for_user_messages,args=[login_username,user_to_chat], daemon=True).start()

    def register_user(self, register_usernames, register_passwords, emails):
        print("[{}] {} {}".format(register_usernames, register_passwords, emails))
        n = chat.registerdetails()
        n.username = register_usernames
        n.password = register_password
        n.email = email
        self.conn.register(n)

    def login_user(self, login_username, login_password):
        n = chat.LoginRequest()
        n.username = login_username
        n.password = login_password
        return self.conn.login(n)

    def send_message(self, username, message):
        """
        This method is called when user enters something into the textbox
        """  # retrieve message from the UI
        if message != '':
            n = chat.Note()  # create protobug message (called Note)
            n.name = username  # set the username
            n.message = message  # set the actual message of the note
            # print("S[{}] {}".format(n.name, n.message))  # debugging statement
            self.conn.SendNote(n)  # send the Note to the server

    def send_to_user(self, login_username, message_to_user, user_to_chat, ):
        if message_to_user != '':
            n = chat.Note()  # create protobug message (called Note)
            n.name = login_username  # set the username
            n.message = message_to_user # set the actual message of the note
            # print("S[{}] {}".format(n.name, n.message))  # debugging statement
            self.conn.SendNotemulti(n)  # send the Note to the server


if __name__ == '__main__':

    username = None
    c = Client(username)

    print("Press 1 to register Press 2 to login")
    choice = input("Enter Your choice")

    if choice == "1":
        print("Register User")

        email = input("Enter Your Email  ")
        register_username = input("Enter Your Name  ")
        register_password = input("Set Your Password ")
        c.register_user(register_username, register_password, email)
        print("You have been Registered")

    print("You can Login now Welcome to this chat application")

    while username is None:
        # retrieve a username so we can distinguish all the different clients
        username = "notnone"
        login_username = input("Username ")
        passs = input("Password ")
        x = c.login_user(login_username, passs)
        if x.responsemessage == "SUCCESS":
            print("You Have successfully Logged in")
            print("What would You like ")
            print("Press 1 for group chat Press 2 for chat with specific user")
            chattype = input()
            if chattype == "1":
                mess = "hi"
                print("You have joined the chat")
                print("To exit the group chat type end")
                print("Type Your Message")

                c.receivemessages()

                while mess != 'end':
                    mess = input()
                    c.send_message(login_username, mess)

            if chattype == "2":
                print("Enter the username of the person you want to chat with")
                user_to_chat = input()

                print("Connection with {} has been established", user_to_chat)
                print("To exit the chat type end")
                message_to_user = "hi"
                c.receiveusermessages(login_username, user_to_chat)
                while message_to_user != 'end':
                    message_to_user = input()
                    c.send_to_user(login_username, message_to_user, user_to_chat, )
