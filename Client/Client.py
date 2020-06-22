import socket
from socket import error
import errno
import os
class Client:
    def __init__(self,Id,Password,Server_Ip,Server_Port,Data_Port):
        self.Id=Id
        self.Password=Password
        self.Server_IP=Server_Ip
        self.Data_Port=Data_Port
        self.Server_Port=Server_Port
        self.Controll_Socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.Controll_Socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)#Setto le opzioni in maniera tale che riusi

    def Create_Data_Sock(self):
        self.Data_Socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.Data_Socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)#Setto le opzioni in maniera tale che riusi
        if self.Server_IP==socket.gethostbyname(socket.gethostname()):
            self.Data_Socket.connect((self.Server_IP,socket.htons(self.Data_Port)))
        welcome=self.Data_Socket.recv(1024)
        if str(welcome.decode()).strip()=="Data Connection established":
            print(str(welcome.decode()).strip())
        else:
            print(" Something has gone wrong ")
            self.Data_Socket.close()
            self.Controll_Socket.close()
            exit(1)
    def Connect_To_Server(self):
        self.Controll_Socket.connect((self.Server_IP,socket.htons(self.Server_Port)))
        #Attendi per comando user
        buff=self.Controll_Socket.recv(128)
        if buff.decode().strip()=="USR":
            self.Controll_Socket.send(self.Id.encode())
        else:
            print(" Error connecting to server \n ")
            self.Controll_Socket.close()
            exit(1)
        buff=self.Controll_Socket.recv(128)
        if buff.decode().strip()=="PASS":
            self.Controll_Socket.send(self.Password.encode())
        else:
            print(" Error connecting to server \n ")
            self.Controll_Socket.close()
            exit(1)
        buff=self.Controll_Socket.recv(1024)
        if str(buff.decode()).strip()=="Connection Accepted":
            print(str(buff.decode()).strip())
            self.Create_Data_Sock()
        else:
            print(str(buff.decode()).strip())
            self.Controll_Socket.close()
            exit(1)
    def Terminate(self):
        self.Controll_Socket.close()
        self.Data_Socket.close()
    def RETR(self,filename):
        print("Sending retrieve Command \n ")
        self.Controll_Socket.send("RETR".encode())#invia il comando
        ack=self.Controll_Socket.recv(2)
        if str(ack.decode()).strip()=="CR": # aspetto ack perche' altrimenti mando due send consecutive
            print("RETR ack")
        self.Controll_Socket.send(filename.encode())#invia nome del file

        try:
            read=self.Controll_Socket.recv(1024)#Attendi la dimensione
            # Il motivo per cui mi dava errore era che non avevo aspettato alcun ack di conferma del comando ed al server non arrivava mai il file name
            #INVIAVO DUE SEND CONSECUTIVE
        except error as e:
            if e.errno!=errno.ECONNRESET:#Se non ho quello specifico errore
                raise #fai propagare la nuova eccezione
            else:
                print("Connection was resetted \n ")
                print("Trying again \n ")
                #self.Controll_Socket.send("Again".encode())
                #read=self.Controll_Socket.recv(1024)
                #print(read.decode().strip())
                exit(1)

        number_of_bytes=int(read.decode().strip()) #Attendo la dimensione del file
        buf=open(filename,"w")
        print("The dimension of the file and the name are  ",number_of_bytes,"  ",filename, "\n ")
        if number_of_bytes<=1024: # primo caso
            rcv=self.Data_Socket.recv(number_of_bytes)
            buf.write(rcv.decode())
        elif number_of_bytes>1024:
            if number_of_bytes%1024==0:#nel caso in cui il numbero di bytes sia divisibile per 1024
                n=number_of_bytes/1024
                for i in range(0,n):
                    rcv=self.Data_Socket.recv(1024)
                    buf.write(rcv.decode())
            else :
                n=number_of_bytes//1024+1
                for i in range(0,n):
                    rcv=self.Data_Socket.recv(1024)
                    if i!=(n-1):
                        buf.write(rcv.decode())
                    else:
                        buf.write(rcv.decode().strip())#nel caso in cui sia l'ultimo avremmo info aggiuntive inutili
                        #le taglio
    def QUIT(self):
        print("Sending QUIT Command \n ")
        self.Controll_Socket.send("QUIT".encode())#invia il comando
        ack=self.Controll_Socket.recv(2)
        if str(ack.decode()).strip()=="CR": # aspetto ack perche' altrimenti mando due send consecutive
            print("QUIT ack")
        self.Controll_Socket.close()
        self.Data_Socket.close()
        exit(0)
    def STR(self,filename):
        print(" Sending STR command \n")
        self.Controll_Socket.send("STR ".encode())#invia il comando
        ack=self.Controll_Socket.recv(2)
        if str(ack.decode()).strip()=="CR": # aspetto ack perche' altrimenti mando due send consecutive
            print("STR ACK \n ")
        self.Controll_Socket.send(filename.encode())# Invia il file name
        file_ack=self.Controll_Socket.recv(128)
        if str(file_ack.decode()).strip=="F_ACK":
            print( "Filename acked \n ")
        dim=os.stat(filename).st_size #divide il file in pezzi da 1024 bytes
        self.Controll_Socket.send(str(dim).encode())#invia sulla controll socket la dimensione del file
        dim_ack=self.Controll_Socket.recv(128)
        if str(dim_ack.decode()).strip()=="DIM_ACK":
            print("Dimension Acked ")
        if dim<=1024: # se e' minore allora invia direttamente
            print("Sent ",dim)
            buf=open(filename,"r")
            self.Data_Sock.send(str(buf.read(dim)).encode())#invia sulla data sock il file
        elif dim>1024:
            if dim%1024==0:#Se è divisibile
                num=dim/1024# dividi in num parti, queste num_parti avranno tutte dimensioni intere ,
                #uso infatti con tranq / che mi da il resto
                buf=open(filename,"r","ascii")
                for i in range(0,num):
                    self.Data_Socket.send(str(buf.read(1024)).encode())# invio num pacchetti di 1024 bytes
            else :
                num=dim//1024+1# divisione senza resto ed aggiungo uno per sovradimensionare
                buf=open(filename,"r")
                for i in range (0, num):
                    self.Data_Socket.send(str(buf.read(1024)).encode())

My_Client=Client(Id="AntonioEmmanuele",Password="123stella",Server_Ip=socket.gethostbyname(socket.gethostname()),Server_Port=29987,Data_Port=29989)
My_Client.Connect_To_Server()
My_Client.RETR(filename="Test.txt")
My_Client.STR(filename="Test2.txt")
My_Client.QUIT()
