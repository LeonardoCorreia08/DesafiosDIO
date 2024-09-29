import textwrap
from abc import ABC, abstractclassmethod, abstractproperty
from datetime import datetime


class ContasIterador:
    def __init__(self, contas):
        self.contas = contas
        self._index = 0

    def __iter__(self):
        return self

    def __next__(self):
        try:
            conta = self.contas[self._index]
            return f"""\
            Agência:\t{conta.agencia}
            Número:\t\t{conta.numero}
            Titular:\t{conta.cliente.nome}
            Saldo:\t\tR$ {conta.saldo:.2f}
        """
        except IndexError:
            raise StopIteration
        finally:
            self._index += 1


class Cliente:
    def __init__(self, endereco):
        self.endereco = endereco
        self.contas = []

    def realizar_transacao(self, conta, transacao):
        transacao.registrar(conta)

    def adicionar_conta(self, conta):
        self.contas.append(conta)


class PessoaFisica(Cliente):
    def __init__(self, nome, data_nascimento, cpf, endereco):
        super().__init__(endereco)
        self.nome = nome
        self.data_nascimento = data_nascimento
        self.cpf = cpf


class Conta(ABC):
    def __init__(self, numero, cliente):
        self._saldo = 0
        self._numero = numero
        self._agencia = "0001"
        self._cliente = cliente
        self._historico = Historico()

    @classmethod
    @abstractclassmethod
    def nova_conta(cls, cliente, numero):
        pass

    @property
    def saldo(self):
        return self._saldo

    @property
    def numero(self):
        return self._numero

    @property
    def agencia(self):
        return self._agencia

    @property
    def cliente(self):
        return self._cliente

    @property
    def historico(self):
        return self._historico

    def sacar(self, valor):
        saldo = self.saldo
        excedeu_saldo = valor > saldo

        if excedeu_saldo:
            print("\n@@@ Operação falhou! Você não tem saldo suficiente. @@@")
            return False

        elif valor > 0:
            self._saldo -= valor
            print("\n=== Saque realizado com sucesso! ===")
            return True

        else:
            print("\n@@@ Operação falhou! O valor informado é inválido. @@@")
            return False

    def depositar(self, valor):
        if valor > 0:
            self._saldo += valor
            print("\n=== Depósito realizado com sucesso! ===")
            return True
        else:
            print("\n@@@ Operação falhou! O valor informado é inválido. @@@")
            return False

    def aplicar_juros(self, taxa_juros):
        if self.saldo > 0:
            juros = self.saldo * taxa_juros / 100
            self._saldo += juros
            print(f"\n=== Juros de {taxa_juros:.2f}% aplicados. Saldo atualizado: R$ {self.saldo:.2f} ===")
        else:
            print("\n@@@ Saldo insuficiente para aplicar juros. @@@")
        return


class ContaCorrente(Conta):
    def __init__(self, numero, cliente, limite=500, limite_saques=3):
        super().__init__(numero, cliente)
        self._limite = limite
        self._limite_saques = limite_saques

    @classmethod
    def nova_conta(cls, cliente, numero, limite=500, limite_saques=3):
        return cls(numero, cliente, limite, limite_saques)

    def sacar(self, valor):
        numero_saques = len(
            [transacao for transacao in self.historico.transacoes if transacao["tipo"] == Saque.__name__]
        )

        excedeu_limite = valor > self._limite
        excedeu_saques = numero_saques >= self._limite_saques

        if excedeu_limite:
            print("\n@@@ Operação falhou! O valor do saque excede o limite. @@@")
            return False

        elif excedeu_saques:
            print("\n@@@ Operação falhou! Número máximo de saques excedido. @@@")
            return False

        else:
            return super().sacar(valor)


class ContaPoupanca(Conta):
    def __init__(self, numero, cliente, taxa_juros=5):
        super().__init__(numero, cliente)
        self.taxa_juros = taxa_juros

    @classmethod
    def nova_conta(cls, cliente, numero):
        return cls(numero, cliente)

    def aplicar_juros(self):
        super().aplicar_juros(self.taxa_juros)


class Historico:
    def __init__(self):
        self._transacoes = []

    @property
    def transacoes(self):
        return self._transacoes

    def adicionar_transacao(self, transacao):
        self._transacoes.append(
            {
                "tipo": transacao.__class__.__name__,
                "valor": transacao.valor,
                "data": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            }
        )

    def gerar_relatorio(self, tipo_transacao=None):
        for transacao in self._transacoes:
            if tipo_transacao is None or transacao["tipo"].lower() == tipo_transacao.lower():
                yield transacao


class Transacao(ABC):
    @property
    @abstractproperty
    def valor(self):
        pass

    @abstractclassmethod
    def registrar(self, conta):
        pass


class Saque(Transacao):
    def __init__(self, valor):
        self._valor = valor

    @property
    def valor(self):
        return self._valor

    def registrar(self, conta):
        sucesso_transacao = conta.sacar(self.valor)

        if sucesso_transacao:
            conta.historico.adicionar_transacao(self)


class Deposito(Transacao):
    def __init__(self, valor):
        self._valor = valor

    @property
    def valor(self):
        return self._valor

    def registrar(self, conta):
        sucesso_transacao = conta.depositar(self.valor)

        if sucesso_transacao:
            conta.historico.adicionar_transacao(self)


class Transferencia(Transacao):
    def __init__(self, valor, conta_destino):
        self._valor = valor
        self.conta_destino = conta_destino

    @property
    def valor(self):
        return self._valor

    def registrar(self, conta_origem):
        sucesso_transacao = conta_origem.sacar(self.valor)

        if sucesso_transacao:
            self.conta_destino.depositar(self.valor)
            conta_origem.historico.adicionar_transacao(self)
            print("\n=== Transferência realizada com sucesso! ===")


def log_transacao(func):
    def envelope(*args, **kwargs):
        resultado = func(*args, **kwargs)
        print(f"{datetime.now()}: {func.__name__.upper()}")
        return resultado

    return envelope


def menu():
    menu = """\n
    ================ MENU ================
    [d]\tDepositar
    [s]\tSacar
    [t]\tTransferir
    [j]\tAplicar Juros
    [e]\tExtrato
    [nc]\tNova conta corrente
    [np]\tNova conta poupança
    [lc]\tListar contas
    [nu]\tNovo usuário
    [q]\tSair
    => """

    return input(textwrap.dedent(menu))


def filtrar_cliente(cpf, clientes):
    clientes_filtrados = [cliente for cliente in clientes if cliente.cpf == cpf]
    return clientes_filtrados[0] if clientes_filtrados else None


def recuperar_conta_cliente(cliente):
    if not cliente.contas:
        print("\n@@@ Cliente não possui conta! @@@")
        return

    return cliente.contas[0]


@log_transacao
def depositar(clientes):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    valor = float(input("Informe o valor do depósito: "))
    conta = recuperar_conta_cliente(cliente)

    if not conta:
        return

    transacao = Deposito(valor)
    cliente.realizar_transacao(conta, transacao)


@log_transacao
def sacar(clientes):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    valor = float(input("Informe o valor do saque: "))
    conta = recuperar_conta_cliente(cliente)

    if not conta:
        return

    transacao = Saque(valor)
    cliente.realizar_transacao(conta, transacao)


@log_transacao
def transferir(clientes):
    cpf_origem = input("Informe o CPF do cliente de origem: ")
    cliente_origem = filtrar_cliente(cpf_origem, clientes)

    if not cliente_origem:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    valor = float(input("Informe o valor da transferência: "))
    cpf_destino = input("Informe o CPF do cliente de destino: ")
    cliente_destino = filtrar_cliente(cpf_destino, clientes)

    if not cliente_destino:
        print("\n@@@ Cliente de destino não encontrado! @@@")
        return

    conta_origem = recuperar_conta_cliente(cliente_origem)
    conta_destino = recuperar_conta_cliente(cliente_destino)

    if not conta_origem or not conta_destino:
        return

    transacao = Transferencia(valor, conta_destino)
    cliente_origem.realizar_transacao(conta_origem, transacao)


@log_transacao
def aplicar_juros(clientes):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    taxa_juros = float(input("Informe a taxa de juros (%): "))
    conta = recuperar_conta_cliente(cliente)

    if not conta:
        return

    conta.aplicar_juros(taxa_juros)


def extrato(clientes):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    conta = recuperar_conta_cliente(cliente)

    if not conta:
        return

    print(f"\n=== Extrato da conta {conta.numero} ===")
    for transacao in conta.historico.gerar_relatorio():
        print(f"Data: {transacao['data']}, Tipo: {transacao['tipo']}, Valor: R$ {transacao['valor']:.2f}")


def nova_conta(clientes):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    numero_conta = input("Informe o número da nova conta: ")
    tipo_conta = input("Informe o tipo da conta (corrente/poupanca): ").lower()

    if tipo_conta == "corrente":
        conta = ContaCorrente.nova_conta(cliente, numero_conta)
    elif tipo_conta == "poupanca":
        conta = ContaPoupanca.nova_conta(cliente, numero_conta)
    else:
        print("\n@@@ Tipo de conta inválido! @@@")
        return

    cliente.adicionar_conta(conta)
    print("\n=== Conta criada com sucesso! ===")


def novo_usuario(clientes):
    nome = input("Informe o nome do cliente: ")
    cpf = input("Informe o CPF do cliente: ")
    data_nascimento = input("Informe a data de nascimento do cliente: ")
    endereco = input("Informe o endereço do cliente: ")

    cliente = PessoaFisica(nome, data_nascimento, cpf, endereco)
    clientes.append(cliente)

    print("\n=== Cliente criado com sucesso! ===")


def listar_contas(clientes):
    for cliente in clientes:
        print(f"\nCliente: {cliente.nome}")
        for conta in cliente.contas:
            print(f"""\
            Conta: {conta.numero}
            Saldo: R$ {conta.saldo:.2f}
            """)


def main():
    clientes = []
    while True:
        opcao = menu()
        if opcao == 'd':
            depositar(clientes)
        elif opcao == 's':
            sacar(clientes)
        elif opcao == 't':
            transferir(clientes)
        elif opcao == 'j':
            aplicar_juros(clientes)
        elif opcao == 'e':
            extrato(clientes)
        elif opcao == 'nc':
            nova_conta(clientes)
        elif opcao == 'np':
            nova_conta(clientes)
        elif opcao == 'lc':
            listar_contas(clientes)
        elif opcao == 'nu':
            novo_usuario(clientes)
        elif opcao == 'q':
            print("\n=== Saindo do sistema ===")
            break
        else:
            print("\n@@@ Opção inválida! @@@")

if __name__ == "__main__":
    main()
