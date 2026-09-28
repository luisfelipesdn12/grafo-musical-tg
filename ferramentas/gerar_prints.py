# -*- coding: utf-8 -*-
"""
Projeto de Teoria dos Grafos - Parte 2
Descoberta Musical por Grafos: Álbuns, Artistas e Gêneros

Integrante: Luis Felipe Santos do Nascimento - RA 10420572

Síntese: gerador automático dos "printscreens" de teste da aplicação de
console (src/app.py), exigidos no relatório (ao menos 2 testes por opção
do menu a-j). Cada roteiro simula uma sessão de terminal fornecendo, no
lugar do input() real, uma lista de respostas pré-definidas; o wrapper de
entrada ecoa "prompt + resposta" (como um terminal real) e a saída
completa é capturada e renderizada como PNG (fundo escuro, fonte
monoespaçada, barra de título falsa) com Pillow. Os índices de vértices
usados nos roteiros (ex.: "[ART] Frank Ocean", um vértice de gênero, uma
aresta álbum-gênero existente etc.) são sempre calculados em tempo de
execução a partir do grafo real (dados/grafo.txt) - nunca fixos no
código - para que cada legenda descreva exatamente o que aparece na
imagem. Toda a execução ocorre sobre CÓPIAS temporárias do arquivo; o
dados/grafo.txt original nunca é alterado.

Uso:  python3 ferramentas/gerar_prints.py

Histórico de alterações:
  28/09/2026 - Luis Felipe - criação
  28/09/2026 - Luis Felipe - recorta a matriz de adjacência (h, teste 2) a
    uma janela de 20x20 vértices, em vez de só truncar linhas, para caber
    legível numa imagem (a matriz completa tem 109 colunas)
  28/09/2026 - Luis Felipe - c1 passa a inserir um álbum com nome
    verificado como ausente do grafo em tempo de execução (evita cair no
    caminho de "já existe o vértice"); adiciona verificar(), que confere
    cada roteiro contra o(s) trecho(s) de saída esperado(s) e falha alto
    se a legenda não bater com o que a aplicação realmente respondeu
"""
import contextlib
import copy
import io
import json
import os
import shutil
import sys
import tempfile

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow não instalado - PNGs não serão gerados (pip install pillow)")
    sys.exit(0)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(RAIZ, "src")
sys.path.insert(0, SRC)

from app import executar  # noqa: E402
from arquivo_grafo import ler  # noqa: E402

GRAFO_ORIGINAL = os.path.join(RAIZ, "dados", "grafo.txt")
DESTINO = os.path.join(RAIZ, "relatorio", "figuras", "prints")

# ---------------------------------------------------------------- aparência
FUNDO = (30, 30, 30)            # #1e1e1e
BARRA_TITULO = (55, 55, 58)
COR_TEXTO = (222, 226, 232)
COR_DESTAQUE = (126, 200, 255)
COR_TITULO_JANELA = (214, 214, 219)
MARGEM = 16
TAM_FONTE = 15
ALTURA_BARRA = 34
MAX_LINHAS = 60
TITULO_JANELA = "python src/app.py"

CAMINHOS_FONTE = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/croscore/Cousine-Regular.ttf",
]


def carregar_fonte(tamanho):
    for caminho in CAMINHOS_FONTE:
        if os.path.exists(caminho):
            return ImageFont.truetype(caminho, tamanho)
    return ImageFont.load_default()


# ---------------------------------------------------------------- entrada simulada
def fazer_entrada(respostas):
    """Fábrica do substituto de input(): devolve a próxima resposta da lista
    e ecoa 'prompt + resposta' no stdout, simulando uma sessão real de
    terminal. Quando as respostas se esgotam, levanta EOFError - que
    Aplicacao.executar() trata encerrando a aplicação normalmente."""
    it = iter(respostas)

    def entrada(prompt):
        try:
            resposta = next(it)
        except StopIteration:
            raise EOFError
        print(prompt + resposta)
        return resposta

    return entrada


def rodar_sessao(respostas, caminho_grafo):
    """Executa a aplicação com as respostas dadas e devolve o texto
    completo que apareceria no terminal."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        executar(entrada=fazer_entrada(respostas), caminho_padrao=caminho_grafo)
    return buffer.getvalue()


PROMPT_MATRIZ = "Mostrar como 1 = lista de adjacência, 2 = matriz de adjacência: "
PREFIXO_MATRIZ = 5          # "     " no cabeçalho / "NNNN " em cada linha de dados
LARGURA_COLUNA_MATRIZ = 5   # cada coluna (cabeçalho ou célula) ocupa 5 caracteres


def recortar_matriz(texto, n, max_colunas=20, max_linhas=20):
    """Recorta especificamente a saída da opção h) 2 (matriz de adjacência
    completa, 109x109) para uma janela legível de max_linhas x max_colunas
    vértices, preservando os comandos ecoados no início e o menu/despedida
    no final - sem isso a imagem fica larga demais (milhares de pixels) e
    ilegível quando embutida no relatório."""
    linhas = texto.rstrip("\n").split("\n")
    inicio = next(i for i, l in enumerate(linhas) if l.startswith(PROMPT_MATRIZ))
    cabecalho = linhas[inicio + 1]
    linhas_dados = linhas[inicio + 2: inicio + 2 + n]
    cauda = linhas[inicio + 2 + n:]

    largura_corte = PREFIXO_MATRIZ + max_colunas * LARGURA_COLUNA_MATRIZ
    bloco = [cabecalho[:largura_corte]]
    bloco += [linha[:largura_corte] for linha in linhas_dados[:max_linhas]]
    bloco.append(f"... (recorte: {max_linhas} de {n} vértices exibidos; "
                 "a opção h mostra a matriz completa) ...")

    return "\n".join(linhas[:inicio + 1] + bloco + cauda)


def truncar(texto, max_linhas=MAX_LINHAS):
    """Trunca sessões muito longas (opções g e h), preservando o começo
    (banner do menu e comandos digitados) e o final (prompt/encerramento),
    para que a imagem caiba num tamanho razoável sem perder o contexto."""
    linhas = texto.rstrip("\n").split("\n")
    if len(linhas) <= max_linhas:
        return "\n".join(linhas)
    cauda = 10
    cabeca = max_linhas - cauda - 1
    omitidas = len(linhas) - cabeca - cauda
    meio = [f"... ({omitidas} linhas omitidas) ..."]
    return "\n".join(linhas[:cabeca] + meio + linhas[-cauda:])


# ---------------------------------------------------------------- renderização
def renderizar_png(texto, caminho_png):
    fonte = carregar_fonte(TAM_FONTE)
    fonte_titulo = carregar_fonte(13)
    linhas = texto.rstrip("\n").split("\n")

    caixa = fonte.getbbox("M")
    largura_char = caixa[2] - caixa[0]
    altura_linha = TAM_FONTE + 7

    colunas = max((len(l) for l in linhas), default=1)
    largura = MARGEM * 2 + max(colunas, 50) * largura_char
    altura = ALTURA_BARRA + MARGEM * 2 + len(linhas) * altura_linha
    largura, altura = int(largura), int(altura)

    img = Image.new("RGB", (largura, altura), FUNDO)
    desenho = ImageDraw.Draw(img)

    # barra de título falsa, com os três "semáforos" de uma janela de terminal
    desenho.rectangle([0, 0, largura, ALTURA_BARRA], fill=BARRA_TITULO)
    for i, cor in enumerate([(237, 106, 94), (245, 191, 79), (97, 194, 84)]):
        cx = 18 + i * 20
        desenho.ellipse([cx - 6, ALTURA_BARRA // 2 - 6, cx + 6, ALTURA_BARRA // 2 + 6], fill=cor)
    desenho.text((largura / 2, ALTURA_BARRA / 2), TITULO_JANELA, font=fonte_titulo,
                  fill=COR_TITULO_JANELA, anchor="mm")

    for i, linha in enumerate(linhas):
        cor = COR_DESTAQUE if linha.startswith("=") or linha.startswith("...") else COR_TEXTO
        y = ALTURA_BARRA + MARGEM + i * altura_linha
        desenho.text((MARGEM, y), linha, font=fonte, fill=cor)

    img.save(caminho_png)


def verificar(opcao, teste, texto, esperado):
    """Confere que a saída BRUTA (antes de truncar/recortar) realmente
    contém o(s) trecho(s) que a legenda promete - falha alto (levanta
    erro e para a geração) se algo não bater, em vez de silenciosamente
    publicar um print que mostra o resultado errado (ex.: c1 legendado
    como "inserção com sucesso" mas mostrando "já existe o vértice")."""
    trechos = [esperado] if isinstance(esperado, str) else list(esperado)
    faltando = [t for t in trechos if t not in texto]
    if faltando:
        raise AssertionError(
            f"Roteiro {opcao}{teste}: a saída não contém o(s) trecho(s) esperado(s) "
            f"{faltando!r}.\n--- saída capturada ---\n{texto}"
        )


# ---------------------------------------------------------------- roteiros
def copiar_grafo(base_tmp, nome):
    pasta = os.path.join(base_tmp, nome)
    os.makedirs(pasta, exist_ok=True)
    destino = os.path.join(pasta, "grafo.txt")
    shutil.copy(GRAFO_ORIGINAL, destino)
    return destino


def nome_ausente(g, tipo_prefixo, base):
    """Garante um rótulo "[tipo_prefixo] <nome>" que ainda NÃO existe no
    grafo - usado para roteiros de inserção (opção c), que precisam de um
    nome livre para o teste realmente inserir o vértice (em vez de cair no
    caminho de "já existe"). Se a base já existir, acrescenta um sufixo
    numérico até achar um nome livre."""
    candidato = base
    sufixo = 2
    while f"[{tipo_prefixo}] {candidato}" in g.rotulos:
        candidato = f"{base} ({sufixo})"
        sufixo += 1
    return candidato


def calcular_dados_reais():
    """Lê o grafo REAL (somente leitura - nunca é gravado) para calcular,
    em tempo de execução, os índices/valores usados nos roteiros."""
    g = ler(GRAFO_ORIGINAL)

    nome_album_c1 = nome_ausente(g, "ALB", "Racional Vol. 3 — Tim Maia")

    idx_frank = g.rotulos.index("[ART] Frank Ocean")
    idx_art2 = next(i for i in range(g.n) if g.tipoVertice(i) == "ART" and i != idx_frank)

    idx_gen1 = next(i for i in range(g.n) if g.tipoVertice(i) == "GEN")

    idx_alb_f1 = idx_gen_f1 = None
    for v in range(g.n):
        if g.tipoVertice(v) != "ALB":
            continue
        for w, _ in g.vizinhos(v):
            if g.tipoVertice(w) == "GEN":
                idx_alb_f1, idx_gen_f1 = v, w
                break
        if idx_alb_f1 is not None:
            break

    def desconecta_ao_isolar(indice):
        copia = copy.deepcopy(g)
        for w, _ in list(copia.vizinhos(indice)):
            copia.removeA(indice, w)
        return copia.componentes()

    candidatos = sorted((i for i in range(g.n) if g.tipoVertice(i) == "ALB"), key=g.grau)
    idx_album_i2 = None
    for cand in candidatos:
        if len(desconecta_ao_isolar(cand)) > 1:
            idx_album_i2 = cand
            break
    if idx_album_i2 is None:
        raise RuntimeError("Nenhum álbum isola o grafo ao remover suas arestas - "
                            "roteiro i2 precisa ser revisto.")
    vizinhos_album_i2 = [w for w, _ in g.vizinhos(idx_album_i2)]

    return {
        "n": g.n,
        "m": g.m,
        "rotulos": g.rotulos,
        "nome_album_c1": nome_album_c1,
        "idx_frank": idx_frank,
        "idx_art2": idx_art2,
        "idx_gen1": idx_gen1,
        "grau_gen1": g.grau(idx_gen1),
        "idx_alb_f1": idx_alb_f1,
        "idx_gen_f1": idx_gen_f1,
        "idx_album_i2": idx_album_i2,
        "vizinhos_album_i2": vizinhos_album_i2,
    }


def montar_roteiros(dados, base_tmp):
    """Devolve a lista de roteiros: (opção, teste, respostas, legenda,
    esperado). `esperado` é uma string ou lista de substrings que DEVEM
    aparecer na saída bruta (antes de qualquer corte/recorte) - é a
    garantia de que a imagem realmente mostra o que a legenda promete
    (ex.: c1 tem que mostrar "inserido", não "já existe")."""
    r = dados["rotulos"]
    nome_c1 = dados["nome_album_c1"]
    fi, ai = dados["idx_frank"], dados["idx_art2"]
    gi, ggrau = dados["idx_gen1"], dados["grau_gen1"]
    albf, genf = dados["idx_alb_f1"], dados["idx_gen_f1"]
    albi, vizi = dados["idx_album_i2"], dados["vizinhos_album_i2"]
    n, m = dados["n"], dados["m"]

    respostas_f_album = []
    for w in vizi:
        respostas_f_album += ["f", str(albi), str(w)]

    return [
        ("a", 1, ["a", ""],
         f"Opção a) — teste 1: leitura do arquivo padrão dados/grafo.txt "
         f"({n} vértices, {m} arestas).",
         f"Grafo lido: {n} vértices, {m} arestas."),
        ("a", 2, ["a", "inexistente.txt"],
         "Opção a) — teste 2: leitura de um arquivo inexistente é tratada com mensagem de erro.",
         "Não foi possível ler o arquivo:"),

        ("b", 1, ["a", "", "c", "3", "neo-soul teste", "b", ""],
         "Opção b) — teste 1: após inserir um gênero novo, o grafo é gravado no caminho padrão "
         "(Enter).",
         [f"Vértice {n} inserido: [GEN] neo-soul teste", f"({n + 1} vértices, {m} arestas)."]),
        ("b", 2, ["a", "", "b", os.path.join(base_tmp, "b2", "copia_alvo.txt")],
         "Opção b) — teste 2: gravação do grafo num caminho alternativo informado pelo usuário.",
         ["Grafo gravado em", f"({n} vértices, {m} arestas)."]),

        ("c", 1, ["a", "", "c", "1", nome_c1],
         f"Opção c) — teste 1: inserção de um novo vértice do tipo álbum (\"{nome_c1}\").",
         f"Vértice {n} inserido: [ALB] {nome_c1}"),
        ("c", 2, ["a", "", "c", "9"],
         "Opção c) — teste 2: tipo de vértice inválido (\"9\") é recusado.",
         "Tipo inválido. Operação cancelada."),

        ("d", 1, ["a", "", "c", "3", "gênero teste", "d", str(n), str(fi), "0.4"],
         f"Opção d) — teste 1: aresta válida entre o novo gênero inserido e "
         f"\"{r[fi]}\" (tipos diferentes).",
         f"Aresta inserida: [GEN] gênero teste <-> {r[fi]} (peso 0.40)"),
        ("d", 2, ["a", "", "d", str(fi), str(ai), "2", "0.2"],
         f"Opção d) — teste 2: peso fora de [0,1] (\"2\") é rejeitado e, em seguida, a aresta "
         f"entre \"{r[fi]}\" e \"{r[ai]}\" (mesmo tipo ART) é recusada pelo grafo tripartido.",
         ["O peso (custo de descoberta) deve estar entre 0 e 1.",
          "Aresta não inserida: já existe, é um laço ou liga vértices do mesmo tipo"]),

        ("e", 1, ["a", "", "e", str(gi)],
         f"Opção e) — teste 1: remoção do vértice de gênero \"{r[gi]}\" e das "
         f"{ggrau} aresta(s) incidente(s).",
         f"Removido {r[gi]} e {ggrau} aresta(s) incidente(s)."),
        ("e", 2, ["a", "", "e", "999", ""],
         "Opção e) — teste 2: índice fora do intervalo válido (\"999\") é rejeitado; Enter "
         "vazio cancela a remoção.",
         [f"Valor fora do intervalo [0, {n - 1}].", "Operação cancelada."]),

        ("f", 1, ["a", "", "f", str(albf), str(genf)],
         f"Opção f) — teste 1: remoção da aresta existente entre \"{r[albf]}\" e \"{r[genf]}\".",
         f"Aresta removida: {r[albf]} <-> {r[genf]}"),
        ("f", 2, ["a", "", "f", str(fi), str(ai)],
         f"Opção f) — teste 2: tentativa de remover uma aresta inexistente entre "
         f"\"{r[fi]}\" e \"{r[ai]}\" (dois artistas nunca ficam ligados) é tratada.",
         "Não existe aresta entre esses vértices."),

        ("g", 1, ["g", ""],
         "Opção g) — teste 1: exibição formatada do conteúdo do arquivo padrão "
         "(saída truncada para caber na imagem).",
         f"Vértices: {n}    Arestas: {m}"),
        ("g", 2, ["g", "inexistente.txt"],
         "Opção g) — teste 2: leitura do conteúdo de um arquivo inexistente é tratada com erro.",
         "Não foi possível mostrar o arquivo:"),

        ("h", 1, ["a", "", "h", "1"],
         "Opção h) — teste 1: grafo exibido como lista de adjacência (saída truncada).",
         f"n = {n}   m = {m}   (tipo 2)"),
        ("h", 2, ["a", "", "h", "2"],
         f"Opção h) — teste 2: grafo exibido como matriz de adjacência (recorte de 20×20 "
         f"vértices para caber na imagem; a matriz completa tem {n}×{n}).",
         [PROMPT_MATRIZ + "2", f"{n - 1:4d} "]),
        ("h", 3, ["h"],
         "Opção h) — teste 3: exibir o grafo sem antes carregá-lo (opção a) é bloqueado.",
         "Nenhum grafo carregado. Use a opção a) primeiro."),

        ("i", 1, ["a", "", "i"],
         f"Opção i) — teste 1: o grafo real é CONEXO (1 componente com os {n} vértices).",
         "O grafo é CONEXO (1 componente(s) conexa(s))."),
        ("i", 2, ["a", ""] + respostas_f_album + ["i"],
         f"Opção i) — teste 2: ao remover as {len(vizi)} aresta(s) do álbum \"{r[albi]}\", "
         f"isolando-o, o grafo passa a ser DESCONEXO (o álbum vira uma componente à parte).",
         ["O grafo é DESCONEXO (2 componente(s) conexa(s)).", f"1 vértice(s) - {r[albi]}"]),

        ("j", 1, ["j"],
         "Opção j) — teste 1: a opção j encerra a aplicação imediatamente.",
         "Encerrando a aplicação. Até logo!"),
        ("j", 2, ["x", "j"],
         "Opção j) — teste 2: uma opção inválida (\"x\") é rejeitada antes de encerrar com j.",
         ["Opção inválida.", "Encerrando a aplicação. Até logo!"]),
    ]


def main():
    os.makedirs(DESTINO, exist_ok=True)
    base_tmp = tempfile.mkdtemp(prefix="grafo_prints_")
    legendas = {}
    try:
        dados = calcular_dados_reais()
        roteiros = montar_roteiros(dados, base_tmp)

        numero = 0
        for opcao, teste, respostas, legenda, esperado in roteiros:
            numero += 1
            pasta_id = f"{opcao}{teste}"
            caminho_copia = copiar_grafo(base_tmp, pasta_id)
            texto = rodar_sessao(respostas, caminho_copia)
            # audita a saída BRUTA (antes de truncar/recortar) contra o que
            # a legenda promete, para nunca publicar um print que mostra
            # um resultado diferente do anunciado.
            verificar(opcao, teste, texto, esperado)
            # só g) e h) produzem saídas muito longas (dump do arquivo,
            # lista/matriz de adjacência); as demais opções já são curtas
            # e truncá-las poderia esconder justamente o resultado do
            # teste (ex.: o resultado de "i" em roteiros com vários passos).
            # h) 2 (matriz) recebe um recorte específico de colunas, e não
            # só de linhas, porque a matriz completa (109 colunas) fica
            # larga demais para uma imagem legível.
            if opcao == "h" and teste == 2:
                texto = recortar_matriz(texto, dados["n"])
            elif opcao in ("g", "h"):
                texto = truncar(texto)

            nome_arquivo = f"{numero:02d}_opcao_{opcao}_teste{teste}.png"
            caminho_png = os.path.join(DESTINO, nome_arquivo)
            renderizar_png(texto, caminho_png)
            legendas[nome_arquivo] = legenda
            print(f"[{numero:02d}] {nome_arquivo}  ->  {legenda}")

        caminho_json = os.path.join(DESTINO, "legendas.json")
        with open(caminho_json, "w", encoding="utf-8") as arq:
            arq.write(json.dumps(legendas, ensure_ascii=False, indent=2) + "\n")
        print(f"\n{len(roteiros)} imagens geradas em {DESTINO}")
        print(f"Legendas salvas em {caminho_json}")
    finally:
        shutil.rmtree(base_tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
