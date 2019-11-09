from threading import Thread, Event

# Obtem a largura da janela para imprimir o número certo de linhas
# que dividem o campo de digitação do resto da tela
from os import get_terminal_size

# Ajuda na colorização dos nomes
from colorsys import hsv_to_rgb

# Sorteia a cor dos nomes
from random import uniform

# Para fazer o diplay ficar sincronizado
from time import sleep

from ansiwrap import ansilen

from getkey import getkey, keys


class Entrada(Thread):
    def __init__(self):
        super().__init__()  # executa o __init__ da classe pai: Thread [padrão]
        self.vivo = True
        self.buffer = ''
        self.pegou = Event()
        self.apertouEnter = Event()

    def mataThread(self):  # "Destrutor"
        self.vivo = False
        self.apertouEnter.set()

    def getEntrada(self):
        self.apertouEnter.wait()
        self.apertouEnter.clear()
        entrada = self.buffer
        self.pegou.set()
        if self.vivo:
            return entrada
        else:
            return 'sair()'

    def run(self):
        # Laço responsável pela entrada de dados
        while self.vivo:
            self.key = getkey()  # Pega a próxima letra
            if self.key == "\n":
                self.apertouEnter.set()
                self.pegou.wait()
                self.pegou.clear()
                # Só pra garantir que tudo vai ser encerrado antes de matar essa thread
                if self.buffer.find('sair()') != -1:
                    sleep(0.1)
                self.buffer = ""
            elif self.key in ('KEY_BACKSPACE', '\b', '\x7f'):
                self.buffer = self.buffer[:-1]
            elif self.key in (keys.UP, keys.DOWN, keys.LEFT, keys.RIGHT):
                continue
            else:
                self.buffer += self.key  # Adiciona a letra ao buffer


class Display(Thread):
    def __init__(self):
        super().__init__()
        self.vivo = True
        self.limpa = "\n"*100  # String que limpra a tela
        self._linhaTam()  # Executa a função logo na inicialização
        self.bg1 = "\033[48;2;71;76;79m"
        self.bg2 = "\033[48;2;51;54;57m"
        self.lCores = []  # Lista de cores para cada usuário
        self.listaDeMensagens = []  # Buffer para as mensagens que irão aparecer na tela
        self.entrada = Entrada()  # Objeto de input
        self.entrada.start()  # Inicia a thread
        print("\033[38;5;255m")

    def mataThread(self):
        self.entrada.mataThread()
        self.vivo = False

    # Prepara a string da linha que divide o campo de digitação do resto da tela
    def _linhaTam(self):
        self.linha = "─"*get_terminal_size(0)[0]

    def run(self):
        while self.vivo:
            while len(self.listaDeMensagens) > 20:  # Limita o tamanho máximo do buffer pra 20
                self.listaDeMensagens.pop(0)

            telaDeMensagens = ''
            for bMensagem in self.listaDeMensagens:
                telaDeMensagens += self.trataMensagem(
                    bMensagem).get('mensagem') + '\n'

            self._linhaTam()

            print(self.bg1 + self.limpa + telaDeMensagens + self.bg2 + self.linha +
                  "\nDigite: " + self.entrada.buffer, end='')
            sleep(0.1)

    # Pega a cor correspondente ao apelido do usuário na lista de cores do display
    def getCor(self, apelido):
        for dupla in self.lCores:
            if dupla[0] == apelido:
                return dupla[1]

        # Se não achar a o apelido, crias-e uma nova cor clara aleatoria e
        # adiciona uma nova entrada na lista que relaciona essa cor com o apelido
        corf = hsv_to_rgb(uniform(0, 1), uniform(0.3, 0.6), uniform(0.7, 1))
        cori = tuple(map(lambda c: int(round(c*255)), corf))
        corstr = "\033[1;38;2;{};{};{}m".format(cori[0], cori[1], cori[2])
        self.lCores.append((apelido, corstr))

        return corstr

    # Faz a conversão das mensagens binárias no protocolo especificado para texto
    def trataMensagem(self, bMensagem):
        tam = int.from_bytes(bMensagem[0:2], 'big')

        apelido = bMensagem[2:18].decode('utf-8')
        apelido = apelido[:apelido.find(' ')]
        cor = self.getCor(apelido)

        comando = bMensagem[18:26].decode('utf-8')

        if apelido == 'Servidor' and comando == 'encerrar':
            return {'mensagem': '', 'comando': comando}

        if comando == 'entrando':
            addr = bMensagem[26:tam].decode('utf-8')
            return {'mensagem': addr + ' tentando entrar...', 'comando': comando}

        if comando == 'apelido?':
            return {'mensagem': 'Qual seu apelido?', 'comando': comando}

        if apelido == '':
            tentaApelido = bMensagem[26:tam].decode('utf-8')
            return {'mensagem': tentaApelido, 'comando': 'apelido!'}

        elif comando == 'jaExiste':
            return {'mensagem': 'Já existe um usuário com esse apelido na sala', 'comando': comando}

        elif comando == 'apelido0':
            return {'mensagem': '', 'comando': comando}

        elif comando == 'apelido1':
            novoApelido = bMensagem[26:tam].decode('utf-8')
            return {'mensagem': novoApelido, 'comando': comando}

        elif comando == ' entrou!':
            apelidoLogado = bMensagem[26:tam].decode('utf-8')
            return {'mensagem': "\033[38;5;248m" + apelidoLogado + " entrou!\033[38;5;255m", 'comando': comando}

        elif comando == 'privado?':
            mensagemPrivada = bMensagem[26:tam].decode('utf-8')
            return {'mensagem': mensagemPrivada, 'comando': comando}

        elif comando == 'privado0':
            return {'mensagem': 'Não há usuários logados com esse apelido!', 'comando': comando}

        elif comando == 'privado1':
            mensagem = bMensagem[26:tam].decode('utf-8')
            return {'mensagem': cor + apelido + "\033[22m mandou no privado\033[38;5;255m: " + mensagem, 'comando': comando}

        elif comando == '  lista?':
            return {'mensagem': cor + apelido + "\033[22;38;5;255m [pediu lista] ", 'comando': comando}

        # lista = bMensagem[26:tam].decode('utf-8')
        elif comando == '  lista!':
            lista = bMensagem[26:tam].decode('utf-8')
            lista = lista[:-1].split('\n')
            topo = '┌' + '─'*18 + '┬' + '─'*18 + '┬' + '─'*18 + '┐'
            cabeca = '├' + '─'*18 + '┼' + '─'*18 + '┼' + '─'*18 + '┤'
            chao = '└' + '─'*18 + '┴' + '─'*18 + '┴' + '─'*18 + '┘'
            listaColorida = ''
            for usuario in lista:
                usuarioSplit = usuario.split('\t')
                cor = self.getCor(usuarioSplit[0])
                listaColorida += '│' + cor + '{0:<18}\033[38;5;255m│{1:<18}│{2:<18}│\n'.format(
                    usuarioSplit[0], usuarioSplit[1], usuarioSplit[2])

            return {'mensagem': topo + '\n│{0:<18}│{1:<18}│{2:<18}│\n'.format('APELIDO', 'IP', 'PORTA') + cabeca + '\n' + listaColorida + chao + '\033[22;38;5;255m', 'comando': comando}

        elif comando == '    sair':
            return {'mensagem': "\033[38;5;248m" + apelido + " saiu!\033[38;5;255m", 'comando': comando}

        elif comando == '   todos':  # Mandar menságem pública (para o grupo)
            mensagem = bMensagem[26:tam].decode('utf-8')
            return {'mensagem': cor + apelido + "\033[22m escreveu\033[38;5;255m: " + mensagem, 'comando': comando}

        # elif comando == 'entrando':  # Avisa (ao servidor) que
        #     addr = bMensagem[26:tam].decode('utf-8')
        #     return "\033[38;5;248m" + addr + " entrando...\033[38;5;255m\n"
        # elif comando == 'apelido?':
        #     return "Qual o seu apelido?\n"
        # elif comando == '  entrou':
        #     return "\033[38;5;248m" + apelido + " entrou!\033[38;5;255m\n"
        # elif comando == '     pop':
        #     return "\n"*100
        # elif comando == '    sair':
        #     return "\033[38;5;248m" + apelido + " saiu!\033[38;5;255m\n"
        # elif comando == '   lista':
        #     lista = bMensagem[26:tam].decode('utf-8')
        #     lista = lista[:-1].split('\n')
        #     listaColorida = ''
        #     for usuario in lista:
        #         usuarioSplit = usuario.split('\t')
        #         cor = self.getCor(usuarioSplit[0])
        #         apelidoColorido = cor + usuarioSplit[0] + '\033[38;5;255m'
        #         listaColorida += apelidoColorido + '\t' + \
        #             usuarioSplit[1] + '\t' + usuarioSplit[2] + '\n'
        #     return ("APELIDO\tIP\tPORTA\n" + listaColorida + '\033[22;38;5;255m').expandtabs(16)
        # elif comando == ' privado':
        #     dados = bMensagem[26:tam].decode('utf-8')
        #     return cor + apelido + "\033[22m mandou no privado\033[38;5;255m: " + dados + "\n"
        # elif comando == 'eprivado':
        #     return "\033[38;5;248mNão há usuário com esse apelido logado na sala\033[38;5;255m\n"
        # elif comando == 'jaExiste':
        #     return "\033[38;5;248mJá existe um usuário logado com este apelido\033[38;5;255m\n"
        else:
            # Debugar
            return "tam: "+str(tam)+";apelido: "+apelido+";comando: "+comando + '\n' + ';mensagem :'+bMensagem.decode('utf-8')
