import shlex
import random
import string
import argparse
import threading
import multiprocessing

parser = argparse.ArgumentParser()
parser.add_argument("-sh", "--server_host", default="127.0.0.1", help = "")
parser.add_argument("-sp", "--server_port", default=6889, help = "")
parser.add_argument("-lp", "--listen_port", default=3000, help = "")
args = parser.parse_args()

from client import (
    connect_to_tracker_server,
    close_connection,
    create_meta_file,
    publish,
    check_metafile,
    get_peers,
    download_file,
    search_torrent,
    get_torrent,
    get_my_torrent
)

from request_handler import (
    start_handling_request
)

if __name__ == "__main__":
    SERVER_HOST = args.server_host
    SERVER_PORT = args.server_port
    LISTEN_PORT = args.listen_port
    CLIENT_ID = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    
    # thread = threading.Thread(target=start_handling_request, args=("127.0.0.1", int(LISTEN_PORT)))
    # thread.start()
    
    proc = multiprocessing.Process(target=start_handling_request, args=("192.168.54.250", int(LISTEN_PORT)))
    proc.start()
    
    print("Welcome to P2P file sharing, type 'help' for more infomation!")
    socket = connect_to_tracker_server(SERVER_HOST, SERVER_PORT, CLIENT_ID, LISTEN_PORT)
    
    if(socket): print(f"You are connected to tracker server {SERVER_HOST}:{SERVER_PORT}\nType 'connect [hostname] [port]' to connect to other tracker server!")
    else: print("Your are not connected to tracker server!\nType 'connect [hostname] [port]' to connect to other tracker server!")
    
    while(True):
        cmd = input(">> ").lower()
        cmd = shlex.split(cmd)
        if len(cmd)==0: continue
        
        try:
            if cmd[0] == 'help':
                print("Help: ")
                
            elif cmd[0] == 'connect' :
                if socket: close_connection(socket, SERVER_HOST, CLIENT_ID, LISTEN_PORT)
                
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
                if(socket): close_connection(socket, SERVER_HOST, CLIENT_ID, LISTEN_PORT)
                proc.terminate() 
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
                
            elif cmd[0] == "publish" :
                if len(cmd) == 1:
                    announce = SERVER_HOST
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
                    
                    publish(
                        tracker_socket= socket, 
                        tracker_addr=   SERVER_HOST,
                        received_hash=  infohash, 
                        client_id=      CLIENT_ID,
                        listen_port=    LISTEN_PORT
                    )
                    
                    print("Publish file successfully")
                
                elif len(cmd) == 2:
                    infohash = cmd[1]
                    if not check_metafile(infohash): print("Metafile is not exist!")
                    
                    publish(
                        tracker_socket= socket, 
                        tracker_addr=   SERVER_HOST,
                        received_hash=  infohash, 
                        client_id=      CLIENT_ID,
                        listen_port=    LISTEN_PORT
                    )
                    
                    print("Publish file successfully")
                
                else: print("Invalid command, type 'help' for more!")
                
            elif cmd[0] == "search" :
                if len(cmd) >= 2: 
                    keyword = cmd[1]
                else:
                    keyword = input(">>> keyword: ")
                    
                if not socket:
                    print("You are not connect to tracker server!")
                    continue
                    
                res = search_torrent(
                    tracker_socket= socket, 
                    keyword=        keyword
                )
                
                for i in range(len(res)):
                    if i >= 10: break
                    print(f"{i+1}. {res[i][1]}. Description: {res[i][2]}")
                
            elif cmd[0] == "get_torrent" :
                if len(cmd) != 2:
                    print("Invalid command, type 'help' for more!")
                    
                get_torrent(
                    tracker_socket= socket,
                    infohash=       cmd[1]
                )
                
            elif cmd[0] == "my_torrent":
                res = get_my_torrent()
                for i in range(len(res)):
                    print(f"{i+1}. {res[i][0]}. Downloaded: {res[i][2]:8}. Description: {res[i][1]}")
                
            elif cmd[0] == "download" :
                if len(cmd)!=2: print("Invalid command, type 'help' for more!")
                if not check_metafile(cmd[1]): print("Metafile is not exist!")
                
                peers = get_peers(
                    tracker_socket= socket,
                    infohash=       cmd[1],
                    client_id=      CLIENT_ID
                )
                
                print(f"Downloading from {peers} ... We'll notice you when the download is complete!")

                download_thread = threading.Thread(target=download_file, args=(socket, CLIENT_ID, LISTEN_PORT, cmd[1], peers))
                download_thread.start()
            
            else:
                print("Invalid command, type 'help' for more!")
        
        except Exception as e:
            proc.terminate() 
            print(e)
            