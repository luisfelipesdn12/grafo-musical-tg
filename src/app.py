# -*- coding: utf-8 -*-
"""
Projeto de Teoria dos Grafos - Parte 2
Descoberta Musical por Grafos: Álbuns, Artistas e Gêneros

Integrante: Luis Felipe Santos do Nascimento - RA 10420572

Síntese: aplicação de console com o menu de opções a-j do enunciado,
operando sobre o grafo tripartido álbum-artista-gênero (matriz de
adjacência, tipo 2) lido de dados/grafo.txt.

Histórico de alterações:
  28/09/2026 - Luis Felipe - criação
"""
import os

from arquivo_grafo import formatarConteudo, gravar, ler
from grafo_matriz import GrafoMatrizPonderado

TITULO = "DESCOBERTA MUSICAL POR GRAFOS — Álbuns, Artistas e Gêneros"
CAMINHO_PADRAO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dados", "grafo.txt")
OPCOES = [
    ("a", "Ler dados do arquivo grafo.txt"), ("b", "Gravar dados no arquivo grafo.txt"),
    ("c", "Inserir vértice"), ("d", "Inserir aresta"), ("e", "Remover vértice"),
    ("f", "Remover aresta"), ("g", "Mostrar conteúdo do arquivo"), ("h", "Mostrar grafo"),
    ("i", "Apresentar a conexidade do grafo"), ("j", "Encerrar a aplicação"),
]
TIPOS = {"1": "ALB", "2": "ART", "3": "GEN"}


class Aplicacao:
    def __init__(self, entrada, caminho_padrao):
        self.entrada = entrada
        self.caminho_padrao = caminho_padrao
        self.grafo = None

    # -------------------------------------------------------------- leitura
    def perguntar(self, texto):
        return self.entrada(texto).strip()

    def ler_inteiro(self, texto, minimo, maximo):
        """Lê inteiro em [minimo, maximo]; Enter vazio cancela (None)."""
        while True:
            valor = self.perguntar(texto)
            if valor == "":
                return None
            if valor.lstrip("-").isdigit():
                numero = int(valor)
                if minimo <= numero <= maximo:
                    return numero
                print(f"  Valor fora do intervalo [{minimo}, {maximo}].")
            else:
                print("  Entrada inválida: digite um número inteiro.")

    def ler_real(self, texto):
        """Lê peso real em [0, 1]; Enter vazio cancela (None)."""
        while True:
            valor = self.perguntar(texto).replace(",", ".")
            if valor == "":
                return None
            try:
                numero = float(valor)
                if 0.0 <= numero <= 1.0:
                    return numero
                print("  O peso (custo de descoberta) deve estar entre 0 e 1.")
            except ValueError:
                print("  Entrada inválida: digite um número real (ex.: 0.35).")

    def ler_vertice(self, texto):
        return self.ler_inteiro(texto, 0, self.grafo.n - 1)

    def caminho(self):
        valor = self.perguntar(f"Caminho do arquivo [Enter = {self.caminho_padrao}]: ")
        return valor or self.caminho_padrao

    # -------------------------------------------------------------- opções
    def op_a(self):
        caminho = self.caminho()
        try:
            self.grafo = ler(caminho)
            print(f"Grafo lido: {self.grafo.n} vértices, {self.grafo.m} arestas.")
        except (OSError, ValueError) as erro:
            print(f"Não foi possível ler o arquivo: {erro}")

    def op_b(self):
        caminho = self.caminho()
        try:
            gravar(self.grafo, caminho)
            print(f"Grafo gravado em {caminho} ({self.grafo.n} vértices, {self.grafo.m} arestas).")
        except OSError as erro:
            print(f"Não foi possível gravar: {erro}")

    def op_c(self):
        tipo = self.perguntar("Tipo do vértice (1 = álbum, 2 = artista, 3 = gênero): ")
        if tipo not in TIPOS:
            print("Tipo inválido. Operação cancelada.")
            return
        nome = self.perguntar("Nome: ").replace('"', "'")
        if not nome:
            print("Nome vazio. Operação cancelada.")
            return
        rotulo = f"[{TIPOS[tipo]}] {nome}"
        if rotulo in self.grafo.rotulos:
            print(f"Já existe o vértice {rotulo}.")
            return
        print(f"Vértice {self.grafo.insereV(rotulo)} inserido: {rotulo}")

    def op_d(self):
        v = self.ler_vertice("Vértice v: ")
        w = None if v is None else self.ler_vertice("Vértice w: ")
        peso = None if w is None else self.ler_real("Peso (custo de descoberta, 0 a 1): ")
        if peso is None:
            print("Operação cancelada.")
            return
        if self.grafo.insereA(v, w, peso):
            print(f"Aresta inserida: {self.grafo.rotulos[v]} <-> {self.grafo.rotulos[w]} (peso {peso:.2f})")
        else:
            print("Aresta não inserida: já existe, é um laço ou liga vértices do mesmo tipo "
                  "(o grafo é tripartido: álbum, artista e gênero).")

    def op_e(self):
        v = self.ler_vertice("Vértice a remover: ")
        if v is None:
            print("Operação cancelada.")
            return
        rotulo, grau = self.grafo.rotulos[v], self.grafo.grau(v)
        self.grafo.removeV(v)
        print(f"Removido {rotulo} e {grau} aresta(s) incidente(s). "
              f"Os vértices após {v} tiveram o índice reduzido em 1.")

    def op_f(self):
        v = self.ler_vertice("Vértice v: ")
        w = None if v is None else self.ler_vertice("Vértice w: ")
        if w is None:
            print("Operação cancelada.")
        elif self.grafo.removeA(v, w):
            print(f"Aresta removida: {self.grafo.rotulos[v]} <-> {self.grafo.rotulos[w]}")
        else:
            print("Não existe aresta entre esses vértices.")

    def op_g(self):
        caminho = self.caminho()
        try:
            print(formatarConteudo(caminho))
        except (OSError, ValueError) as erro:
            print(f"Não foi possível mostrar o arquivo: {erro}")

    def op_h(self):
        forma = self.perguntar("Mostrar como 1 = lista de adjacência, 2 = matriz de adjacência: ")
        print(self.grafo.textoMatriz() if forma == "2" else self.grafo.textoLista())

    def op_i(self):
        comps = self.grafo.componentes()
        print(f"O grafo é {'CONEXO' if len(comps) <= 1 else 'DESCONEXO'} "
              f"({len(comps)} componente(s) conexa(s)).")
        for k, comp in enumerate(sorted(comps, key=len, reverse=True), start=1):
            amostra = "; ".join(self.grafo.rotulos[v] for v in comp[:8])
            extra = " ..." if len(comp) > 8 else ""
            print(f"  Componente {k}: {len(comp)} vértice(s) - {amostra}{extra}")
        print("Obs.: grafo NÃO orientado - as categorias C0-C3, o algoritmo FCONEX e o grafo "
              "reduzido se aplicam a grafos orientados.")

    # -------------------------------------------------------------- laço
    def menu(self):
        print("\n" + "=" * len(TITULO))
        print(TITULO)
        print("=" * len(TITULO))
        for letra, texto in OPCOES:
            print(f"  {letra}) {texto}")

    def executar(self):
        precisa_grafo = set("bcdefhi")
        while True:
            self.menu()
            opcao = self.perguntar("Opção: ").lower()
            if opcao == "j":
                print("Encerrando a aplicação. Até logo!")
                return
            if opcao not in dict(OPCOES):
                print("Opção inválida.")
                continue
            if opcao in precisa_grafo and self.grafo is None:
                print("Nenhum grafo carregado. Use a opção a) primeiro.")
                continue
            getattr(self, f"op_{opcao}")()


def executar(entrada=input, caminho_padrao=CAMINHO_PADRAO):
    Aplicacao(entrada, caminho_padrao).executar()


if __name__ == "__main__":
    executar()
