import socket
import threading
from client_handler import client_handler
import argparse

# Initialize parser
parser = argparse.ArgumentParser()

parser.add_argument("-hs", "--host", default="127.0.0.1", help = "")
parser.add_argument("-pt", "--port", default=6888, help = "")

args = parser.parse_args()


def start_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen()
    
    print(f"Server is listening at port {port}")
    
    try:
        while True:
            conn, addr = server_socket.accept()
            # host = server_socket.getsockname()
            # log_event(f"Accepted connection from {addr}, hostname is {host}")
            thread = threading.Thread(target=client_handler, args=(conn, addr))
            thread.start()
            print(f"Active connections: {threading.active_count() - 1}")
            
    except KeyboardInterrupt as e:
        print(f"Close server {e}")
    finally:
        server_socket.close()
        if(conn):
            conn.close()
    
if __name__ == "__main__":
    start_server(args.host, int(args.port))