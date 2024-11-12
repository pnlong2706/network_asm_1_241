import socket
import shlex
import threading
import json

def connect_to_tracker_server(host, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        
        ### Send infomation to server
        
        ######################
        
        print(f"Connect to tracker host {host}:{port}")
        return s
    
    except Exception as e:
        return 0

def close_connection(s):
    ## Send close connection
    
    #####################
    s.close()
    
if __name__ == "__main__":
    SERVER_HOST = "127.0.0.1"
    SERVER_PORT = 6888
    
    print("Welcome to P2P file sharing, type 'help' for more infomation!")
    
    s = connect_to_tracker_server(SERVER_HOST, SERVER_PORT)
    if(s): print(f"You are connected to tracker server {SERVER_HOST}: {SERVER_PORT}\nType 'connect [hostname] [port]' to connect to other tracker server!")
    else: print("Your are not connected to tracker server!\nType 'connect [hostname] [port]' to connect to other tracker server!")
    
    while(True):
        cmd = input(">> ").lower()
        cmd = shlex.split(cmd)
        
        if(cmd[0] == 'help'):
            print("Help: ")
            
        elif(cmd[0] == 'connect'):
            if(s):
                close_connection(s)
            
            if(len(cmd)!=3):
                s = connect_to_tracker_server(SERVER_HOST, SERVER_PORT)
            else:
                SERVER_HOST = cmd[1]
                SERVER_PORT = int(cmd[2])
                s = connect_to_tracker_server(cmd[1], int(cmd[2]))
                
            if(not s):
                print("Cannot connect to this host!")

        elif(cmd[0] == "exit"):
            if(s):
                close_connection(s)
            break
        
        elif(cmd[0] == 'create'):
            announce = SERVER_HOST
            name = input(">>> Dir: ")
            file = input(">>> File: ")
            piece_lenght = input(">>> Piece length: ")
            
        elif(cmd[0] == "upload"):
            s.send("upload".encode())
            
        elif(cmd[0] == "search"):
            s.send("search".encode())
            
        elif(cmd[0] == "get_torrent"):
            s.send("get_torrent".encode())
            
        elif(cmd[0] == "download"):
            ## get peer from server
            ## perform bittorent handshake
            ## send request to get pieces
            s.send("get_peer".encode())
        
        else:
            print("Command is invalid!")
            