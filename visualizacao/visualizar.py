# -*- coding: utf-8 -*-
"""
Projeto de Teoria dos Grafos - Parte 2
Descoberta Musical por Grafos: Álbuns, Artistas e Gêneros

Integrante: Luis Felipe Santos do Nascimento - RA 10420572

Síntese: visualização do grafo. Lê grafo.txt com a classe da aplicação,
calcula a disposição com NetworkX (spring layout, semente fixa) e desenha
com Plotly (HTML interativo + PNG). Exporta também grafo.gexf, com as
mesmas posições e cores, para abrir no Gephi. NetworkX é usado apenas
para layout/exportação; nenhum algoritmo da aplicação depende dele.

Histórico de alterações:
  28/09/2026 - Luis Felipe - criação
"""
import os
import sys

import networkx as nx
import plotly.graph_objects as go

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(RAIZ, "src"))
from arquivo_grafo import ler  # noqa: E402

CORES = {"ART": "#d1495b", "ALB": "#00798c", "GEN": "#edae49"}
NOMES = {"ART": "Artista", "ALB": "Álbum", "GEN": "Gênero"}
TAMANHOS = {"ART": 22, "ALB": 11, "GEN": 16}
LIMIAR_COLISAO = 0.065  # distância (layout) abaixo da qual dois rótulos (artista
# e/ou gênero) tendem a se sobrepor visualmente


def posicoes_rotulo(nos, pos, limiar):
    """Agrupa nós próximos (com rótulo de texto) e alterna a posição do texto
    dentro de cada grupo, para reduzir sobreposição em regiões densas."""
    pai = {v: v for v in nos}

    def achar(v):
        while pai[v] != v:
            pai[v] = pai[pai[v]]
            v = pai[v]
        return v

    def unir(a, b):
        ra, rb = achar(a), achar(b)
        if ra != rb:
            pai[ra] = rb

    for i, a in enumerate(nos):
        for b in nos[i + 1:]:
            if ((pos[a][0] - pos[b][0]) ** 2 + (pos[a][1] - pos[b][1]) ** 2) ** 0.5 < limiar:
                unir(a, b)

    grupos = {}
    for v in nos:
        grupos.setdefault(achar(v), []).append(v)

    ciclo = ["top center", "bottom center", "middle right", "middle left"]
    textpos = {}
    for grupo in grupos.values():
        if len(grupo) == 1:
            textpos[grupo[0]] = "top center"
            continue
        cx = sum(pos[v][0] for v in grupo) / len(grupo)
        cy = sum(pos[v][1] for v in grupo) / len(grupo)
        usados = set()
        # ordena do mais distante do centro para o mais próximo, para que quem
        # tem direção clara escolha primeiro sua posição (afastando o rótulo
        # do centro do grupo); o restante recebe a posição livre no ciclo
        for v in sorted(grupo, key=lambda v: -((pos[v][0] - cx) ** 2 + (pos[v][1] - cy) ** 2)):
            dx, dy = pos[v][0] - cx, pos[v][1] - cy
            if dx == 0 and dy == 0:
                candidatos = ciclo
            elif abs(dy) >= abs(dx):
                candidatos = (["top center", "bottom center"] if dy > 0
                              else ["bottom center", "top center"])
                candidatos += ["middle right", "middle left"]
            else:
                candidatos = (["middle right", "middle left"] if dx > 0
                              else ["middle left", "middle right"])
                candidatos += ["top center", "bottom center"]
            escolhida = next((c for c in candidatos if c not in usados), candidatos[0])
            usados.add(escolhida)
            textpos[v] = escolhida
    return [textpos[v] for v in nos]


def para_networkx(g):
    G = nx.Graph()
    for v in range(g.n):
        tipo = g.tipoVertice(v)
        G.add_node(v, label=g.rotulos[v], tipo=tipo)
    for v in range(g.n):
        for w, p in g.vizinhos(v):
            if v < w:
                G.add_edge(v, w, weight=round(1 - p, 2), custo=p)  # weight = afinidade
    return G


def desenhar(g, G, pos):
    fig = go.Figure()
    # arestas agrupadas em 3 faixas de afinidade (largura/opacidade)
    faixas = [(0.0, 0.34, 0.6, "afinidade baixa"), (0.34, 0.67, 1.2, "afinidade média"),
              (0.67, 1.01, 2.2, "afinidade alta")]
    for lo, hi, largura, nome in faixas:
        xs, ys = [], []
        for v, w, d in G.edges(data=True):
            if lo <= d["weight"] < hi:
                xs += [pos[v][0], pos[w][0], None]
                ys += [pos[v][1], pos[w][1], None]
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", name=nome, hoverinfo="skip",
                                 line=dict(width=largura, color="rgba(120,120,120,0.45)")))
    # posições de texto calculadas juntas para ART+GEN (os dois tipos com rótulo
    # visível), para evitar sobreposição também entre artista e gênero próximos
    nos_com_texto = [v for v in G.nodes if G.nodes[v]["tipo"] in ("ART", "GEN")]
    pos_texto = dict(zip(nos_com_texto, posicoes_rotulo(nos_com_texto, pos, LIMIAR_COLISAO)))
    # ordem de desenho: ALB primeiro (fica no fundo), GEN e ART por cima, para que
    # nenhum marcador sem rótulo (álbum) sobreponha o texto de artista/gênero;
    # legendrank mantém a ordem original da legenda (Gênero, Artista, Álbum)
    legendrank = {"GEN": 1, "ART": 2, "ALB": 3}
    for tipo in ("ALB", "GEN", "ART"):
        nos = [v for v in G.nodes if G.nodes[v]["tipo"] == tipo]
        rotulos = [g.rotulos[v].split("] ", 1)[-1] for v in nos]
        textposition = ([pos_texto[v] for v in nos] if tipo != "ALB" else "top center")
        fig.add_trace(go.Scatter(
            x=[pos[v][0] for v in nos], y=[pos[v][1] for v in nos],
            mode="markers+text" if tipo != "ALB" else "markers",
            name=NOMES[tipo], text=rotulos, textposition=textposition,
            textfont=dict(size=9), legendrank=legendrank[tipo],
            hovertext=[f"{NOMES[tipo]}: {g.rotulos[v].split('] ', 1)[-1]}<br>grau {g.grau(v)}"
                       for v in nos],
            hoverinfo="text", cliponaxis=False,
            marker=dict(size=TAMANHOS[tipo], color=CORES[tipo],
                        line=dict(width=1, color="white"))))
    fig.update_layout(
        title=f"Grafo tripartido álbum–artista–gênero ({g.n} vértices, {g.m} arestas) — dados: MusicBrainz",
        showlegend=True, plot_bgcolor="white", width=1400, height=1000,
        # cliponaxis=False (acima) evita que rótulos nas bordas sejam cortados pelo
        # eixo; a margem generosa dá espaço para o texto que sobra além dos dados
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        margin=dict(l=70, r=70, t=60, b=70))
    return fig


def exportar_gexf(G, pos, caminho):
    for v in G.nodes:
        cor = CORES[G.nodes[v]["tipo"]].lstrip("#")
        G.nodes[v]["viz"] = {
            "color": {"r": int(cor[0:2], 16), "g": int(cor[2:4], 16), "b": int(cor[4:6], 16), "a": 1.0},
            "position": {"x": float(pos[v][0] * 1000), "y": float(pos[v][1] * 1000), "z": 0.0},
            "size": float(TAMANHOS[G.nodes[v]["tipo"]]),
        }
    nx.write_gexf(G, caminho)


def main():
    caminho = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, "dados", "grafo.txt")
    g = ler(caminho)
    G = para_networkx(g)
    pos = nx.spring_layout(G, weight="weight", seed=42, k=0.35, iterations=200)
    saida = os.path.join(RAIZ, "visualizacao")
    fig = desenhar(g, G, pos)
    # GEXF e HTML primeiro: não dependem do kaleido (engine de imagem estática) e
    # devem ser gerados mesmo que a exportação do PNG falhe (ver bloco abaixo).
    exportar_gexf(G, pos, os.path.join(saida, "grafo.gexf"))
    fig.write_html(os.path.join(saida, "grafo_interativo.html"), include_plotlyjs="cdn")
    gerados = ["grafo.gexf", "grafo_interativo.html"]
    try:
        fig.write_image(os.path.join(saida, "grafo.png"), scale=2)
        gerados.append("grafo.png")
    except Exception as erro:  # noqa: BLE001 - kaleido pode falhar por motivos de ambiente
        print("Aviso: falha ao gerar grafo.png via kaleido:", erro)
        print("O kaleido 0.2.1 não aceita espaços no caminho do ambiente virtual; "
              "crie o .venv em um caminho sem espaços ou gere o PNG pelo botão de "
              "câmera (ícone de máquina fotográfica) no canto superior do HTML "
              "interativo (grafo_interativo.html).")
    print("Gerados:", ", ".join(gerados))


if __name__ == "__main__":
    main()
