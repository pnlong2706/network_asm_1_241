import socket
import shlex
import threading
import json
import hashlib
import os
import random
import string

import os
import pickle
import struct

def connect_to_tracker_server(host, port, client_id, client_port):
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
                "port": client_port
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

def close_connection(s, client_id, client_port):
    ## Send close connection
    s.send(json.dumps({"action": "none", "event": "stop", "peerid": client_id, "port": client_port}).encode())
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
    LISTEN_PORT = 3000
    
    client_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    
    print("Welcome to P2P file sharing, type 'help' for more infomation!")
    
    s = connect_to_tracker_server(SERVER_HOST, SERVER_PORT, client_id, LISTEN_PORT)
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
                s = connect_to_tracker_server(SERVER_HOST, SERVER_PORT, client_id, LISTEN_PORT)
            else:
                SERVER_HOST = cmd[1]
                SERVER_PORT = int(cmd[2])
                s = connect_to_tracker_server(cmd[1], int(cmd[2]), client_id, LISTEN_PORT)
                
            if(not s):
                print("Cannot connect to this host!")

        elif(cmd[0] == "exit"):
            if(s):
                close_connection(s,client_id, LISTEN_PORT)
            break
        
        elif(cmd[0] == 'create'):

            torrent_id = ''.join(random.choices(string.ascii_letters + string.digits, k=12))

            announce = SERVER_HOST
            name = input(">>> Dir: ")
            files = input(">>> File: ").split()
            piece_length = int(input(">>> Piece length: "))

            # Khởi tạo cấu trúc metadata
            metadata = {
                torrent_id: {
                    "announce": announce,
                    "info": {
                        "files": [],
                        "name": name,
                        "piece length": piece_length,
                        "pieces": ""
                    },
                    "description": "information",
                    "piece_have": "0010110111",  
                    "left": 128  
                }
            }

            pieces_concatenated = ""  

            for file in files:
                file_path = os.path.join(name, file)
                print(f"Đang xử lý file: {file_path}")

                file_info = {
                    "length": os.path.getsize(file_path),
                    "path": file
                }

                try:
                    with open(file_path, "rb") as f:
                        while True:
                            piece_data = f.read(piece_length)
                            if not piece_data:
                                break
                            
                            # Tính hash SHA-1 cho phần dữ liệu và nối vào `pieces_concatenated`
                            sha1 = hashlib.sha1(piece_data).digest()
                            pieces_concatenated += sha1.hex()
                except FileNotFoundError:
                    print(f"File '{file_path}' không tồn tại.")
                    continue

                # Thêm thông tin file vào danh sách `files`
                metadata[torrent_id]["info"]["files"].append(file_info)

            # Gán chuỗi hash SHA-1 vào `pieces` trong metadata
            metadata[torrent_id]["info"]["pieces"] = pieces_concatenated

            # Tính toán infohash từ phần `info`
            info_dict = metadata[torrent_id]["info"]
            info_bytes = json.dumps(info_dict).encode('utf-8')  # Chuyển dict info thành bytes
            infohash = hashlib.sha1(info_bytes).hexdigest()  # Tính SHA-1 hash của info

            # Thêm infohash vào metadata
            metadata[torrent_id]["infohash"] = infohash

            # Kiểm tra xem metafile đã tồn tại chưa và đọc nó nếu có
            meta_file_name = "metafile_status.json"
            if os.path.exists(meta_file_name):
                with open(meta_file_name, "r") as meta_file:
                    current_metadata = json.load(meta_file)
            else:
                current_metadata = {}

            # Append thêm metadata mới vào dữ liệu hiện tại
            current_metadata.update(metadata)

            # Lưu lại toàn bộ metadata vào file
            with open(meta_file_name, "w") as meta_file:
                json.dump(current_metadata, meta_file, indent=4)

            print(f"Metadata đã được lưu vào '{meta_file_name}'")

            
        elif(cmd[0] == "upload"):
            #s.send("upload".encode())
            received_hash = cmd[1]
            with open('metafile_status.json', 'r') as file:
                data = json.load(file)

            # Tạo một request để gửi đi
            request = {
                "action": "upload",
                "event": "started",
                "peerid": client_id,
                "downloaded": 100,
                "port": 3000
            }

            # Duyệt qua từng torrent trong metadata
            for info_hash, torrent_info in data.items():
                # Kiểm tra nếu infohash trong metafile khớp với hash đã nhận
                # print(info_hash)
                # print(torrent_info["infohash"])
                # print(received_hash)
                if torrent_info["infohash"] == received_hash:
                    # Nếu khớp, thêm thông tin của torrent vào request
                    request["info"]= torrent_info["info"]
                    request["description"] = torrent_info["description"]

                    #print(request)
                

            # Gửi request dưới dạng JSON
            s.send(json.dumps(request).encode())
            
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
            
        elif(cmd[0] == "test"):
            s.send(json.dumps({"action": "get-peer", "infohash": "anan221r5naan"}).encode())
            res = s.recv(4096).decode()
            print(res)
        
        else:
            print("Command is invalid!")
            