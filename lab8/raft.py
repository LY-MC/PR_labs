import socket
import json


class RAFTFactory:
    def __init__(self,
                 service_info: dict,
                 udp_host: str = "127.0.0.1",
                 udp_port: int = 4444,
                 udp_buffer_size: int = 1024,
                 num_followers: int = 2):

        self.udp_host = udp_host
        self.udp_port = udp_port
        self.udp_buffer_size = udp_buffer_size
        self.udp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.service_info = service_info
        self.min_num_msgs = num_followers * 2

        try:
            self.udp_socket.bind((self.udp_host, self.udp_port))
            self.role = "leader"

            self.followers = []
            count_of_msgs = 0
            while True:
                message, address = self.udp_socket.recvfrom(self.udp_buffer_size)

                if message.decode() == "Accept":
                    data = json.dumps(self.service_info)
                    count_of_msgs += 1
                    self.udp_socket.sendto(str.encode(data), address)
                else:
                    message = message.decode()
                    count_of_msgs += 1
                    follower_data = json.loads(message)
                    self.followers.append(follower_data)
                if count_of_msgs >= self.min_num_msgs:
                    break
        except:
            self.role = "follower"
            self.leader_data = self.send_accept("Accept")
            self.send_accept(self.service_info)

        self.info = service_info
        self.udp_socket.close()

    def send_accept(self, msg):
        if type(msg) is str:
            bytes_to_send = str.encode(msg)
            self.udp_socket.sendto(bytes_to_send, (self.udp_host, self.udp_port))
            msg_from_server = self.udp_socket.recvfrom(self.udp_buffer_size)[0]
            return json.loads(msg_from_server.decode())
        else:
            str_dict = json.dumps(msg)
            bytes_to_send = str.encode(str_dict)
            self.udp_socket.sendto(bytes_to_send, (self.udp_host, self.udp_port))

    def to_string(self):
        print(f'Is leader: {self.role}')
        if self.role == 'leader':
            print(f'Followers: {self.followers}')
        return self.info
