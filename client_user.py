import sys
import threading
import time

import grpc
import helloworld_pb2 as chat
import helloworld_pb2_grpc as rpc

address = 'localhost'
port = 11912


class Client:

    def __init__(self, u: str):
        # create a gRPC channel + stub
        channel = grpc.insecure_channel(address + ':' + str(port))
        self.conn = rpc.ChatServerStub(channel)

    def __listen_for_messages(self, groupno,chattype):
        for note in self.conn.ChatStream(chat.Empty()):  # this line will wait for new messages from the server!
            if (note.group == groupno):
                print("[{}]: {}".format(note.name, note.message))# the message from group chat
            else:
                if chattype=="broad" and note.group==0:
                    print("[{}]: {}".format(note.name, note.message))

    def __listen_for_user_messages(self, login_username, user_to_chat):
        """
               This method will be ran in a separate thread as the main/ui thread, because the for-in call is blocking
               when waiting for new messages
               """
        for note in self.conn.ChatStreamUser(chat.Empty()):  # this line will wait for new messages from the server!
            if note.name == user_to_chat and note.receiver == login_username:  # checking if the user is correct required user
                print("[{}]: {}".format(note.name, note.message))  # the chat message

    def get_registered_users_list(self):
        """
          to get the all registered users registered in the chat application
        """
        print("Available users are:  ")
        for note in self.conn.RegisteredUsers(chat.Empty()):  # this line will wait for new messages from the server!
            print("[{}]".format(note.username))  # # debugging statement

    def registered_users(self):
        """
        thread to get the registered users list whenever a new user a registered the information is passed to the user
        """
        threading.Thread(target=self.get_registered_users_list, daemon=True).start()

    def receivemessages(self, groupno,chattype):
        """
        thread for receiving the group chat messages
        """
        threading.Thread(target=self.__listen_for_messages, args=[groupno,chattype], daemon=True).start()

    def receiveusermessages(self, login_username, user_to_chat):
        """
        thread for receiving the specific user messages for one to one chat
        """
        threading.Thread(target=self.__listen_for_user_messages, args=[login_username, user_to_chat],
                         daemon=True).start()

    def register_user(self, register_usernames, register_passwords, emails):
        """
        function to register the user the details are sent to the server
        """
        print("[{}] {} {}".format(register_usernames, register_passwords, emails))
        n = chat.registerdetails()
        n.username = register_usernames
        n.password = register_passwords
        n.email = email
        return self.conn.register(n)

    def login_user(self, login_username, login_password):
        """
        user authentication of user
        """
        n = chat.LoginRequest()
        n.username = login_username
        n.password = login_password
        return self.conn.login(n)

    def send_message(self, username, message, group):
        """
        for sending message in group chat
        """
        if message != '':
            n = chat.Note()  # create protobug message (called Note)
            n.name = username  # set the username
            n.message = message  # set the actual message of the note
            # print("S[{}] {}".format(n.name, n.message))  # debugging statement
            n.group = group
            self.conn.SendNote(n)  # send the Note to the server

    def send_to_user(self, login_username, message_to_user, user_to_chat, ):
        """
        for sending message to specific user
        """
        if message_to_user != '':
            n = chat.ChatUserMessage()  # create protobug message (called Note)
            n.name = login_username  # set the username
            n.message = message_to_user  # set the actual message of the note
            n.receiver = user_to_chat
            # print("S[{}] {}".format(n.name, n.message))  # debugging statement
            self.conn.SendNotemulti(n)  # send the Note to the server


if __name__ == '__main__':

    username = None
    c = Client(username)

    print("Press 1 to register Press 2 to login")
    choice = input("Enter Your choice ")

    if choice == "1":
        print("Register User")

        email = input("Enter Your Email  ")
        register_username = input("Enter Your Name  ")
        register_password = input("Set Your Password ")
        y = c.register_user(register_username, register_password, email)
        if y.responsemessage == "failed":
            print("Username already exist Start the application again and choose a different username")
            sys.exit()
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
            print("Press 1 for group chat Press 2 for chat with specific user Press 3 for broadcast")
            chattype = input()
            if chattype == "1":
                mess = "hi"
                print("You have joined the chat")
                group = input("Enter the group you want to join 1 or 2 or 3 ")
                print(" All users in group {} will be able to see your chat".format(group))
                print("To exit the group chat type end")
                print("Type Your Message")
                chat_type = "multi"
                c.receivemessages(group, chat_type)
                while mess != 'end':
                    mess = input()
                    c.send_message(login_username, mess, group)

            if chattype == "3":
                mess = "hi"
                print("You have joined the chat")
                print(" Users in the group are ")
                c.registered_users();
                time.sleep(1)
                print("To exit the group chat type end")
                print("Type Your Message")
                chat_type = "broad"
                group="0"
                c.receivemessages(group, chat_type)
                while mess != 'end':
                    mess = input()
                    c.send_message(login_username, mess, group)

            if chattype == "2":
                c.registered_users();
                time.sleep(1)
                print("Enter the username of the person you want to chat with")
                user_to_chat = input()
                print("Connection with {} has been established".format(user_to_chat))
                print("Enter your message to exit the chat type end")
                message_to_user = "hi"
                c.receiveusermessages(login_username, user_to_chat)
                while message_to_user != 'end':
                    message_to_user = input()
                    c.send_to_user(login_username, message_to_user, user_to_chat)

        if x.responsemessage == "failed":
            print("Wrong Credentials or user is not registered")
            # c.login_again()
    print("Application is Closed See you soon to chat again run the client")
