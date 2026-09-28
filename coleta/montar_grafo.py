# -*- coding: utf-8 -*-
"""
Projeto de Teoria dos Grafos - Parte 2
Descoberta Musical por Grafos: Álbuns, Artistas e Gêneros

Integrante: Luis Felipe Santos do Nascimento - RA 10420572

Síntese: transforma os dados brutos do MusicBrainz (dados/brutos/*.json)
no grafo tripartido álbum-artista-gênero e grava dados/grafo.txt,
dados/vertices.csv e dados/arestas.csv.
Peso da aresta = custo de descoberta = 1 - afinidade.

Histórico de alterações:
  28/09/2026 - Luis Felipe - criação
"""
import csv
import glob
import json
import os
import sys

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(RAIZ, "src"))
from grafo_matriz import GrafoMatrizPonderado  # noqa: E402
from arquivo_grafo import gravar  # noqa: E402


def limpar(texto):
    return texto.replace('"', "'").strip()


def afinidades(genres, k):
    """Top-k gêneros por votos; afinidade = votos / votos do mais votado."""
    ordenados = sorted(genres, key=lambda g: (-g["count"], g["name"]))[:k]
    if not ordenados:
        return []
    maximo = ordenados[0]["count"]
    return [(g["name"], round(g["count"] / maximo, 2)) for g in ordenados]


def escolher_albuns(albuns, max_albuns):
    """Álbuns com gênero, os mais votados primeiro (desempate: mais antigo)."""
    com_genero = [a for a in albuns if a.get("genres")]
    com_genero.sort(key=lambda a: (-sum(g["count"] for g in a["genres"]),
                                   a.get("first-release-date") or "9999"))
    return com_genero[:max_albuns]


def construir(artistas, max_albuns=4, max_generos=5):
    ligacoes = []  # (rotulo_origem, nome_genero, afinidade)
    rot_art, rot_alb, autoria = [], [], []
    for art in artistas:
        ra = f"[ART] {limpar(art['nome'])}"
        rot_art.append(ra)
        for nome, af in afinidades(art["genres"], max_generos):
            ligacoes.append((ra, nome, af))
        for alb in escolher_albuns(art["albuns"], max_albuns):
            rb = f"[ALB] {limpar(alb['title'])} — {limpar(art['nome'])}"
            rot_alb.append(rb)
            autoria.append((ra, rb))
            for nome, af in afinidades(alb["genres"], max_generos):
                ligacoes.append((rb, nome, af))

    contagem = {}
    for _, nome, _ in ligacoes:
        contagem[nome] = contagem.get(nome, 0) + 1
    generos = sorted(n for n, c in contagem.items() if c >= 2)

    g = GrafoMatrizPonderado()
    indice = {}
    for rotulo in rot_art + rot_alb + [f"[GEN] {limpar(n)}" for n in generos]:
        indice[rotulo] = g.insereV(rotulo)
    for ra, rb in autoria:
        g.insereA(indice[ra], indice[rb], 0.0)
    for origem, nome, af in ligacoes:
        rg = f"[GEN] {limpar(nome)}"
        if rg in indice:
            g.insereA(indice[origem], indice[rg], round(1 - af, 2))
    return g


def carregar_brutos(pasta):
    artistas = []
    for arquivo in sorted(glob.glob(os.path.join(pasta, "*.json"))):
        with open(arquivo, encoding="utf-8") as f:
            artistas.append(json.load(f))
    artistas.sort(key=lambda a: a["ordem"])
    return artistas


def exportar_csv(g, pasta):
    with open(os.path.join(pasta, "vertices.csv"), "w", newline="", encoding="utf-8") as f:
        esc = csv.writer(f)
        esc.writerow(["id", "tipo", "rotulo", "grau"])
        for v in range(g.n):
            esc.writerow([v, g.tipoVertice(v), g.rotulos[v], g.grau(v)])
    with open(os.path.join(pasta, "arestas.csv"), "w", newline="", encoding="utf-8") as f:
        esc = csv.writer(f)
        esc.writerow(["v", "w", "peso", "afinidade", "relacao"])
        for v in range(g.n):
            for w, p in g.vizinhos(v):
                if v < w:
                    rel = "-".join(sorted([g.tipoVertice(v), g.tipoVertice(w)]))
                    esc.writerow([v, w, f"{p:.2f}", f"{1 - p:.2f}", rel])


if __name__ == "__main__":
    max_albuns = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    dados = os.path.join(RAIZ, "dados")
    g = construir(carregar_brutos(os.path.join(dados, "brutos")), max_albuns=max_albuns)
    gravar(g, os.path.join(dados, "grafo.txt"))
    exportar_csv(g, dados)
    tipos = {t: sum(1 for v in range(g.n) if g.tipoVertice(v) == t) for t in ("ART", "ALB", "GEN")}
    print(f"n={g.n} m={g.m} por tipo={tipos} componentes={len(g.componentes())}")
    if g.n < 80 or g.m < 200:
        sys.exit("ATENÇÃO: abaixo do mínimo (80 vértices / 200 arestas)")
