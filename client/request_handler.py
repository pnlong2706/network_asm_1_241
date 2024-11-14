import socket
import threading
import json
import os
import math

with open('metafile_status.json', 'r') as file:
    metadata = json.load(file)

def request_handler(conn, addr):
    data = conn.recv(4096)
    
    if not data:
        conn.close()
        return
    
    if(data[0] == 19 and data[1:20] == b'BitTorrent protocol'):
        infohash = data[28:68].decode()
        
        metafile = metadata[infohash]
        conn.sendall(b"\x13BitTorrent protocol")
        
        bitfield = metafile["piece_have"]
        lenB = len(bitfield) + 1

        bitfield_mess = (
            int(lenB).to_bytes(4) +
            int(5).to_bytes(1) +
            bitfield.encode()
        )
        
        conn.sendall(bitfield_mess)
    
    elif data[4] == 6:
        piece_id = int.from_bytes(data[5:9])
        infohash = data[9:49].decode()
        metafile = metadata[infohash]
                
        filepath = ""
        max_num_piece = 0
        for file in metafile["info"]["files"]:
            prv_num_piece = max_num_piece
            max_num_piece += math.ceil(file["length"] / metafile["info"]["piece_length"])
            if(max_num_piece > piece_id): 
                offset = piece_id - prv_num_piece
                filepath = file["path"]
                break
                
        ff = open(os.path.join("file", filepath), "rb")
        ff.seek(offset * metafile["info"]["piece_length"])
        result = ff.read(metafile["info"]["piece_length"])
        
        conn.send(result)
    else:
        conn.send(b"\x06Refuse")
            


def start_handling_request(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen()
    
    try:
        while True:
            conn, addr = server_socket.accept()
            thread = threading.Thread(target=request_handler, args=(conn, addr))
            thread.start()
            
    except KeyboardInterrupt as e:
        print("End")
    finally:
        server_socket.close()
        if(conn):
            conn.close()
            
if __name__ == "__main__":
    start_handling_request("127.0.0.1", 3000)