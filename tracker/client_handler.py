from database import (
    update_peerfile,
    get_peer,
    delete_peer,
    update_metafile
)

import json
import hashlib

def client_handler(conn, addr):
    try:
        while(True):
            data = conn.recv(4096).decode()
            if not data:
                break
            
            print("Recv: ", data)
            cmd = json.loads(data)
            
            if cmd['action'] == 'update' and cmd['event'] == 'started':
                for file in cmd['infohash']:
                    update_peerfile(
                        infohash= file['hash'],
                        peerid= cmd['peerid'],
                        addr= addr[0],
                        port= cmd['port'],
                        downloaded= file['downloaded']
                    )
                    
                conn.sendall(b"Update successfully")
                    
            elif cmd['action'] == 'get-peer':
                result = get_peer(cmd['infohash'])
                peer_list = []
                
                for peer in result:
                    peer_list.append({
                        "peerid": peer[0],
                        "addr": peer[1],
                        "port": peer[2]
                    })
                    
                print(peer_list)
                
                conn.sendall(json.dumps({"result": peer_list}).encode())
            
            elif cmd['action'] == 'download' and cmd['event'] == 'start':
                update_peerfile(
                    infohash=cmd['infohash'],
                    peerid=cmd['peerid'],
                    addr=addr[0],
                    port=cmd['port'],
                    downloaded=cmd['downloaded']
                )
            
            elif cmd['action'] == 'upload':
                
                sha1_hash = hashlib.sha1(cmd["info"]).hexdigest()
                
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
 
                # Writing to sample.json
                with open(sha1_hash + ".json", "w") as outfile:
                    outfile.write(json_object)
                
            elif cmd['event'] == 'stop':
                delete_peer(
                    peerid= cmd['peerid'],
                    addr= addr[0],
                    port=cmd['port']
                )
                
                break
            
    except Exception as e:
        print(f"An error occurred while handling client {addr}: {e}")
    finally:
        conn.close()
        print(f"Connection with {addr} has been closed.")