import socket
import shlex
import threading
import json
import hashlib
import os
import random
import string
import math

import os
import pickle
import struct

from download import download_from_peers

def connect_to_tracker_server(host, port, client_id, client_port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
    
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
                valid = True
                for file in data[info_hash]["info"]["files"]:
                    if not os.path.exists(os.path.join("file", file["path"])): valid = False
                                
                if valid:
                    request["infohash"].append({"hash": info_hash, "downloaded": data[info_hash]["downloaded"]})
            
            sock.send(("POST / HTTP/1.1\r\nHost:" + host + "/update\r\n\r\n" + json.dumps(request)).encode())
            sock.recv(4096)
                
        return sock
    
    except Exception as e:
        return 0

def close_connection(s, host, client_id, client_port):
    ## Send close connection
    s.send(("POST / HTTP/1.1\r\nHost:" + host + "/update\r\n\r\n" + json.dumps({"action": "stopped", "event": "stopped", "peerid": client_id, "port": client_port})).encode())
    s.close()
        
def create_meta_file(announce, name, files, piece_length, description):
    torrent_id = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        
    if(piece_length > 524288):
        raise Exception("Piece length must be smaller than 512KB!")
        
    # Khởi tạo cấu trúc metadata
    metadata = {
        torrent_id: {
            "announce": announce,
            "info": {
                "files": [],
                "name": name,
                "piece_length": piece_length,
                "pieces": ""
            },
            "description": description,
            "piece_have": "0010110111",  
            "downloaded": 0  
        }
    }

    pieces_concatenated = ""  
    total_length = 0
    num_piece = 0
    
    for file in files:
        file_path = os.path.join("file", file)
        print(f"Processing file: {file_path}")
        
        if not os.path.exists(file_path):
            raise Exception("File is not exist in file folder!")

        sz = os.path.getsize(file_path)
        total_length += sz
        file_info = {
            "length": sz,
            "path": file
        }
        
        num_piece += math.ceil(sz / piece_length)

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
    metadata[torrent_id]["piece_have"] = "1" * num_piece
    metadata[torrent_id]["downloaded"] = num_piece * piece_length

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

def publish(tracker_socket, tracker_addr, received_hash, client_id, listen_port):
    #s.send("upload".encode())
    if not tracker_socket:
        raise Exception("You are not connected to any tracker server")
    
    with open('metafile_status.json', 'r') as file:
        data = json.load(file)
        
    if not received_hash in data:
        raise Exception("Metafile not found!")

    # Tạo một request để gửi đi
    request = {
        "action": "publish",
        "event": "started",
        "info": data[received_hash]["info"],
        "description": data[received_hash]["description"],
        "peerid": client_id,
        "downloaded": data[received_hash]["downloaded"],
        "port": listen_port
    }
    
    data[received_hash]["announce"] = tracker_addr
    tracker_socket.send(("POST / HTTP/1.1\r\nHost:" + tracker_addr + "/publish\r\n\r\n" + json.dumps(request)).encode())
    response = json.loads(tracker_socket.recv(4096).decode())
    
    if(response["status"] == "success"):
        with open("metafile_status.json", "w") as meta_file:
            json.dump(data, meta_file, indent=4)

def check_metafile(infohash):
    with open('metafile_status.json', 'r') as file:
        data = json.load(file)
    
    return (infohash in data)

def get_peers(tracker_socket, infohash, client_id):
    if not tracker_socket:
        raise Exception("You are not connected to any tracker server")
    
    request = {
        "action":   "get-peer",
        "id":       client_id,
        "infohash": infohash
    }
    
    tracker_socket.send(("GET / HTTP/1.1\r\nHost:" + tracker_socket.getsockname()[0] + "/peers\r\n\r\n" + json.dumps(request)).encode())
    response = json.loads(tracker_socket.recv(4096).decode())
    
    if(response["status"] == "success"):
        return response["peers"]
    else:
        raise Exception(response["failure_reason"])
    
def download_file(tracker_socket, client_id, listen_port, infohash, peers):
    with open('metafile_status.json', 'r') as file:
        data = json.load(file)
    
    request = {
        "action": "download",
        "event": "started",
        "infohash": infohash,
        "peerid": client_id,
        "port": listen_port,
        "downloaded": data[infohash]["downloaded"]
    }
    
    tracker_socket.send(("POST / HTTP/1.1\r\nHost:" + tracker_socket.getsockname()[0] + "/download\r\n\r\n" + json.dumps(request)).encode())
    response = json.loads(tracker_socket.recv(4096).decode())
    
    download_from_peers(
                    info_hash=  infohash,
                    client_id=  client_id,
                    peers=      peers
                )
    
    with open('metafile_status.json', 'r') as file:
        data = json.load(file)
    
    print(f"\nFinish download: {infohash}, you can see log file of download process!\n>> ", end =" ")
    
    request = {
        "action": "download",
        "event": "completed",
        "infohash": infohash,
        "peerid": client_id,
        "port": listen_port,
        "downloaded": data[infohash]["downloaded"]
    }
    
    tracker_socket.send(("POST / HTTP/1.1\r\nHost:" + tracker_socket.getsockname()[0] + "/download\r\n\r\n" + json.dumps(request)).encode())
    response = json.loads(tracker_socket.recv(4096).decode())
    
def search_torrent(tracker_socket, keyword):
    
    request = {
        "action": "search",
        "keyword": keyword
    }
    
    tracker_socket.send(("GET / HTTP/1.1\r\nHost:" + tracker_socket.getsockname()[0] + "/search\r\n\r\n" + json.dumps(request)).encode())
    response = json.loads(tracker_socket.recv(4096).decode())
    
    return response["result"]

def get_torrent(tracker_socket, infohash):
    request = {
        "action": "get-torrent",
        "infohash": infohash
    }
    
    tracker_socket.send(("GET / HTTP/1.1\r\nHost:" + tracker_socket.getsockname()[0] + "/getTorrent\r\n\r\n" + json.dumps(request)).encode())
    response = json.loads(tracker_socket.recv(1024*1024).decode())
    
    if(response["status"] == "success"):
        meta_file_name = "metafile_status.json"
        if os.path.exists(meta_file_name):
            with open(meta_file_name, "r") as meta_file:
                    current_metadata = json.load(meta_file)
        else:
            current_metadata = {}

        metadata = {}
        metadata["announce"] = str(tracker_socket.getsockname()[0])
        metadata["info"] = response["result"]["info"]
        metadata["description"] = response["result"]["description"]
        
        num_piece = 0
        piece_length = metadata["info"]["piece_length"]
        for file in metadata["info"]["files"]:
            num_piece += math.ceil( file["length"] / piece_length )
        
        metadata["piece_have"] = "0" * num_piece
        metadata["downloaded"] = 0
        metadata["infohash"] = infohash
        
        # Append thêm metadata mới vào dữ liệu hiện tại
        current_metadata.update({infohash: metadata})

        # Lưu lại toàn bộ metadata vào file
        with open(meta_file_name, "w") as meta_file:
            json.dump(current_metadata, meta_file, indent=4)
            
        print("Success!")
        
    else:
        print(response["failure_reason"])
        
def get_my_torrent():
    meta_file_name = "metafile_status.json"
    if os.path.exists(meta_file_name):
        with open(meta_file_name, "r") as meta_file:
            data = json.load(meta_file)
            
        res = []
        for key, value in data.items():
            res.append((key, value["description"], value["downloaded"]))
            
        return res
    
    return []
    
if __name__ == "__main__":
    print("Client::test")
            
            