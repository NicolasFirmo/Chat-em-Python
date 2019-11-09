# Pega a string da mensagem e codifica devidamente num byte array que segue o protocolo
def codifica(apelido, mensagem):
    def MontaMensagem(comando, dados=''):
        # Inicializa a mensagem com um bytearray nulo utf-8
        bMensagem = bytearray('', 'utf-8')

        # Define os primeiros dois octetos do protocolo
        bTam = (len(dados) + 26).to_bytes(2, byteorder='big')

        # Define os 16 octetos do protocolo para o apelido
        apelido16 = apelido + ' '*(16 - len(apelido))
        bApelido = bytearray(apelido16, 'utf-8')

        # Define o comando para sair
        bComando = bytearray(comando, 'utf-8')

        # Define os bytes de dado da mensagem
        bDados = bytearray(dados, 'utf-8')

        # Prepara a mensagem com base no protocolo
        bMensagem.extend(bTam)
        bMensagem.extend(bApelido)
        bMensagem.extend(bComando)
        bMensagem.extend(bDados)

        return bMensagem

    # Comando de login
    if apelido == '':
        return MontaMensagem('apelido!', mensagem)

    # Comando de login
    if apelido == 'Servidor' and mensagem == 'encerrar':
        return MontaMensagem('encerrar')

    # Comando de login
    pos = mensagem.find('apelido?')
    if pos != -1 and apelido == 'Servidor':
        return MontaMensagem('apelido?')

    # Comando de usuário tentando entrar
    pos = mensagem.find('entrando')
    if pos != -1 and apelido == 'Servidor':
        return MontaMensagem('entrando', mensagem[8:])

    # Comando de usuário tentando entrar
    pos = mensagem.find('apelido0')
    if pos != -1 and apelido == 'Servidor':
        return MontaMensagem('apelido0')

    # Comando de usuário tentando entrar
    pos = mensagem.find('jaExiste')
    if pos != -1 and apelido == 'Servidor':
        return MontaMensagem('jaExiste')

    # Comando de usuário tentando entrar
    pos = mensagem.find('apelido1')
    if pos != -1 and apelido == 'Servidor':
        return MontaMensagem('apelido1', mensagem[8:])

    # Comando de logado com sucesso
    pos = mensagem.find(' entrou!')
    if pos != -1:
        return MontaMensagem(' entrou!', apelido)

    # Comando sair
    pos = mensagem.find("sair()")
    if pos != -1:
        return MontaMensagem('    sair')

    # Comando lista
    pos = mensagem.find("lista()")
    if pos != -1:
        return MontaMensagem('  lista?')

    if apelido == 'Lista':
        return MontaMensagem('  lista!', mensagem)

    # Comando lista
    pos = mensagem.find("privado(")
    if pos != -1:
        fim = mensagem.find(')')
        destinatario = mensagem[pos+7:fim+1]
        mensagem = mensagem[0:pos] + mensagem[fim+1:]
        return MontaMensagem('privado?', destinatario + mensagem)

    # Comando lista
    pos = mensagem.find("privadoOK")
    if pos != -1:
        mensagem = mensagem[9:]
        return MontaMensagem('privado1', mensagem)

    # Comando lista
    pos = mensagem.find("privadoFAIL")
    if pos != -1:
        mensagem = mensagem[9:]
        return MontaMensagem('privado0')

    return MontaMensagem('   todos', mensagem)
