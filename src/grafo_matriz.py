# -*- coding: utf-8 -*-
"""
Projeto de Teoria dos Grafos - Parte 2
Descoberta Musical por Grafos: Álbuns, Artistas e Gêneros

Integrante: Luis Felipe Santos do Nascimento - RA 10420572

Síntese: classe GrafoMatrizPonderado - grafo NÃO orientado com peso nas
arestas (tipo 2), representado por MATRIZ DE ADJACÊNCIA, com um vetor de
rótulos. Baseada na classe GrafoND (matriz de adjacência) vista em aula.

Histórico de alterações:
  28/09/2026 - Luis Felipe - criação a partir de grafoMatrizND.py da aula
"""

TIPOS_VALIDOS = ("ALB", "ART", "GEN")


class GrafoMatrizPonderado:
    TIPO = 2  # 2 = não orientado com peso na aresta

    def __init__(self):
        self.n = 0          # número de vértices
        self.m = 0          # número de arestas
        self.adj = []       # matriz n x n; None = sem aresta (0.0 é peso válido)
        self.rotulos = []   # rótulo do vértice i, ex.: "[ART] Frank Ocean"

    # ---------------------------------------------------------------- utilidades
    def _valido(self, v):
        return isinstance(v, int) and 0 <= v < self.n

    def tipoVertice(self, v):
        """Tipo do vértice a partir do prefixo do rótulo ([ALB], [ART], [GEN])."""
        rotulo = self.rotulos[v]
        if rotulo.startswith("[") and "]" in rotulo:
            tipo = rotulo[1:rotulo.index("]")]
            if tipo in TIPOS_VALIDOS:
                return tipo
        return "?"

    def peso(self, v, w):
        return self.adj[v][w]

    def vizinhos(self, v):
        """Lista de (w, peso) adjacentes a v."""
        return [(w, p) for w, p in enumerate(self.adj[v]) if p is not None]

    def grau(self, v):
        return len(self.vizinhos(v))

    # ---------------------------------------------------------------- vértices
    def insereV(self, rotulo):
        """Acrescenta uma linha e uma coluna vazias; devolve o índice novo."""
        for linha in self.adj:
            linha.append(None)
        self.n += 1
        self.adj.append([None] * self.n)
        self.rotulos.append(rotulo)
        return self.n - 1

    def removeV(self, v):
        """Remove o vértice v e todas as arestas incidentes; os vértices
        seguintes têm o índice decrementado em 1."""
        if not self._valido(v):
            return False
        self.m -= self.grau(v)
        del self.adj[v]
        for linha in self.adj:
            del linha[v]
        del self.rotulos[v]
        self.n -= 1
        return True

    # ---------------------------------------------------------------- arestas
    def insereA(self, v, w, peso):
        """Insere {v,w} com o peso dado (custo de descoberta em [0,1]).
        Recusa laço, aresta repetida, índice inválido, peso fora do
        intervalo e aresta entre vértices do mesmo tipo (grafo tripartido)."""
        if not (self._valido(v) and self._valido(w)) or v == w:
            return False
        if not (0.0 <= peso <= 1.0) or self.adj[v][w] is not None:
            return False
        if self.tipoVertice(v) == self.tipoVertice(w) != "?":
            return False
        self.adj[v][w] = peso
        self.adj[w][v] = peso
        self.m += 1
        return True

    def removeA(self, v, w):
        if not (self._valido(v) and self._valido(w)) or self.adj[v][w] is None:
            return False
        self.adj[v][w] = None
        self.adj[w][v] = None
        self.m -= 1
        return True

    # ---------------------------------------------------------------- conexidade
    def componentes(self):
        """Componentes conexas por busca em largura (BFS); cada componente é
        a lista ordenada de índices. Grafo conexo <=> uma única componente."""
        visitado = [False] * self.n
        resultado = []
        for inicio in range(self.n):
            if visitado[inicio]:
                continue
            fila = [inicio]
            visitado[inicio] = True
            componente = []
            while fila:
                v = fila.pop(0)
                componente.append(v)
                for w, _ in self.vizinhos(v):
                    if not visitado[w]:
                        visitado[w] = True
                        fila.append(w)
            resultado.append(sorted(componente))
        return resultado

    def ehConexo(self):
        return len(self.componentes()) <= 1

    # ---------------------------------------------------------------- exibição
    def textoLista(self):
        """Lista de adjacência legível: vértice, rótulo e vizinhos com peso."""
        linhas = [f"n = {self.n}   m = {self.m}   (tipo {self.TIPO})", ""]
        for v in range(self.n):
            viz = ", ".join(f"{w}({p:.2f})" for w, p in self.vizinhos(v))
            linhas.append(f"{v:3d} {self.rotulos[v]}")
            linhas.append(f"      -> {viz if viz else '(sem vizinhos)'}")
        return "\n".join(linhas)

    def textoMatriz(self):
        """Matriz compacta: '.' = sem aresta, senão o peso com 2 casas."""
        cab = "     " + "".join(f"{j:>5d}" for j in range(self.n))
        linhas = [cab]
        for i in range(self.n):
            cel = "".join("    ." if p is None else f"{p:5.2f}" for p in self.adj[i])
            linhas.append(f"{i:4d} {cel}")
        return "\n".join(linhas)
