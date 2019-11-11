from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
from time import sleep

# Minha classe responsável pela interface e pelo tratamento das mensagens
from display import Display

# Minha classe responsável pela codificação da mensagem com base no protocolo
from protocolo import codifica


# Classe que faz a interface com o servidor
class Servidor(Thread):
    def __init__(self, clientSocket, display):
        super().__init__()
        self.vivo = True
        self.cSocket = clientSocket
        self.display = display
        self.listaDeMensagens = display.listaDeMensagens

    def mataThread(self):
        self.vivo = False
        self.cSocket.close
        self.display.mataThread()

    def run(self):
        while self.vivo:
            bMensagem = self.cSocket.recv(1024)
            if bMensagem == b'':
                self.mataThread()
                print('\033[0m\nO servidor caiu! Pressione qualquer tecla para sair')
            else:
                self.listaDeMensagens.append(bMensagem)
                # comando que o servidor envia para forçar a desconexão
            if display.trataMensagem(bMensagem).get('comando') == 'encerrar':
                sleep(0.1)
                self.mataThread()


# definicao das variaveis
serverName = 'localhost'  # ip do servidor
serverPort = 65000  # porta a se conectar
clientSocket = socket(AF_INET, SOCK_STREAM)  # criacao do socket TCP
clientSocket.connect((serverName, serverPort))  # conecta o socket ao servidor

# Cria e inicia a thread do display
display = Display()
display.start()

# login...
apelido = ''
while apelido == '':  # Enquanto o apelido fornecido não estiver disponível...
    # Recebe mensagem de aviso
    display.listaDeMensagens.append(
        clientSocket.recv(1024))
    # Manda o apelido. Quando o apelido é '', o codificador retorna uma mensagem com o comando 'apelido!'
    clientSocket.send(codifica('', display.entrada.getEntrada()))
    # Atribui a apelido recebido do servidor em caso de sucesso ou '' em caso de falha
    apelido = display.trataMensagem(clientSocket.recv(1024)).get('mensagem')
    # Tira a última mensagem enviada pelo servidor da lista de mensagens do display
    display.listaDeMensagens.pop(0)

# Cria e inicia a thread responsável por receber as mensagens do servidor independetemente
servidor = Servidor(clientSocket, display)
servidor.start()

# Enquando o usuário não pedir pra sair, fica mandando quantas mensagens o usuário quiser...
mensagem = ''
while mensagem.find('sair()') == -1:
    mensagem = display.entrada.getEntrada()
    clientSocket.send(codifica(apelido, mensagem))

# Encerra as threads e a conexão com o servidor
servidor.mataThread()
print('\033[0m')  # printa uma nova linha
