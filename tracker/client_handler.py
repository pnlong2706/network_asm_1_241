

def client_handler(conn, addr):
    try:
        while(True):
            data = conn.recv(4096).decode()
            if not data:
                break
            
            print("Recv: ", data)
            if(data == "exit"):
                break
            
    except Exception as e:
        print(f"An error occurred while handling client {addr}: {e}")
    finally:
        conn.close()
        print(f"Connection with {addr} has been closed.")