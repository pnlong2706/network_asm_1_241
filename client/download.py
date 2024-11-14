import pickle
import os
import json
import struct
import socket
import random
import hashlib
import math
from concurrent.futures import ThreadPoolExecutor

def create_handshake(info_hash, peer_id):
    """Tạo gói tin handshake theo giao thức BitTorrent"""
    pstr = "BitTorrent protocol"
    pstrlen = len(pstr)
    reserved = b'\x00' * 8
    
    handshake = (
        bytes([pstrlen]) +
        pstr.encode() +
        reserved +
        info_hash.encode() +
        peer_id.encode()
    )
    return handshake    

def download_from_peers(info_hash, client_id, peers):
    with open('metafile_status.json', 'r') as file:
        data = json.load(file)
        
    metafile = data[info_hash]
    piece_have = list(metafile["piece_have"])
    total_length = 0
    num_piece = 0
    piece_to_peer = []
    
    for file in metafile["info"]["files"]:
        if(not os.path.exists(os.path.join("file", file["path"]))):
            with open(os.path.join("file", file["path"]), "wb") as out:
                out.seek(file["length"]-1)
                out.write(b'\0')
                
        total_length += file["length"]
        piece_to_peer += ([(file["path"], i, []) for i in range( math.ceil(file["length"] / metafile["info"]["piece_length"]) )])
        num_piece += math.ceil(file["length"] / metafile["info"]["piece_length"])
    
    peer_conn = {}
    for peer in peers: peer_conn[peer['peerid']] = (0, 0, 0)
    
    def connect_to_peer(peerid, addr, port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((addr, port))
            s.sendall(create_handshake(info_hash, client_id))
            res = s.recv(4096)
            
            if(res and res[0] == 19 and res[1:20] == b'BitTorrent protocol'):
                res = s.recv(4096) ## receive bitfield
                if(res[4] == 5):
                    len_bit = int.from_bytes(res[0:4]) - 1
                    bitfiled = res[5:(5+len_bit)].decode()
                    peer_conn[peerid] = (bitfiled, addr, port)
                    
            s.close()
        except Exception as e:
            print(f"Cannot connect to peer {peerid}")
        
                
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(connect_to_peer, [peer["peerid"] for peer in peers], [peer["addr"] for peer in peers], [peer["port"] for peer in peers])
    
    ## Process mapping
    for peer_id, (bit, addr, port) in peer_conn.items():
        if not addr: continue
        
        # piece to (peerid, file)
        for i in range(num_piece):
            if(bit[i] == '1' and piece_have[i] != '1'):
                piece_to_peer[i][2].append(peer_id)
    
    for i in range(num_piece):
        random.shuffle(piece_to_peer[i][2])
    
    def request_and_save_piece(piecenum, filename, offset, peers, peer_conn):    
        if(piece_have[piecenum] == '1'): return True
        for i in range(len(peers)):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((peer_conn[peers[i]][1], peer_conn[peers[i]][2]))
            
            request_mess = (
                int(5).to_bytes(4) +
                int(6).to_bytes(1) +
                int(piecenum).to_bytes(4) +
                info_hash.encode()
            )
            
            s.send(request_mess)
            res = s.recv(1048576)
            
            ## Check hash !!
            sha1_hash = hashlib.sha1(res).digest().hex()
            sha1_hash_true = metafile["info"]["pieces"][piecenum * 40: (piecenum+1)*40]
            
            if(sha1_hash_true == sha1_hash):
                ff = open(os.path.join("file", filename), "r+b")
                ff.seek(offset * metafile["info"]["piece_length"])
                ff.write(res)
                ff.close()
                
                print(f"Successfully download piece {piecenum} belong to {filename} from peer {peers[i]}")
                
                piece_have[piecenum] = '1'
                s.close()
                return True
            else:
                s.close()
                continue
            
        return False
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        result = list(executor.map(request_and_save_piece, 
                        [i for i in range(num_piece)],
                        [piece_to_peer[i][0] for i in range(num_piece)], 
                        [piece_to_peer[i][1] for i in range(num_piece)], 
                        [piece_to_peer[i][2] for i in range(num_piece)],
                        [peer_conn for i in range(num_piece)]
                    ))
    
    
    data[info_hash]["piece_have"] = "".join(piece_have)
    
    with open("metafile_status.json", "w") as meta_file:
        json.dump(data, meta_file, indent=4)

        
if __name__ == "__main__":
    download_from_peers("b9c671194183d8a464df7a0a57394736084e1ffb", "NIAIOAC134", [{'peerid': 'WA6P1HLZ5T', 'addr': '127.0.0.1', 'port': 3000}])
