from database import (
    update_peerfile,
    get_peer,
    delete_peer,
    update_metafile,
    search_by_keyword,
    add_peer,
    add_file_downloaded
)

import json
import hashlib
import os

def client_handler(conn, addr, tracker_addr):
    try:
        while(True):
            data = conn.recv(262144).decode()
            if not data:
                break
            
            print("Recv: ", data, "\n")
            cmd = json.loads(data.split("\r\n\r\n")[1])
            
            if cmd['action'] == 'update' and cmd['event'] == 'started':
                for file in cmd['infohash']:
                    update_peerfile(
                        infohash= file['hash'],
                        peerid= cmd['peerid'],
                        addr= addr[0],
                        port= cmd['port'],
                        downloaded= file['downloaded']
                    )
                    
                add_peer(addr[0], cmd['port'])
                conn.sendall(b"Update successfully")
                    
            elif cmd['action'] == 'get-peer':
                result = get_peer(cmd['infohash'])
                peer_list = []
                
                for peer in result:
                    if(peer[0] == cmd["id"]): continue 
                    peer_list.append({
                        "peerid": peer[0],
                        "addr": peer[1],
                        "port": peer[2]
                    })
                    
                    if len(peer_list) >= 20: break
                
                conn.sendall(json.dumps({"status": "success", "tracker_id": tracker_addr, "peers": peer_list}).encode())
            
            elif cmd['action'] == 'download' and cmd['event'] == 'started':
                update_peerfile(
                    infohash=cmd['infohash'],
                    peerid=cmd['peerid'],
                    addr=addr[0],
                    port=cmd['port'],
                    downloaded=cmd['downloaded']
                )
                
                conn.sendall(json.dumps({"status": "success"}).encode())
                
            elif cmd['action'] == 'download' and cmd['event'] == 'completed':
                update_peerfile(
                    infohash=cmd['infohash'],
                    peerid=cmd['peerid'],
                    addr=addr[0],
                    port=cmd['port'],
                    downloaded=cmd['downloaded']
                )
                
                add_file_downloaded(addr[0], cmd['port'])
                conn.sendall(json.dumps({"status": "success"}).encode())
                
            elif cmd['action'] == "search":
                result = search_by_keyword(cmd['keyword'])
                conn.sendall(json.dumps({"status": "success", "tracker_id": tracker_addr, "result": result}).encode())
                
            elif cmd['action'] == 'get-torrent':
                infohash = cmd['infohash']
                filepath = os.path.join("metafile", infohash + ".json")
                if os.path.exists(filepath):
                    with open(filepath, 'r') as file:
                        metadata = json.load(file)
                        
                    conn.sendall(json.dumps({"status": "success", "tracker_id": tracker_addr, "result": metadata}).encode())
                else:
                    conn.sendall(json.dumps({"status": "fail", "failure_reason": "cannot find this torrent"}).encode())
            
            elif cmd['action'] == 'publish':
                sha1_hash = hashlib.sha1(json.dumps(cmd["info"]).encode('utf-8')).hexdigest()
                                
                update_metafile(
                    name=cmd['info']['name'],
                    infohash=sha1_hash,
                    description=cmd['description']
                )
                
                update_peerfile(
                    infohash=sha1_hash,
                    peerid=cmd['peerid'],
                    addr=addr[0],
                    port=cmd['port'],
                    downloaded=cmd['downloaded']
                )
                
                json_object = json.dumps({"info": cmd["info"], "description": cmd["description"]})

                with open(os.path.join("metafile", sha1_hash + ".json"), "w") as outfile:
                    outfile.write(json_object)
                    
                conn.sendall(json.dumps({"status": "success"}).encode())
                
            elif cmd['event'] == 'stopped':
                break
            
    except Exception as e:
        print(f"An error occurred while handling client {addr}: {e}")
        conn.sendall(json.dumps({"status": "error", "failure_reason": e}).encode())
    
    finally:
        delete_peer(
                peerid= cmd['peerid'],
                addr= addr[0],
                port=cmd['port']
            )
        
        if conn: conn.close()
        print(f"Connection with {addr} has been closed.")