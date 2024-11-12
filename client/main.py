import socket
import shlex
import threading
import json
import os
import pickle
import struct

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
    
def get_info_hash(torrent_file):
    with open(torrent_file, 'rb') as f:
        torrent_data = pickle.loads(f.read())
        return torrent_data['info_hash']

def generate_peer_id():
    return os.urandom(20)  # Tạo ID ngẫu nhiên 20 byte

def create_handshake(info_hash, peer_id):
    """Tạo gói tin handshake theo giao thức BitTorrent"""
    pstr = "BitTorrent protocol"
    pstrlen = len(pstr)
    reserved = b'\x00' * 8
    
    handshake = (
        bytes([pstrlen]) +
        pstr.encode() +
        reserved +
        info_hash +
        peer_id.encode()
    )
    return handshake

def get_piece_length(torrent_file):
    with open(torrent_file, 'rb') as f:
        torrent_data = pickle.loads(f.read())
        return torrent_data['piece_length']

def get_num_pieces(torrent_file):
    with open(torrent_file, 'rb') as f:
        torrent_data = pickle.loads(f.read())
        return len(torrent_data['pieces'])
    
def create_request(piece_index, offset, length):
    """Tạo gói tin request theo giao thức BitTorrent"""
    # id=6 cho message type REQUEST
    return struct.pack('>IbIII', 13, 6, piece_index, offset, length)

def receive_piece(sock):
    """Nhận một mảnh dữ liệu từ peer"""
    try:
        # Nhận 4 byte đầu tiên chứa độ dài message
        length_prefix = sock.recv(4)
        if not length_prefix:
            return None
            
        # Chuyển đổi độ dài từ bytes sang số
        length = struct.unpack('>I', length_prefix)[0]
        
        # Nhận phần dữ liệu còn lại
        piece_data = sock.recv(length)
        if len(piece_data) != length:
            return None
            
        return piece_data
        
    except Exception as e:
        print(f"Error receiving piece: {e}")
        return None
    
def save_piece(piece_data, piece_index, torrent_file):
    with open(torrent_file, 'rb') as f:
        torrent_data = pickle.loads(f.read())
        torrent_data['pieces'][piece_index] = piece_data
        
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
            if len(cmd) != 2:
                print("Usage: download [torrent file name]")
                continue
                
            torrent_file = cmd[1]
            if not os.path.exists(torrent_file):
                print(f"Torrent file {torrent_file} not found")
                continue
                
            # Send request to get peer list from tracker
            s.send("get_peer".encode())
            s.send(torrent_file.encode())
            
            peer_list = pickle.loads(s.recv(1024))
            if not peer_list:
                print("No peers found sharing this file")
                continue
                
            print(f"Found {len(peer_list)} peers sharing the file")
            
            # Connect to each peer
            for peer in peer_list:
                peer_host = peer[0] 
                peer_port = peer[1]
                
                # Create connection to peer
                peer_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    peer_sock.connect((peer_host, peer_port))
                except:
                    print(f"Cannot connect to peer {peer_host}:{peer_port}")
                    continue
                    
                # Perform BitTorrent handshake
                info_hash = get_info_hash(torrent_file)
                peer_id = generate_peer_id()
                
                handshake = create_handshake(info_hash, peer_id)
                peer_sock.send(handshake)
                
                response = peer_sock.recv(68)
                if len(response) != 68:
                    print("Handshake failed")
                    peer_sock.close()
                    continue
                    
                print(f"Successfully connected to peer {peer_host}:{peer_port}")
                
                # Send requests for pieces
                piece_length = get_piece_length(torrent_file)
                num_pieces = get_num_pieces(torrent_file)
                
                for piece_index in range(num_pieces):
                    request = create_request(piece_index, 0, piece_length)
                    peer_sock.send(request)
                    
                    piece_data = receive_piece(peer_sock)
                    if not piece_data:
                        print(f"Error downloading piece {piece_index}")
                        continue
                        
                    save_piece(piece_data, piece_index, torrent_file)
                    print(f"Downloaded piece {piece_index}/{num_pieces}")
                
                peer_sock.close()
                
            print("File download completed")
            s.send("get_peer".encode())
        
        else:
            print("Command is invalid!")
            