from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, timeout
from threading import Thread
from time import sleep

# Minha classe responsável pela interface e pelo tratamento das mensagens
from display import Display

# Minha classe responsável pela codificação da mensagem com base no protocolo
from protocolo import codifica


# Classe que faz a interface com os clientes
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
        listaDeUsuarios.remove(self)
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

            elif comando == 'privado?':
                sendPrivado(self, bMensagem)

            elif comando == '  lista?':
                self.sSocket.send(fazLista())

            else:
                try:
                    self.sSocket.send(bMensagem)
                except BrokenPipeError:
                    self.mataThread()


# definicao das variaveis e funções
serverName = ''  # ip do servidor (em branco)
serverPort = 65000  # porta a se conectar
serverSocket = socket(AF_INET, SOCK_STREAM)  # criacao do socket TCP
# bind do ip do servidor com a porta
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.bind((serverName, serverPort))
serverSocket.listen(1)  # socket pronto para 'ouvir' conexoes

# Inicia o diplay
display = Display()
display.start()

listaDeUsuarios = []


# Manda a mensagem recebida para todos os usuários logados e para o display do servidor
def sendBroadcast(bMensagem):
    for usuario in listaDeUsuarios:
        try:
            usuario.sSocket.send(bMensagem)
        except OSError:
            usuario.mataThread()


# Tenta mandar a mensagem recebida para o usuário especificado no comando privado()
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


# Faz a lista formatada
def fazLista():
    lista = ''
    for usuario in listaDeUsuarios:
        lista += usuario.apelido + '\t' + \
            str(usuario.addr[0]) + '\t' + str(usuario.addr[1]) + '\n'
    bMensagem = codifica('Lista', lista)
    return bMensagem


despachadorVivo = True


# Função que se certifica de receber um apelido válido do usuário a logar (utilizada pela próxima função)
def validaApelido(connectionSocket):
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

    return apelido


# Função responsável por tratar da entrada do usuário à sala em uma thread à parte
def ConectaUsuario(connectionSocket, addr):
    if despachadorVivo:
        bMensagem = codifica('Servidor', 'entrando' +
                             str(addr[0]) + ':' + str(addr[1]))

        display.listaDeMensagens.append(bMensagem)

        apelido = validaApelido(connectionSocket)

        if apelido == '':  # Abora caso o usuário não complete o login devidamente
            return

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

# Enquando o usuário não pedir pra sair...
mensagem = ''
while mensagem.find('sair()') == -1:
    mensagem = display.entrada.getEntrada()
    if mensagem.find('lista()') != -1:
        display.listaDeMensagens.append(fazLista())
        continue
    display.listaDeMensagens.append(codifica('Serivdor', mensagem))

# Encerra as threads e aa conexões com todos os clientes logados
display.mataThread()
for usuario in listaDeUsuarios:
    usuario.sSocket.send(codifica('Servidor', 'encerrar'))
    usuario.mataThread()
despachadorVivo = False
socketFechadora = socket(AF_INET, SOCK_STREAM).connect(
    (serverName, serverPort))
serverSocket.close()
print('\033[0m')  # printa uma nova linha
