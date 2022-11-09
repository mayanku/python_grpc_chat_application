from concurrent import futures

import grpc
import time

import helloworld_pb2 as chat
import helloworld_pb2_grpc as rpc


class ChatServer(rpc.ChatServerServicer):  # inheriting here from the protobuf rpc file which is generated

    def __init__(self):
        self.chats = []  # List with all the chat history
        self.registeredUsersdict = {}  # dictionary to check for user authentication
        self.userchats = []  # list to store user specific chats
        self.registeredUsersName = []  # registered users are maintained in one list

    def SendNotemulti(self, request: chat.ChatUserMessage, context):
        """
         This method stores the userspecific chats
               """
        # this is only for the server console
        print("[{}] {}".format(request.name, request.message, request.receiver))
        # Add it to the chat history
        self.userchats.append(request)
        return chat.Empty()  # something needs to be returned required by protobuf language, we just return empty msg

    def RegisteredUsers(self, request_iterator, context):
        # This method returns all the registered users list
        lastindex = 0
        while True:
            while len(self.registeredUsersName) > lastindex:
                n = self.registeredUsersName[lastindex]
                lastindex += 1
                yield n

    def ChatStreamUser(self, request_iterator, context):
        """
                This is a response-stream type call. This means the server can keep sending messages
                Every client opens this connection and waits for server to send new messages
                """
        lastindex = 0
        # For every client a infinite loop starts (in gRPC's own managed thread)
        while True:
            # Check if there are any new messages
            while len(self.userchats) > lastindex:
                n = self.userchats[lastindex]
                lastindex += 1
                yield n

    def ChatUser(self, request: chat.ChatUserMessage, context):
        print("[{}] {} {}".format(request.name, request.message, request.receiver))
        self.chatsUser[request.name + request.receiver].append(request.message)
        self.chatsUser[request.receiver + request.name].append(request.message)
        return chat.Empty()

    def register(self, request: chat.registerdetails, context):  # the function to register the user
        if request.username in self.registeredUsersdict.keys():
            result = {'responsemessage': 'failed', 'responsecode': 2}
            return chat.APIResponse(**result)
        print("User has registered with following details email-[{}] username-{} password-{}".format(request.email,
                                                                                                     request.username,
                                                                                                     request.password))

        self.registeredUsersName.append(request)
        self.registeredUsersdict[request.username] = request.password
        result = {'responsemessage': 'SUCCESS', 'responsecode': 1}
        return chat.APIResponse(**result)

    def login(self, request: chat.LoginRequest, context):  # the function to check if user has valid details
        if request.username not in self.registeredUsersdict.keys():
            result = {'responsemessage': 'failed', 'responsecode': 2}
            return chat.APIResponse(**result)
        if self.registeredUsersdict[request.username] == request.password:
            print("success")
            result = {'responsemessage': 'SUCCESS', 'responsecode': 1}
        else:
            print("Wrong credentials")
            result = {'responsemessage': 'failed', 'responsecode': 2}

        return chat.APIResponse(**result)

    def logout(self, request, context):
        return super().logout(request, context)

    # The stream which will be used to send new messages to clients
    def ChatStream(self, request_iterator, context):
        """
        This is a response-stream type call. This means the server can keep sending messages
        Every client opens this connection and waits for server to send new messages
        """
        lastindex = 0
        # For every client a infinite loop starts (in gRPC's own managed thread)
        while True:
            # Check if there are any new messages
            while len(self.chats) > lastindex:
                n = self.chats[lastindex]
                lastindex += 1
                yield n

    def SendNote(self, request: chat.Note, context):
        """
        This method is called when a clients sends a Note to the server used specifically for group chats
        """
        # this is only for the server console
        print("[{}] {}".format(request.name, request.message))
        # Add it to the chat history
        self.chats.append(request)
        return chat.Empty()  # something needs to be returned required by protobuf language, we just return empty msg


if __name__ == '__main__':
    port = 11912  # a random port for the server to run on
    # the workers is like the amount of threads that can be opened at the same time, when there are 10 clients connected
    # then no more clients able to connect to the server.
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=20))  # create a gRPC server
    rpc.add_ChatServerServicer_to_server(ChatServer(), server)  # register the server to gRPC
    # gRPC basically manages all the threading and server responding logic, which is perfect!
    print('Starting server. Listening...')
    print("Chat server is up and running")
    server.add_insecure_port('[::]:' + str(port))
    server.start()
    # Server starts in background (in another thread) so keep waiting
    # if we don't wait here the main thread will end, which will end all the child threads, and thus the threads
    # from the server won't continue to work and stop the server
    while True:
        time.sleep(64 * 64 * 100)
