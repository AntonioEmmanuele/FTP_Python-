import socket
import ast
import os
from socket import error
import errno
class Server:
    def __init__(self,Controll_Port,Data_Port):# inizializza la socket del server
        self.Controll_Port=Controll_Port
        self.Data_Port=Data_Port
        self.Controll_Socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.Controll_Socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)#Setto le opzioni in maniera tale che riusi
        #una socket nello stato di time wait
        self.Controll_Socket.bind((socket.gethostbyname(socket.gethostname()),socket.htons(self.Controll_Port)))
    def Connect(self):# connettiti
        self.Controll_Socket.listen(3)
        self.Client_Controll_Socket,self.new_controll_addresses=self.Controll_Socket.accept()
    def Create_Data_Socket(self):
        self.Data_Sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.Data_Sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.Data_Sock.bind((socket.gethostbyname(socket.gethostname()),socket.htons(self.Data_Port)))
        self.Data_Sock.listen(3)
        self.Client_Data_Socket,self.client_addr=self.Data_Sock.accept()
        self.Client_Data_Socket.send("Data Connection established".encode())
    def User_Password(self):
        self.Client_Controll_Socket.send("USR".encode())
        rcv_name=self.Client_Controll_Socket.recv(128)
        rcv_name=str(rcv_name.decode()).strip()#Rimuove elementi vuoti tra inizio e fine
        self.Client_Controll_Socket.send("PASS".encode())
        rcv_password=self.Client_Controll_Socket.recv(128)
        rcv_password=str(rcv_password.decode()).strip()#Rimuove elementi vuoti tra inizio e fine
        file2=open("file_list.txt","r")# prende le liste da un file
        number=file2.readline()
        #print("The number of lists is ", number)
        check=0
        for i in range(2,int(number)+2):
            #print(i)
            my_list=ast.literal_eval(file2.readline())# devo ottenere una lista con username e password
            #print(my_list[0],my_list[1])
            if(my_list[0]==rcv_name and my_list[1]==rcv_password):
                #print("FIND \n ")
                check=1
            #print(" In the cicle ",i , " The value of check is ",check)
        if check==0:
            print(" Must close connection, Unknown client , name and passwords are ",rcv_name,rcv_password)
            self.Client_Controll_Socket.send("Connection Refused".encode())
            self.Client_Controll_Socket.close()# chiudo la connessione se non trovo la passwod nel server
        elif check==1:
            self.Client_Controll_Socket.send("Connection Accepted".encode())
            print(" Connection Accepted ")
            self.Create_Data_Socket()
    def Terminate(self):
        self.Client_Controll_Socket.close()
        self.Controll_Socket.close()
        self.Client_Data_Socket.close()
        self.Data_Sock.close()
    def RETR(self,filename):
        print(" Executing Retrieve command \n")
        dim=os.stat(filename).st_size #divide il file in pezzi da 1024 bytes
        self.Client_Controll_Socket.send(str(dim).encode())#invia sulla controll socket la dimensione del file
        print("The name of the file and the dim are ",filename,"   ",dim)
        if dim<=1024: # se e' minore allora invia direttamente
            print("Sent ",dim)
            buf=open(filename,"r")
            self.Client_Data_Sock.send(str(buf.read(dim)).encode())#invia sulla data sock il file
        elif dim>1024:
            if dim%1024==0:#Se è divisibile
                num=dim/1024# dividi in num parti, queste num_parti avranno tutte dimensioni intere ,
                #uso infatti con tranq / che mi da il resto
                buf=open(filename,"r","ascii")
                for i in range(0,num):
                    self.Client_Data_Socket.send(str(buf.read(1024)).encode())# invio num pacchetti di 1024 bytes
            else :
                num=dim//1024+1# divisione senza resto ed aggiungo uno per sovradimensionare
                buf=open(filename,"r")
                for i in range (0, num):
                    self.Client_Data_Socket.send(str(buf.read(1024)).encode())
    def QUIT(self):
        self.Client_Controll_Socket.close()
        self.Controll_Socket.close()
        self.Client_Data_Socket.close()
        self.Data_Sock.close()
        exit(0)
    def STR(self,filename): # Essenzialmente la funzione list del client
        print ("Receive STR Command ")
        try:
            read=self.Client_Controll_Socket.recv(1024)#Attendi la dimensione
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
        self.Client_Controll_Socket.send("DIM_ACK".encode())
        number_of_bytes=int(read.decode().strip()) #Attendo la dimensione del file
        buf=open(filename,"w")
        print("The dimension of the file and the name are  ",number_of_bytes,"  ",filename, "\n ")
        if number_of_bytes<=1024: # primo caso
            rcv=self.Client_Data_Socket.recv(number_of_bytes)
            buf.write(rcv.decode())
        elif number_of_bytes>1024:
            if number_of_bytes%1024==0:#nel caso in cui il numbero di bytes sia divisibile per 1024
                n=number_of_bytes/1024
                for i in range(0,n):
                    rcv=self.Client_Data_Socket.recv(1024)
                    buf.write(rcv.decode())
            else :
                n=number_of_bytes//1024+1
                for i in range(0,n):
                    rcv=self.Client_Data_Socket.recv(1024)
                    if i!=(n-1):
                        buf.write(rcv.decode())
                    else:
                        buf.write(rcv.decode().strip())#nel caso in cui sia l'ultimo avremmo info aggiuntive inutili
                        #le taglio


    def Wait_For_Commands(self):
        #end=0
        while 1:
            command=self.Client_Controll_Socket.recv(8)
            print("The command received is ",str(command.decode()).strip(),"\n ")
            self.Client_Controll_Socket.send("CR".encode())# Mando un command Received, funziona come un ack
            if str(command.decode()).strip()=="QUIT":
                #end=1
                self.QUIT()
            elif str(command.decode()).strip()=="RETR":
                filename=self.Client_Controll_Socket.recv(256)
                print("Filename received ",str(filename.decode()).strip())
                self.RETR(filename=str(filename.decode()).strip())
            elif str(command.decode()).strip()=="STR":
                filename=self.Client_Controll_Socket.recv(256)
                print("Filename received ",str(filename.decode()).strip())
                self.Client_Controll_Socket.send("F_ACK".encode())#Uso multipli ack in questo caso
                self.STR(filename=str(filename.decode()).strip())


My_Server=Server(Controll_Port=29987,Data_Port=29989)
My_Server.Connect()
My_Server.User_Password()
My_Server.Wait_For_Commands()
#My_Server.Terminate()
