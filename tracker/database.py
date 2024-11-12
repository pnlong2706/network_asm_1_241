import  psycopg2
    
conn = psycopg2.connect(database = "neondb", 
                        user = "neondb_owner", 
                        host= 'ep-lucky-band-a55plt4v.us-east-2.aws.neon.tech',
                        password = "mxCvR9T0OboZ",
                        port = 5432)

cur = conn.cursor()

def update_peerfile(infohash, peerid, addr, port, downloaded):
    cur.execute(f"SELECT * FROM metafile WHERE infohash = '{infohash}'")
    re = cur.fetchall()
    
    if(len(re)==0):
        return
    
    cur.execute(f"INSERT INTO peerfile (infohash, peerid, peeraddr, peerport, downloaded) VALUES ('{infohash}', '{peerid}', '{addr}', {port}, {downloaded})")
    conn.commit()

def get_peer(infohash):
    cur.execute(f"SELECT peerid, peeraddr, peerport FROM peerfile WHERE infohash = '{infohash}'")
    rows = cur.fetchall()
    return rows

def delete_peer(peerid, addr, port):
    cur.execute(f"DELETE FROM peerfile WHERE peerid = '{peerid}' AND peeraddr = '{addr}' AND peerport = '{port}'")
    conn.commit()
    
def update_metafile(name, infohash, description):
    cur.execute(f"INSERT INTO metafile (name, infohash, description) VALUES ('{name}', '{infohash}', '{description}'")
    conn.commit()
    
if __name__ == "__main__":
    update_peerfile("anan221r5naan", "uytuyiuac", "127.0.0.1", 3000)
    print("Done")
    