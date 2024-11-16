# Simple Like-torrent application (2024 HCMUT Compter Network Assignment)

## Overview 

This is a Simple Like-torrent application with application protocols defined by each group, using the TCP/IP protocol stack. 
The application consists of:
-  A centralized server keeps track of which clients are connected and storing what pieces of 
files.  
- Through tracker protocol, a client informs the server as to what files are contained in its local 
repository but does not actually transmit file data to the server. 
- When a client requires a file that does not belong to its repository, a request is sent to the 
server. 
- Multiple clients could be downloading different files from a target client at a given point in 
time. This requires the client code to be multithreaded

![Screenshot 2024-11-16 165714](https://github.com/user-attachments/assets/3df37f39-2c2b-4b9d-aa9a-4574070e1268)

## Requirements

- Python 3 (version > 3.11.4)
- PostgreSQL database. Host on your machine or other host server.

Note: In the code, we use the Neon serverless Postgres platform for the database. You can see this in tracker/database.py. The host inside database.py is owned by us, it's free and gives you about 0.5 GB storage limit.
You can use our database to test this application as long as it's still alive. The database structure is provided in the document.

You may have to install ```psycopg2``` library and other libraries if needed.

## Installation

You just have to clone this repository:
```
git clone https://github.com/pnlong2706/network_asm_1_241.git
cd network_asm_1_241
```

## Usage

You can test our application on a single computer or in a group of peers who share the same local network.

### For testing on a single computer

1. Go to the tracker folder and run main.py:
```
cd tracker
py main.py
```
2. Open another terminal, go to the client, and run main.py
```
cd client
py main.py
```
3. Clone folder client to client1, go to client1, and run main, similar to 2, but change the listen port by passing it into -lp argument.
```
cd client
py main.py -lp 3001
```
4. Now you have 2 peers connected to the tracker server through localhost, you can start by entering the command in the command line on the client side. You can type help to see details of each command.

### For using the application in a group of peers

1. Make sure you and your friends are connected to the same local network and set this network as your private network on all of your computers.
2. Go to the tracker folder and run main.py, but bind the host as your IPv4 address.
```
cd tracker
py main.py [--host SERVER_IPv4]
```
3. For the client, change the default server host, and your host as your IPv4. Of course, you can change your listen port if you want:
```
cd client
py main.py [--server_host SERVER_IPv4] [--host YOUR_IPv4] 
```

### Client usage

All of the commands:
1. ```connect [hostname] [port]``` : Connect to the tracker server by providing the hostname and port.
2. ```exit``` : Exit application.
3. ```create``` : Create a new torrent file, after entering 'create', you'll have to enter a name, files, piece_length, and description of your torrent. You will receive an infohash for this torrent
4. ```publish [infohash]``` : Publish your torrent file, you'll become the first seeder for this torrent if the tracker doesn't have this torrent. you can enter only 'publish', then you can create a torrent file and upload it at the same time.
5. ```search [keyword]``` : Search for available torrents that the tracker has.
6. ```get_torrent [infohash]``` : Get a torrent file from the tracker server by infohash.
7. ```my_torrent``` : See all of your torrents.
8. ```download [infohash]``` : Download all files of a torrent, you must have this torrent file in my_torrent first. In case there are not enough seeders, the download may only be partly complete.

You can see the details and examples in the document.

## Demo:

There is a simple example for this application:

Initially, the client had cat1.png and cat2.png, the client2 had img1.png, img2.png, text1.txt, text2.txt and glove.6B.50d.txt.

![image](https://github.com/user-attachments/assets/8a78fa1b-2396-4942-89eb-37487d854c1b)

Then, client2 creates a torrent file consisting of img1.png and text1.txt. Client2 publishes it to the tracker server.

![image](https://github.com/user-attachments/assets/1a0858fd-5c7c-4bd3-bca7-538d10e8a081)

Then, the client searches it by keyword client2 and receives the info hash of that torrent file client2 created. The client gets that torrent and downloads it from client2.

![image](https://github.com/user-attachments/assets/76cd7477-5b28-4c6f-8997-4fc0f31f8fb9)

After downloading successfully, the client now has img1.png and text1.txt in the folder file.

![image](https://github.com/user-attachments/assets/d508e662-cd7a-495d-b437-c366f6dd4ecd)

The download log:

![image](https://github.com/user-attachments/assets/931a11e4-773a-405a-8400-ebc4a09135c0)

The upload log of client2:

![image](https://github.com/user-attachments/assets/8fe2f1e8-ca21-4adc-aa64-b6aac7a5e6b7)


## Bugs and limit

There are still some bugs and limits:

-  The database server is not working after some amount of time.
-  KeyboardInterupt can not stop tracker process.
-  We can only download files that are less than 5GB, we can increase this limit but we think it's good enough for simple applications.
-  The application may not be compatible with a lower Python version.

## Contributor

-  Pham Ngoc Long - 2211894 (K22 CSE-HCMUT)
-  Nguyen Quang Huy - 2211235 (K22 CSE-HCMUT)
-  Vo Phuong Minh Nhat - 2212413 (K22 CSE-HCMUT)

