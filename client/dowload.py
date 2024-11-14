import pickle
import os
import struct

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