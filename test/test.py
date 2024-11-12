import os
import random

ori_file = "img1.png"
des_file = "img2.png"
chunk_size = 1024

if(not os.path.exists(des_file)):
    sz = os.path.getsize(ori_file)
    with open(des_file, "wb") as out:
        out.seek(sz-1)
        out.write(b'\0')
    
byteLs = []
with open(ori_file, "rb") as f:
    i = 0
    while(True):
        a = f.read(chunk_size)
        if(not a):
            break
        
        byteLs.append((a, i))
        i += 1
        
random.shuffle(byteLs)
ff = open(des_file, "r+b")

# print(len(byteLs[0][0]))
# print(byteLs[0][0][0:4])
# print(byteLs[0][0][0], byteLs[0][0][1], byteLs[0][0][2], byteLs[0][0][3])

for piece in byteLs:
    ff.seek(piece[1]*chunk_size)
    ff.write(piece[0])
    
ff.close()