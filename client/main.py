import shlex
import threading
import random
import string
import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument("-sh", "--server_host", default="127.0.0.1", help = "")
parser.add_argument("-sp", "--server_port", default=6888, help = "")
parser.add_argument("-lp", "--listen_port", default=3000, help = "")
args = parser.parse_args()

from client import (
    connect_to_tracker_server,
    close_connection,
    create_meta_file,
    upload,
    check_metafile,
    get_peers
)

if __name__ == "__main__":
    
    SERVER_HOST = args.server_host
    SERVER_PORT = args.server_port
    LISTEN_PORT = args.listen_port
    CLIENT_ID = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    
    print("Welcome to P2P file sharing, type 'help' for more infomation!")
    socket = connect_to_tracker_server(SERVER_HOST, SERVER_PORT, CLIENT_ID, LISTEN_PORT)
    
    if(socket): print(f"You are connected to tracker server {SERVER_HOST}:{SERVER_PORT}\nType 'connect [hostname] [port]' to connect to other tracker server!")
    else: print("Your are not connected to tracker server!\nType 'connect [hostname] [port]' to connect to other tracker server!")
    
    while(True):
        cmd = input(">> ").lower()
        cmd = shlex.split(cmd)
        if len(cmd)==0: continue
        
        if cmd[0] == 'help':
            print("Help: ")
            
        elif cmd[0] == 'connect' :
            if socket:close_connection(socket)
            
            if len(cmd) == 1:
                socket = connect_to_tracker_server(SERVER_HOST, SERVER_PORT, CLIENT_ID, LISTEN_PORT)
            elif len(cmd) == 3:
                SERVER_HOST = cmd[1]
                SERVER_PORT = int(cmd[2])
                socket = connect_to_tracker_server(cmd[1], int(cmd[2]), CLIENT_ID, LISTEN_PORT)
            else: print("Invalid command, type 'help' for more!")
                
            if(not socket): print("Cannot connect to this host!")
            else: print("Connect successfully!")

        elif cmd[0] == "exit" :
            if(socket): close_connection(socket, CLIENT_ID, LISTEN_PORT)
            break
        
        elif cmd[0] == 'create' :
            announce = "none"
            name = input(">>> Name: ")
            files = input(">>> Files: ").split()
            description = input(">>> Description: ")
            piece_length = int(input(">>> Piece length: "))
            
            infohash = create_meta_file(
                announce=       announce,
                name=           name,
                files=          files,
                piece_length=   piece_length,
                description=    description
            )
            
            print(f"Metafile created successfully!\nInfoHash: {infohash}")
            
        elif cmd[0] == "upload" :
            infohash = cmd[1]
            
            upload(
                tracker_socket= socket, 
                tracker_addr=   SERVER_HOST,
                received_hash=  infohash, 
                client_id=      CLIENT_ID
            )
            
        elif cmd[0] == "search" :
            socket.send("search".encode())
            
        elif cmd[0] == "get_torrent" :
            socket.send("get_torrent".encode())
            
        elif cmd[0] == "download" :
            if len(cmd)!=2: print("Invalid command, type 'help' for more!")
            if not check_metafile(cmd[1]): print("Metafile is not exist!")
            
            peers = get_peers(
                tracker_socket= socket,
                infohash=       cmd[1]
            )
            
            print(peers)
        
        else:
            print("Invalid command, type 'help' for more!")
            