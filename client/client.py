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
                if(data[info_hash]["announce"] == host):
                    request["infohash"].append({"hash": info_hash, "downloaded": 100})
            
            s.send(json.dumps(request).encode())
            s.recv(4096)
        
        return s
    
    except Exception as e:
        return 0

def close_connection(s, client_id, client_port):
    ## Send close connection
    s.send(json.dumps({"action": "stop", "event": "stop", "peerid": client_id, "port": client_port}).encode())
    s.close()
        
def create_meta_file(announce, name, files, piece_length, description):
    torrent_id = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        
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
            "description": description,
            "piece_have": "0010110111",  
            "left": 128  
        }
    }

    pieces_concatenated = ""  
    total_length = 0
    
    for file in files:
        file_path = os.path.join("file", file)
        print(f"Đang xử lý file: {file_path}")

        total_length += os.path.getsize(file_path)
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
    metadata[torrent_id]["piece_have"] = "1" * ( total_length // piece_length )

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
    current_metadata.update({infohash: metadata[torrent_id]})

    # Lưu lại toàn bộ metadata vào file
    with open(meta_file_name, "w") as meta_file:
        json.dump(current_metadata, meta_file, indent=4)
        
    return infohash

def upload(tracker_socket, tracker_addr, received_hash, client_id):
    #s.send("upload".encode())
    with open('metafile_status.json', 'r') as file:
        data = json.load(file)

    # Tạo một request để gửi đi
    request = {
        "action": "upload",
        "event": "started",
        "info": data[received_hash]["info"],
        "description": data[received_hash]["description"],
        "peerid": client_id,
        "downloaded": 100,
        "port": 3000
    }
    
    data[received_hash]["announce"] = tracker_addr
    tracker_socket.send(json.dumps(request).encode())
    response = json.loads(tracker_socket.recv(4096).decode())
    
    if(response["status"] == "success"):
        with open("metafile_status.json", "w") as meta_file:
            json.dump(data, meta_file, indent=4)

def check_metafile(infohash):
    with open('metafile_status.json', 'r') as file:
        data = json.load(file)
    
    return (infohash in data)

def get_peers(tracker_socket, infohash):
    request = {
        "action": "get-peer",
        "infohash": infohash,
    }
    
    tracker_socket.send(json.dumps(request).encode())
    response = json.loads(tracker_socket.recv(4096).decode())
    
    if(response["status"] == "success"):
        return response["result"]
    
if __name__ == "__main__":
    print("Client::test")
            
            