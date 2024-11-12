import  psycopg2
    
conn = psycopg2.connect(database = "neondb", 
                        user = "neondb_owner", 
                        host= 'ep-lucky-band-a55plt4v.us-east-2.aws.neon.tech',
                        password = "mxCvR9T0OboZ",
                        port = 5432)

def hello():
    cur = conn.cursor()
    
    #cur.execute("INSERT INTO metafile (name, infohash, description) VALUES ('catto', 'njajnvsknanksnkjj', 'Cute cate pic')")
    #conn.commit()
    
    cur.execute("SELECT * FROM metafile")
    rows = cur.fetchall()
    
    print(rows[0])