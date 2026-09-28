# -*- coding: utf-8 -*-
"""
Projeto de Teoria dos Grafos - Parte 2
Descoberta Musical por Grafos: Álbuns, Artistas e Gêneros

Integrante: Luis Felipe Santos do Nascimento - RA 10420572

Síntese: leitura e gravação do arquivo grafo.txt no formato do enunciado
(tipo, n, n linhas de vértice, m, m linhas de aresta) e formatação do
conteúdo para exibição no menu.

Histórico de alterações:
  28/09/2026 - Luis Felipe - criação
"""
import shlex

from grafo_matriz import GrafoMatrizPonderado

NOMES_TIPO = {
    0: "não orientado sem peso", 1: "não orientado com peso no vértice",
    2: "não orientado com peso na aresta", 3: "não orientado com peso nos vértices e arestas",
    4: "orientado sem peso", 5: "orientado com peso no vértice",
    6: "orientado com peso na aresta", 7: "orientado com peso nos vértices e arestas",
}


def _linhas_uteis(caminho):
    with open(caminho, encoding="utf-8") as arq:
        return [linha.strip() for linha in arq if linha.strip()]


def ler(caminho):
    """Monta um GrafoMatrizPonderado a partir de grafo.txt (tipo 2)."""
    linhas = _linhas_uteis(caminho)
    try:
        tipo = int(linhas[0])
        if tipo != GrafoMatrizPonderado.TIPO:
            raise ValueError(f"tipo {tipo} ({NOMES_TIPO.get(tipo, '?')}) não suportado: "
                             "a aplicação trabalha com o tipo 2")
        n = int(linhas[1])
        g = GrafoMatrizPonderado()
        for i in range(n):
            partes = shlex.split(linhas[2 + i])
            g.insereV(partes[1])
        m = int(linhas[2 + n])
        for j in range(m):
            v, w, peso = linhas[3 + n + j].split()
            if not g.insereA(int(v), int(w), float(peso)):
                raise ValueError(f"aresta inválida na linha {4 + n + j}: {v} {w} {peso}")
    except (IndexError, ValueError) as erro:
        raise ValueError(f"arquivo inválido: {erro}") from erro
    return g


def gravar(g, caminho):
    """Grava o grafo da memória no mesmo formato da leitura."""
    with open(caminho, "w", encoding="utf-8") as arq:
        arq.write(f"{g.TIPO}\n{g.n}\n")
        for i, rotulo in enumerate(g.rotulos):
            arq.write(f'{i} "{rotulo}"\n')
        arq.write(f"{g.m}\n")
        for v in range(g.n):
            for w in range(v + 1, g.n):
                if g.adj[v][w] is not None:
                    arq.write(f"{v} {w} {g.adj[v][w]:.2f}\n")


def formatarConteudo(caminho):
    """Texto tabulado do arquivo: tipo, vértices (por tipo) e arestas."""
    g = ler(caminho)
    saida = [f"Arquivo: {caminho}",
             f"Tipo do grafo: {g.TIPO} - {NOMES_TIPO[g.TIPO]}",
             f"Vértices: {g.n}    Arestas: {g.m}", "",
             f"{'Nº':>4}  {'Tipo':<4}  Rótulo", "-" * 60]
    for i, rotulo in enumerate(g.rotulos):
        saida.append(f"{i:>4}  {g.tipoVertice(i):<4}  {rotulo.split('] ', 1)[-1]}")
    saida += ["", f"{'v':>4}  {'w':>4}  {'peso':>5}  ligação", "-" * 60]
    for v in range(g.n):
        for w in range(v + 1, g.n):
            if g.adj[v][w] is not None:
                saida.append(f"{v:>4}  {w:>4}  {g.adj[v][w]:5.2f}  "
                             f"{g.rotulos[v]}  <->  {g.rotulos[w]}")
    return "\n".join(saida)
