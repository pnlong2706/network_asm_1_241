import socket
import shlex
import threading
import json
import random
import string

def connect_to_tracker_server(host, port, client_id):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
    
        ### Send infomation to server
        with open('metafile_status.json', 'r') as file:
            data = json.load(file)
            
            request = {
                "action": "update",
                "event": "started",
                "infohash": [],
                "peerid": client_id,
                "port": 3000
            }
            
            
            for info_hash in data:
                request["infohash"].append({"hash": data[info_hash]["infohash"], "downloaded": 100})
            
            s.send(json.dumps(request).encode())
            s.recv(4096)
                
        ######################
        
        print(f"Connect to tracker host {host}:{port}")
        return s
    
    except Exception as e:
        print(e)
        return 0

def close_connection(s, client_id):
    ## Send close connection
    s.send(json.dumps({"action": "none", "event": "stop", "peerid": client_id, "port": 3000}).encode())
    #####################
    s.close()
    
if __name__ == "__main__":
    SERVER_HOST = "127.0.0.1"
    SERVER_PORT = 6888
    
    client_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    
    print("Welcome to P2P file sharing, type 'help' for more infomation!")
    
    s = connect_to_tracker_server(SERVER_HOST, SERVER_PORT, client_id)
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
                s = connect_to_tracker_server(SERVER_HOST, SERVER_PORT, client_id)
            else:
                SERVER_HOST = cmd[1]
                SERVER_PORT = int(cmd[2])
                s = connect_to_tracker_server(cmd[1], int(cmd[2]), client_id)
                
            if(not s):
                print("Cannot connect to this host!")

        elif(cmd[0] == "exit"):
            if(s):
                close_connection(s,client_id)
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
            
        elif(cmd[0] == "test"):
            s.send(json.dumps({"action": "get-peer", "infohash": "anan221r5naan"}).encode())
            res = s.recv(4096).decode()
            print(res)
        
        else:
            print("Command is invalid!")
            