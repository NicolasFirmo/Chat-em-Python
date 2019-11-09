from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, timeout
from threading import Thread

# Minha classe responsável pela interface e pelo tratamento das mensagens
from display import Display, sleep

# Minha classe responsável pela codificação da mensagem com base no protocolo
from protocolo import codifica


class Usuario(Thread):
    def __init__(self, apelido, socket, addr, listaDeMensagens):
        super().__init__()
        self.vivo = True
        self.apelido = apelido
        self.sSocket = socket
        self.addr = addr
        self.listaDeMensagens = listaDeMensagens
        self.sSocket.settimeout(0.1)

    def mataThread(self):
        self.vivo = False
        self.sSocket.close()
        sleep(0.1)

    def run(self):
        while self.vivo:
            try:
                bMensagem = self.sSocket.recv(1024)
            except timeout:
                continue
            except OSError:
                continue
            comando = display.trataMensagem(bMensagem).get("comando")
            if comando == '   todos':
                sendBroadcast(bMensagem)
                self.listaDeMensagens.append(bMensagem)
            elif comando == '    sair':
                sendBroadcast(bMensagem)
                self.listaDeMensagens.append(bMensagem)
                self.mataThread()
                listaDeUsuarios.remove(self)
            elif comando == 'privado?':
                sendPrivado(self, bMensagem)
            elif comando == '  lista?':
                sendLista(self)
            else:
                self.sSocket.send(bMensagem)


# definicao das variaveis e funções
serverName = ''  # ip do servidor (em branco)
serverPort = 65000  # porta a se conectar
serverSocket = socket(AF_INET, SOCK_STREAM)  # criacao do socket TCP
# bind do ip do servidor com a porta
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.bind((serverName, serverPort))
serverSocket.listen(1)  # socket pronto para 'ouvir' conexoes
print('Servidor TCP esperando conexoes na porta %d ...' % (serverPort))

listaDeUsuarios = []

# Inicia o diplay
display = Display()
display.start()


# Manda a mensagem recebida para todos os usuários logados e para o display do servidor
def sendBroadcast(bMensagem):
    for usuario in listaDeUsuarios:
        usuario.sSocket.send(bMensagem)


# Manda a mensagem recebida para todos os usuários logados e para o display do servidor
def sendPrivado(origem, bMensagem):
    mensagem = display.trataMensagem(bMensagem).get('mensagem')
    apelido = mensagem[1:mensagem.find(')')]
    mensagem = mensagem[mensagem.find(')')+1:]

    presente = False
    for usuario in listaDeUsuarios:
        if usuario.apelido == apelido:
            presente = True
            break

    if presente:
        bMensagemOK = codifica(origem.apelido, 'privadoOK' + mensagem)
        origem.sSocket.send(bMensagemOK)
        usuario.sSocket.send(bMensagemOK)
    else:
        bMensagemFAIL = codifica(origem.apelido, 'privadoFAIL')
        origem.sSocket.send(bMensagemFAIL)


# Manda a lista pra quem pediu
def sendLista(origem):
    lista = ''
    for usuario in listaDeUsuarios:
        lista += usuario.apelido + '\t' + \
            str(usuario.addr[0]) + '\t' + str(usuario.addr[1]) + '\n'
    bMensagem = codifica('Lista', lista)
    origem.sSocket.send(bMensagem)


despachadorVivo = True


# Função responsável por tratar da entrada do usuário à sala
def ConectaUsuario(connectionSocket, addr):

    if despachadorVivo:
        bMensagem = codifica('Servidor', 'entrando' +
                             str(addr[0]) + ':' + str(addr[1]))

        display.listaDeMensagens.append(bMensagem)

        bMensagem = codifica('Servidor', 'apelido?')
        connectionSocket.send(bMensagem)

        apelido = display.trataMensagem(
            connectionSocket.recv(1024)).get('mensagem')
        if apelido.find(' ') != -1:
            apelido = apelido[:apelido.find(' ')]

        jaTem = True
        while jaTem:
            jaTem = False
            for usuario in listaDeUsuarios:
                if apelido == usuario.apelido:
                    jaTem = True

                    bMensagem = codifica('Servidor', 'apelido0')
                    connectionSocket.send(bMensagem)

                    bMensagem = codifica('Servidor', "jaExiste")
                    connectionSocket.send(bMensagem)

                    apelido = display.trataMensagem(
                        connectionSocket.recv(1024)).get('mensagem')
                    if apelido.find(' ') != -1:
                        apelido = apelido[:apelido.find(' ')]
                    break

        bMensagem = codifica('Servidor', 'apelido1'+apelido)
        connectionSocket.send(bMensagem)

        u = Usuario(apelido, connectionSocket, addr, display.listaDeMensagens)
        listaDeUsuarios.append(u)
        u.start()

        sleep(0.1)

        bMensagem = codifica(apelido, " entrou!")
        display.listaDeMensagens.append(bMensagem)
        sendBroadcast(bMensagem)


# Função responsável por despachar o usuário que teve sua conexão aceita à função ConectaUsuario
def DespachaConexao():
    global despachadorVivo
    while despachadorVivo:
        connectionSocket, addr = serverSocket.accept()  # aceita as conexoes dos clientes
        conecta = Thread(target=ConectaUsuario, args=(connectionSocket, addr))
        conecta.start()


despachador = Thread(target=DespachaConexao)
despachador.start()


mensagem = ''
# Enquando o usuário não pedir pra sair...
while mensagem.find('sair()') == -1:
    mensagem = display.entrada.getEntrada()
    display.listaDeMensagens.append(codifica('Serivdor', mensagem))

display.mataThread()
# Encerra as threads e a conexão com o servidor
for usuario in listaDeUsuarios:
    usuario.sSocket.send(codifica('Servidor', 'encerrar'))
    usuario.mataThread()
despachadorVivo = False
socketFechadora = socket(AF_INET, SOCK_STREAM).connect(
    (serverName, serverPort))
serverSocket.close()  # encerra o socket do servidor
print('\033[0m')
