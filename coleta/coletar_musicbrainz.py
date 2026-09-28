# -*- coding: utf-8 -*-
"""
Projeto de Teoria dos Grafos - Parte 2
Descoberta Musical por Grafos: Álbuns, Artistas e Gêneros

Integrante: Luis Felipe Santos do Nascimento - RA 10420572

Síntese: coleta, na API pública do MusicBrainz (sem dados de usuários),
os gêneros votados de cada artista semente e seus álbuns de estúdio com
os gêneros votados de cada álbum. Grava um JSON por artista em dados/brutos.
Respeita o limite de 1 requisição por segundo da API.

Formato de coleta/artistas_semente.txt: "nome|cena" por linha; uma
terceira coluna opcional "|mbid" fixa o MBID do MusicBrainz e pula a
busca por nome — usado quando a busca encontra um homônimo (ex.: Steve
Lacy, o jazzista 1934-2004, em vez do músico de R&B nascido em 1998).

Histórico de alterações:
  28/09/2026 - Luis Felipe - criação
"""
import json
import os
import time
import urllib.parse
import urllib.request

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
API = "https://musicbrainz.org/ws/2/"
USER_AGENT = "grafo-musical-tg/1.0 ( https://github.com/luisfelipesdn12 )"
_ultima = [0.0]


def requisitar(caminho, params, tentativas=5):
    params = dict(params, fmt="json")
    url = API + caminho + "?" + urllib.parse.urlencode(params)
    for tentativa in range(tentativas):
        espera = 1.1 - (time.time() - _ultima[0])
        if espera > 0:
            time.sleep(espera)
        _ultima[0] = time.time()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)
        except Exception as erro:  # 503 = limite de taxa; tenta de novo
            print(f"  tentativa {tentativa + 1} falhou ({erro}); aguardando...")
            time.sleep(2 * (tentativa + 1))
    raise RuntimeError(f"falha ao acessar {url}")


def buscar_artista(nome):
    resp = requisitar("artist", {"query": f'artist:"{nome}"', "limit": 5})
    candidatos = sorted(resp["artists"], key=lambda a: -int(a.get("score", 0)))
    return candidatos[0]["id"]


def albuns_de_estudio(mbid):
    albuns, deslocamento = [], 0
    while True:
        resp = requisitar("release-group", {"artist": mbid, "type": "album",
                                            "inc": "genres", "limit": 100,
                                            "offset": deslocamento})
        for rg in resp["release-groups"]:
            if rg.get("primary-type") == "Album" and not rg.get("secondary-types"):
                albuns.append({"title": rg["title"],
                               "first-release-date": rg.get("first-release-date", ""),
                               "genres": [{"name": g["name"], "count": g["count"]}
                                          for g in rg.get("genres", [])]})
        deslocamento += 100
        if deslocamento >= resp.get("release-group-count", 0):
            return albuns


def main():
    pasta = os.path.join(RAIZ, "dados", "brutos")
    os.makedirs(pasta, exist_ok=True)
    with open(os.path.join(RAIZ, "coleta", "artistas_semente.txt"), encoding="utf-8") as f:
        sementes = [linha.strip().split("|") for linha in f if linha.strip()]
    for ordem, semente in enumerate(sementes):
        # terceira coluna opcional: MBID fixo, usado quando a busca por nome
        # encontra um homônimo (ex.: Steve Lacy jazzista x Steve Lacy R&B)
        nome, cena = semente[0], semente[1]
        mbid_fixo = semente[2] if len(semente) > 2 else None
        destino = os.path.join(pasta, f"{ordem:02d}.json")
        if os.path.exists(destino):
            continue  # já coletado (permite retomar)
        print(f"[{ordem + 1}/{len(sementes)}] {nome}")
        mbid = mbid_fixo or buscar_artista(nome)
        artista = requisitar(f"artist/{mbid}", {"inc": "genres"})
        dados = {"ordem": ordem, "nome": artista["name"], "cena": cena, "mbid": mbid,
                 "genres": [{"name": g["name"], "count": g["count"]}
                            for g in artista.get("genres", [])],
                 "albuns": albuns_de_estudio(mbid),
                 "coletado_em": time.strftime("%Y-%m-%d")}
        with open(destino, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
