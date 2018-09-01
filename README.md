# remote-it-tool
The remote IT tool is meant to help the IT guy remotely access the rest of the computers in the lab, or simply for lazy people who don't want to get up from their chair every time they need something from another computer within their LAN.

## How it works
Just simply run the server code on one host (your computer), and put the client code on every host you want remote access to, and run it as well.

The server is not meant to be shut down and neither the clients, just run the program one time and stay connected.

## The features
  * Multi client compatibility, meaning the server can manage number of sessions at the same time.
  * Screenshot - take a screenshot of the client's screen.
  * Download - browse the client's directory tree and double click to download a file from the client to the server.
  * Upload - select a file to send from the server to the client.
  * Shell - "open" a cmd in the client's computer and communicate with it. (the client can't see the cmd window)
  * Shutdown - shutdown the client's computer.
  * Restart - restart the client's computer.
  
## Additional required modules
* PIL
  
  ```pip install pillow```

### Things to add in the future
  * Encrypted communication between the server and the clients.
  * An option to get the current open tabs in the browser.
  * Deleting a client from the clients list in case the program was closed on the client.
  * Automatically running the program on startup.
   
