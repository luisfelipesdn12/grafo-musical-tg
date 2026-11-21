# -*- coding: utf-8 -*-
"""
Projeto de Teoria dos Grafos - Parte 3
Descoberta Musical por Grafos: Álbuns, Artistas e Gêneros

Integrante: Luis Felipe Santos do Nascimento - RA 10420572

Síntese: técnicas da disciplina aplicadas ao grafo tripartido
(GrafoMatrizPonderado, matriz de adjacência, tipo 2):
  - solução do problema: algoritmo de Dijkstra (caminho mínimo) para a
    "trilha de descoberta" entre dois vértices e para recomendar os
    álbuns mais próximos de um álbum de partida;
  - características do grafo: distribuição de graus, coloração de
    vértices por classe (com rerotulação por grau), grafo euleriano /
    percurso euleriano, grafo hamiltoniano (Dirac, Ore e conjunto
    independente maior que n/2), bipartição e planaridade (m <= 3n - 6).
Todas as funções recebem o grafo e não o alteram.

Histórico de alterações:
  19/11/2026 - Luis Felipe - criação (Parte 3)
"""

INFINITO = float("inf")


# =====================================================================
# Solução: caminho mínimo (Dijkstra)
# =====================================================================
def dijkstra(g, origem):
    """Algoritmo de Dijkstra sobre a matriz de adjacência (versão O(n²) vista
    em aula: a cada passo escolhe o vértice aberto de menor estimativa e
    relaxa as arestas que saem dele). Exige pesos não negativos - todos os
    custos do grafo estão em [0,10; 1].
    Devolve (dist, pred): dist[v] = custo mínimo origem -> v (INFINITO se
    inalcançável) e pred[v] = predecessor de v no caminho mínimo."""
    dist = [INFINITO] * g.n
    pred = [None] * g.n
    aberto = [True] * g.n
    dist[origem] = 0.0
    for _ in range(g.n):
        # vértice aberto com a menor estimativa
        u, menor = None, INFINITO
        for v in range(g.n):
            if aberto[v] and dist[v] < menor:
                u, menor = v, dist[v]
        if u is None:          # restantes são inalcançáveis
            break
        aberto[u] = False
        for w, peso in g.vizinhos(u):
            if aberto[w] and dist[u] + peso < dist[w] - 1e-12:
                dist[w] = dist[u] + peso
                pred[w] = u
    return dist, pred


def caminho(pred, destino):
    """Reconstrói o caminho origem -> destino a partir do vetor pred."""
    vertices = []
    v = destino
    while v is not None:
        vertices.append(v)
        v = pred[v]
    return vertices[::-1]


def trilha_descoberta(g, origem, destino):
    """Trilha de descoberta de menor custo entre dois vértices.
    Devolve (custo_total, [vértices]) ou (INFINITO, []) se não houver caminho."""
    dist, pred = dijkstra(g, origem)
    if dist[destino] == INFINITO:
        return INFINITO, []
    return dist[destino], caminho(pred, destino)


def recomendar_albuns(g, album, k=5):
    """Os k álbuns de OUTROS artistas mais próximos (menor custo de
    descoberta) do álbum de partida. Desempate: menos arestas no caminho e,
    depois, ordem do índice. Devolve [(custo, destino, [caminho])]."""
    dist, pred = dijkstra(g, album)
    artista = artista_do_album(g, album)
    candidatos = []
    for v in range(g.n):
        if v == album or g.tipoVertice(v) != "ALB" or dist[v] == INFINITO:
            continue
        if artista is not None and artista_do_album(g, v) == artista:
            continue
        rota = caminho(pred, v)
        candidatos.append((round(dist[v], 2), len(rota), v, rota))
    candidatos.sort()
    return [(c, v, rota) for c, _, v, rota in candidatos[:k]]


def artista_do_album(g, album):
    """Vértice [ART] ligado ao álbum pela aresta de autoria (ou None)."""
    for w, _ in g.vizinhos(album):
        if g.tipoVertice(w) == "ART":
            return w
    return None


# =====================================================================
# Característica 1: graus
# =====================================================================
def resumo_graus(g):
    """Grau de cada vértice, soma dos graus (= 2m, lema do aperto de mãos),
    grau mínimo/máximo/médio por tipo e distribuição (grau -> quantidade)."""
    graus = [g.grau(v) for v in range(g.n)]
    por_tipo = {}
    for tipo in ("ART", "ALB", "GEN"):
        vs = [v for v in range(g.n) if g.tipoVertice(v) == tipo]
        if not vs:
            continue
        gs = [graus[v] for v in vs]
        vmax = max(vs, key=lambda v: (graus[v], -v))
        vmin = min(vs, key=lambda v: (graus[v], v))
        por_tipo[tipo] = {"qtd": len(vs), "min": min(gs), "max": max(gs),
                          "media": sum(gs) / len(gs), "vmax": vmax, "vmin": vmin}
    distribuicao = {}
    for d in graus:
        distribuicao[d] = distribuicao.get(d, 0) + 1
    impares = sum(1 for d in graus if d % 2 == 1)
    return {"graus": graus, "soma": sum(graus), "por_tipo": por_tipo,
            "distribuicao": dict(sorted(distribuicao.items())), "impares": impares,
            "isolados": [v for v in range(g.n) if graus[v] == 0]}


# =====================================================================
# Característica 2: coloração de vértices
# =====================================================================
def rerotular_por_grau(g):
    """Ordem dos vértices por grau decrescente (desempate: menor índice),
    a rerotulação vista em aula para a coloração por classe."""
    return sorted(range(g.n), key=lambda v: (-g.grau(v), v))


def coloracao_por_classe(g):
    """Coloração por classe (aula de coloração de vértices): percorre os
    vértices na ordem rerotulada e monta uma classe de cor de cada vez,
    colocando na classe atual todo vértice ainda sem cor que não seja
    adjacente a nenhum vértice da classe. Devolve a lista de classes
    (cada classe = lista de vértices) - o número de classes é o número de
    cores usado (limite superior para o número cromático)."""
    ordem = rerotular_por_grau(g)
    sem_cor = list(ordem)
    classes = []
    while sem_cor:
        classe = []
        for v in sem_cor:
            if all(g.peso(v, u) is None for u in classe):
                classe.append(v)
        classes.append(classe)
        sem_cor = [v for v in sem_cor if v not in classe]
    return classes


def coloracao_valida(g, classes):
    """Confere que nenhuma aresta liga dois vértices da mesma classe."""
    cor = {}
    for c, classe in enumerate(classes):
        for v in classe:
            cor[v] = c
    if len(cor) != g.n:
        return False
    return all(cor[v] != cor[w] for v in range(g.n) for w, _ in g.vizinhos(v))


def encontrar_triangulo(g):
    """Um triângulo (K3) do grafo, se houver: prova que são necessárias
    pelo menos 3 cores e que o grafo não é bipartido."""
    for u in range(g.n):
        viz_u = [w for w, _ in g.vizinhos(u) if w > u]
        for i, v in enumerate(viz_u):
            for w in viz_u[i + 1:]:
                if g.peso(v, w) is not None:
                    return (u, v, w)
    return None


# =====================================================================
# Característica 3: grafo euleriano
# =====================================================================
def analise_euler(g, conexo):
    """Teorema de Euler (grafo não orientado): um grafo conexo tem ciclo
    euleriano se e só se todos os graus são pares, e tem percurso euleriano
    aberto se e só se tem exatamente 2 vértices de grau ímpar."""
    impares = [v for v in range(g.n) if g.grau(v) % 2 == 1]
    if not conexo:
        situacao = "não euleriano (grafo desconexo)"
    elif not impares:
        situacao = "EULERIANO: admite ciclo euleriano"
    elif len(impares) == 2:
        situacao = "SEMIEULERIANO: admite percurso euleriano aberto"
    else:
        situacao = "NÃO EULERIANO: não admite ciclo nem percurso euleriano"
    # arestas extras mínimas para eulerizar (cada aresta corrige 2 ímpares)
    return {"impares": impares, "situacao": situacao, "eulerizar": len(impares) // 2}


# =====================================================================
# Característica 4: grafo hamiltoniano
# =====================================================================
def analise_hamilton(g, conexo):
    """Condições estudadas em aula + argumento do conjunto independente.
    - Dirac (suficiente, n >= 3): todo grau >= n/2;
    - Ore (suficiente, n >= 3): d(u) + d(v) >= n para todo par não adjacente;
    - Necessária: se existe conjunto independente S (nenhuma aresta interna)
      com |S| > n/2, não há ciclo hamiltoniano (no ciclo, vértices de S não
      podem ser consecutivos); se |S| > (n + 1)/2, não há nem caminho
      hamiltoniano. Cada parte do grafo tripartido é um conjunto independente."""
    n = g.n
    graus = [g.grau(v) for v in range(n)]
    dirac = n >= 3 and all(2 * d >= n for d in graus)
    ore = n >= 3 and all(graus[u] + graus[v] >= n
                         for u in range(n) for v in range(u + 1, n) if g.peso(u, v) is None)
    partes = {}
    for v in range(n):
        partes.setdefault(g.tipoVertice(v), []).append(v)
    tipo_maior, maior = max(partes.items(), key=lambda kv: len(kv[1]))
    sem_ciclo = 2 * len(maior) > n
    sem_caminho = 2 * len(maior) > n + 1
    if not conexo:
        conclusao = "NÃO HAMILTONIANO (grafo desconexo)"
    elif sem_caminho:
        conclusao = "NÃO HAMILTONIANO: não admite ciclo nem caminho hamiltoniano"
    elif sem_ciclo:
        conclusao = "NÃO HAMILTONIANO: não admite ciclo hamiltoniano"
    elif dirac or ore:
        conclusao = "HAMILTONIANO (garantido por Dirac/Ore)"
    else:
        conclusao = "inconclusivo pelas condições estudadas"
    return {"dirac": dirac, "ore": ore, "grau_min": min(graus) if graus else 0,
            "tipo_maior": tipo_maior, "tam_maior": len(maior), "sem_ciclo": sem_ciclo,
            "sem_caminho": sem_caminho, "conclusao": conclusao}


# =====================================================================
# Característica 5: bipartição e planaridade
# =====================================================================
def eh_bipartido(g):
    """Tenta 2-colorir cada componente por busca em largura; falha ao achar
    uma aresta entre vértices de mesma cor (ciclo ímpar)."""
    lado = [None] * g.n
    for inicio in range(g.n):
        if lado[inicio] is not None:
            continue
        lado[inicio] = 0
        fila = [inicio]
        while fila:
            v = fila.pop(0)
            for w, _ in g.vizinhos(v):
                if lado[w] is None:
                    lado[w] = 1 - lado[v]
                    fila.append(w)
                elif lado[w] == lado[v]:
                    return False, (v, w)
    return True, None


def analise_planaridade(g):
    """Condições necessárias de planaridade (corolários da fórmula de Euler
    n - m + f = 2 para grafos simples conexos com n >= 3):
      m <= 3n - 6 (qualquer grafo planar) e m <= 2n - 4 (planar sem triângulos).
    Se a desigualdade falha, o grafo com certeza NÃO é planar; se vale, o
    teste é inconclusivo (seria preciso procurar subdivisões de K5/K3,3)."""
    limite = 3 * g.n - 6
    triangulo = encontrar_triangulo(g)
    limite_sem_tri = 2 * g.n - 4
    if g.m > limite:
        conclusao = "NÃO PLANAR (m > 3n - 6)"
    elif triangulo is None and g.m > limite_sem_tri:
        conclusao = "NÃO PLANAR (sem triângulos e m > 2n - 4)"
    else:
        conclusao = "inconclusivo pela fórmula de Euler"
    return {"limite": limite, "limite_sem_tri": limite_sem_tri, "triangulo": triangulo,
            "conclusao": conclusao}
