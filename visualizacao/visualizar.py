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
import math
import os
import sys

import networkx as nx
import plotly.graph_objects as go

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(RAIZ, "src"))
from arquivo_grafo import ler  # noqa: E402

CORES = {"ART": "#d1495b", "ALB": "#00798c", "GEN": "#edae49"}
NOMES = {"ART": "Artista", "ALB": "Álbum", "GEN": "Gênero"}
# marcadores maiores (proporcionais aos originais) para acompanhar a fonte maior dos rótulos
TAMANHOS = {"ART": 34, "ALB": 17, "GEN": 25}
FONTE_ROTULO = 22  # px na figura (width=1400, scale=2): 22px*2/444dpi*72pt ≈ 7,1pt impresso
# a 16 cm de largura no relatório (2800 px / (16 cm / 2,54) ≈ 444 dpi)
GRAU_MINIMO_ROTULO_GEN = 5  # gêneros com grau abaixo disso ficam só no hover (reduz poluição)
DIST_MINIMA_ROTULO = 0.09  # separação mínima forçada entre nós rotulados (ver
# afastar_rotulos_proximos); sem isso, pares quase coincidentes (ex.: gêneros
# "latin"/"mpb", que compartilham quase os mesmos álbuns) não cabem em nenhuma
# das 8 direções de texto, por maior que seja o afastamento do rótulo
RAIO_INFLUENCIA_ROTULO = 0.45  # até que distância um nó vizinho ainda "empurra"
# a direção do rótulo (peso 1/d²: vizinhos bem mais próximos dominam)
RAIO_CONFLITO_ROTULO = 0.24  # abaixo disso, dois rótulos na mesma direção
# (ex.: "top center") tendem a se sobrepor visualmente


def tem_rotulo(g, G, v):
    """ART sempre tem rótulo visível; GEN só a partir de um grau mínimo (os
    demais nós continuam com marcador e hover, só sem texto fixo na figura)."""
    tipo = G.nodes[v]["tipo"]
    return tipo == "ART" or (tipo == "GEN" and g.grau(v) >= GRAU_MINIMO_ROTULO_GEN)


def afastar_rotulos_proximos(pos, nos, dist_min, iteracoes=60, passo=0.6):
    """Empurra iterativamente pares de nós rotulados mais próximos que
    dist_min para longe um do outro, só o suficiente para o texto caber.
    Só os nós em `nos` se movem; os demais (álbuns, gêneros sem rótulo)
    mantêm a posição original do spring_layout."""
    pos = dict(pos)
    for _ in range(iteracoes):
        moveu = False
        for i, a in enumerate(nos):
            for b in nos[i + 1:]:
                dx = pos[a][0] - pos[b][0]
                dy = pos[a][1] - pos[b][1]
                d = math.hypot(dx, dy)
                if d < dist_min:
                    moveu = True
                    if d < 1e-9:
                        dx, dy, d = 1e-3, 1e-3, math.sqrt(2) * 1e-3
                    falta = (dist_min - d) / 2 * passo
                    ux, uy = dx / d, dy / d
                    pos[a] = (pos[a][0] + ux * falta, pos[a][1] + uy * falta)
                    pos[b] = (pos[b][0] - ux * falta, pos[b][1] - uy * falta)
        if not moveu:
            break
    return pos


def posicoes_rotulo(nos, pos, raio_influencia=RAIO_INFLUENCIA_ROTULO,
                     raio_conflito=RAIO_CONFLITO_ROTULO):
    """Escolhe, para cada nó rotulado, uma das 8 direções da bússola para o
    texto (ex.: "top center"), afastando-o do "centro de massa" dos outros
    rótulos próximos (repulsão com peso 1/d², não só dos que estão dentro de
    um grupo rígido) e evitando repetir a mesma direção perto de outro nó já
    posicionado (o que causaria sobreposição de texto)."""
    direcoes = [(0, "middle right"), (45, "top right"), (90, "top center"),
                (135, "top left"), (180, "middle left"), (225, "bottom left"),
                (270, "bottom center"), (315, "bottom right")]

    peso_total = {}
    vetor = {}
    for v in nos:
        vx = vy = soma = 0.0
        for u in nos:
            if u == v:
                continue
            dx, dy = pos[v][0] - pos[u][0], pos[v][1] - pos[u][1]
            d = math.hypot(dx, dy) or 1e-6
            if d < raio_influencia:
                peso = 1.0 / (d * d)
                vx += dx / d * peso
                vy += dy / d * peso
                soma += peso
        vetor[v] = (vx, vy)
        peso_total[v] = soma

    # quem tem mais vizinhos próximos (mais "espremido") escolhe direção primeiro
    ordem = sorted(nos, key=lambda v: -peso_total[v])
    atribuidos = []  # [(x, y, direção)]
    textpos = {}
    for v in ordem:
        vx, vy = vetor[v]
        angulo = math.degrees(math.atan2(vy, vx)) % 360 if peso_total[v] > 0 else 90
        candidatos = sorted(direcoes, key=lambda d: min(abs(d[0] - angulo),
                                                          360 - abs(d[0] - angulo)))
        escolhida = candidatos[0][1]
        for _, nome in candidatos:
            em_conflito = any(nome == d2 and math.hypot(pos[v][0] - x2, pos[v][1] - y2) < raio_conflito
                               for x2, y2, d2 in atribuidos)
            if not em_conflito:
                escolhida = nome
                break
        atribuidos.append((pos[v][0], pos[v][1], escolhida))
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
    # rótulo estático só para ART (todos) e GEN com grau >= GRAU_MINIMO_ROTULO_GEN;
    # os demais continuam com marcador e hover, só não exibem texto na figura (reduz
    # poluição visual sem esconder informação, que segue disponível ao passar o mouse)
    nos_rotulados = [v for v in G.nodes if tem_rotulo(g, G, v)]
    pos_texto = dict(zip(nos_rotulados, posicoes_rotulo(nos_rotulados, pos)))
    # marcadores por tipo (sem texto embutido no ponto): a ordem de desenho aqui
    # não importa mais para a legibilidade dos rótulos, porque o texto vai numa
    # trace própria, desenhada por último (ver abaixo), sempre por cima de
    # qualquer marcador (ALB, GEN ou ART)
    legendrank = {"GEN": 1, "ART": 2, "ALB": 3}  # mantém a ordem original na legenda
    for tipo in ("ALB", "GEN", "ART"):
        nos = [v for v in G.nodes if G.nodes[v]["tipo"] == tipo]
        fig.add_trace(go.Scatter(
            x=[pos[v][0] for v in nos], y=[pos[v][1] for v in nos],
            mode="markers", name=NOMES[tipo], legendrank=legendrank[tipo],
            hovertext=[f"{NOMES[tipo]}: {g.rotulos[v].split('] ', 1)[-1]}<br>grau {g.grau(v)}"
                       for v in nos],
            hoverinfo="text",
            marker=dict(size=TAMANHOS[tipo], color=CORES[tipo],
                        line=dict(width=1, color="white"))))
    # trace só de texto, desenhada por último: garante que nenhum marcador (nem
    # mesmo um artista grande) fique por cima do rótulo de outro nó. O marcador
    # invisível (opacity=0) do mesmo tamanho do marcador real é necessário para
    # que o Plotly calcule o deslocamento do texto (ex.: "top center") a partir
    # da borda do círculo verdadeiro, e não de um marcador padrão pequeno
    fig.add_trace(go.Scatter(
        x=[pos[v][0] for v in nos_rotulados], y=[pos[v][1] for v in nos_rotulados],
        mode="markers+text", text=[g.rotulos[v].split("] ", 1)[-1] for v in nos_rotulados],
        textposition=[pos_texto[v] for v in nos_rotulados],
        textfont=dict(size=FONTE_ROTULO), showlegend=False,
        marker=dict(size=[TAMANHOS[G.nodes[v]["tipo"]] for v in nos_rotulados], opacity=0),
        hoverinfo="skip", cliponaxis=False))
    fig.update_layout(
        title=dict(
            text=(f"Grafo tripartido álbum–artista–gênero ({g.n} vértices, {g.m} arestas) "
                  f"— dados: MusicBrainz<br>"
                  f"<sup>rótulos: artistas e gêneros com grau ≥ {GRAU_MINIMO_ROTULO_GEN} "
                  f"(demais só no hover)</sup>"),
            font=dict(size=20)),
        showlegend=True, plot_bgcolor="white", width=1400, height=1000,
        # cliponaxis=False (acima) evita que rótulos nas bordas sejam cortados pelo
        # eixo; a margem generosa dá espaço para o texto que sobra além dos dados
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        margin=dict(l=160, r=160, t=100, b=120))
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
    # afasta minimamente pares de nós rotulados quase coincidentes (ex.: gêneros
    # que compartilham quase os mesmos álbuns), só o suficiente para o texto não
    # se sobrepor; usa a mesma posição ajustada na figura e no GEXF, então HTML,
    # PNG e Gephi mostram sempre o mesmo layout
    nos_rotulados = [v for v in G.nodes if tem_rotulo(g, G, v)]
    pos = afastar_rotulos_proximos(pos, nos_rotulados, DIST_MINIMA_ROTULO)
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
