# -*- coding: utf-8 -*-
"""
Projeto de Teoria dos Grafos - Parte 2
Descoberta Musical por Grafos: Álbuns, Artistas e Gêneros

Integrante: Luis Felipe Santos do Nascimento - RA 10420572

Síntese: gera o relatório final da Parte 2
(relatorio/Relatorio_Projeto_TG_Parte2.docx) a partir do template da
disciplina (cabeçalho, logotipo e estilos do Mackenzie). Todas as
estatísticas do grafo (n, m, quantidades por tipo e por relação, graus,
densidade, componentes, gêneros e artistas-ponte entre as cenas, exemplo
numérico de peso, distâncias em arestas) são CALCULADAS em tempo de
execução a partir de dados/grafo.txt (lido com a própria classe da
aplicação) e dos dados brutos do MusicBrainz (dados/brutos/*.json) -
nenhum número do grafo é digitado à mão. As figuras de teste do menu são
lidas de relatorio/figuras/prints (ordem alfabética, legendas em
legendas.json); o print do Gephi é lido de relatorio/figuras/gephi.png,
se existir, e, caso contrário, é deixado um marcador para inserção.

Uso: python3 ferramentas/gerar_relatorio.py

Histórico de alterações:
  28/09/2026 - Luis Felipe - criação
"""
import glob
import io
import json
import os
import subprocess
import sys
import unittest
from collections import Counter, defaultdict, deque

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image

RAIZ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(RAIZ, "src"))
sys.path.insert(0, os.path.join(RAIZ, "coleta"))
from arquivo_grafo import ler  # noqa: E402
from montar_grafo import afinidades, carregar_brutos, escolher_albuns, rotular_albuns  # noqa: E402

TEMPLATE = os.path.join(RAIZ, "..", "parte 2 projeto", "projetoTG_parte2_templateRelatorio.docx")
SAIDA = os.path.join(RAIZ, "relatorio", "Relatorio_Projeto_TG_Parte2.docx")
PASTA_PRINTS = os.path.join(RAIZ, "relatorio", "figuras", "prints")
FIG_GEPHI = os.path.join(RAIZ, "relatorio", "figuras", "gephi.png")
FIG_PLOTLY = os.path.join(RAIZ, "visualizacao", "grafo.png")
GITHUB = "https://github.com/luisfelipesdn12/grafo-musical-tg"

TITULO = "Descoberta Musical por Grafos: modelagem tripartida de álbuns, artistas e gêneros"
NOME = "Luis Felipe Santos do Nascimento"
RA = "10420572"
EMAIL = "10420572@mackenzista.com.br"
FONTE = "Arial"
NOMES_TIPO = {"ART": "Artista", "ALB": "Álbum", "GEN": "Gênero"}
NOMES_CENA = {"rnb": "R&B/hip-hop", "mpb": "MPB"}


# =====================================================================
# 1. Estatísticas (calculadas a partir dos dados)
# =====================================================================
def fmt(x, casas=2):
    """Número no padrão brasileiro (vírgula decimal)."""
    return f"{x:.{casas}f}".replace(".", ",")


def lista_pt(itens):
    """'a, b e c'."""
    itens = list(itens)
    return itens[0] if len(itens) == 1 else ", ".join(itens[:-1]) + " e " + itens[-1]


def bfs_dist(g, origem):
    """Distância em número de arestas de origem a todos os vértices (BFS)
    e o predecessor de cada vértice na árvore de busca."""
    dist = {origem: 0}
    pred = {origem: None}
    fila = deque([origem])
    while fila:
        v = fila.popleft()
        for w, _ in g.vizinhos(v):
            if w not in dist:
                dist[w] = dist[v] + 1
                pred[w] = v
                fila.append(w)
    return dist, pred


def calcular_estatisticas():
    g = ler(os.path.join(RAIZ, "dados", "grafo.txt"))
    brutos = carregar_brutos(os.path.join(RAIZ, "dados", "brutos"))
    e = {"g": g, "n": g.n, "m": g.m, "brutos": brutos}

    tipo = {v: g.tipoVertice(v) for v in range(g.n)}
    indice = {r: i for i, r in enumerate(g.rotulos)}
    e["por_tipo"] = Counter(tipo.values())
    rel = Counter()
    pesos_rel = defaultdict(list)
    for v in range(g.n):
        for w, p in g.vizinhos(v):
            if v < w:
                chave = "-".join(sorted([tipo[v], tipo[w]]))
                rel[chave] += 1
                pesos_rel[chave].append(p)
    e["por_relacao"] = rel
    e["pesos_rel"] = pesos_rel

    # graus por tipo
    graus = {}
    for t in ("ART", "ALB", "GEN"):
        vs = [v for v in range(g.n) if tipo[v] == t]
        gs = [g.grau(v) for v in vs]
        vmax = max(vs, key=lambda v: (g.grau(v), -v))
        graus[t] = {"media": sum(gs) / len(gs), "max": max(gs), "min": min(gs),
                    "vmax": g.rotulos[vmax]}
    e["graus"] = graus
    e["grau_medio"] = 2 * g.m / g.n
    e["densidade"] = 2 * g.m / (g.n * (g.n - 1))
    nA, nL, nG = e["por_tipo"]["ART"], e["por_tipo"]["ALB"], e["por_tipo"]["GEN"]
    e["m_max_tri"] = nA * nL + nA * nG + nL * nG
    e["densidade_tri"] = g.m / e["m_max_tri"]
    e["componentes"] = g.componentes()

    # cena (rnb/mpb) de cada artista e álbum
    cena_art = {f"[ART] {a['nome'].replace(chr(34), chr(39)).strip()}": a["cena"] for a in brutos}
    cena = {}
    artista_de = {}
    for v in range(g.n):
        if tipo[v] == "ART":
            cena[v] = cena_art[g.rotulos[v]]
    for v in range(g.n):
        if tipo[v] == "ALB":
            art = [w for w, _ in g.vizinhos(v) if tipo[w] == "ART"][0]
            artista_de[v] = art
            cena[v] = cena[art]
    e["cena"] = cena

    generos = [v for v in range(g.n) if tipo[v] == "GEN"]
    info_gen = []
    for v in generos:
        c = Counter(cena[w] for w, _ in g.vizinhos(v))
        info_gen.append({"v": v, "nome": g.rotulos[v][6:], "grau": g.grau(v),
                         "rnb": c["rnb"], "mpb": c["mpb"]})
    e["top_generos"] = sorted(info_gen, key=lambda x: (-x["grau"], x["nome"]))[:5]
    pontes = [x for x in info_gen if x["rnb"] and x["mpb"]]
    pontes.sort(key=lambda x: (-min(x["rnb"], x["mpb"]), -x["grau"], x["nome"]))
    e["generos_ponte"] = pontes
    e["generos_exclusivos"] = {c: sum(1 for x in info_gen if x[c] and not x[{"rnb": "mpb", "mpb": "rnb"}[c]])
                               for c in ("rnb", "mpb")}

    # artistas-ponte: força da ligação (artista + seus álbuns) com gêneros-ponte
    ids_ponte = {x["v"] for x in pontes}
    forca = defaultdict(lambda: {"arestas": 0, "afinidade": 0.0, "generos": set()})
    for v in range(g.n):
        if tipo[v] not in ("ART", "ALB"):
            continue
        dono = v if tipo[v] == "ART" else artista_de[v]
        for w, p in g.vizinhos(v):
            if w in ids_ponte:
                forca[dono]["arestas"] += 1
                forca[dono]["afinidade"] += 1 - p
                forca[dono]["generos"].add(g.rotulos[w][6:])
    artistas_ponte = []
    for c in ("rnb", "mpb"):
        lista = [(a, f) for a, f in forca.items() if cena[a] == c]
        lista.sort(key=lambda x: (-x[1]["afinidade"], -x[1]["arestas"], g.rotulos[x[0]]))
        for a, f in lista[:3]:
            artistas_ponte.append({"artista": g.rotulos[a][6:], "cena": c, "arestas": f["arestas"],
                                   "afinidade": f["afinidade"], "generos": sorted(f["generos"])})
    e["artistas_ponte"] = artistas_ponte

    # distâncias em arestas (BFS) - diâmetro, distância média e um caminho entre cenas
    soma, pares, diam, par_diam = 0, 0, 0, None
    for v in range(g.n):
        dist, _ = bfs_dist(g, v)
        for w, d in dist.items():
            if w > v:
                soma += d
                pares += 1
                if d > diam:
                    diam, par_diam = d, (v, w)
    e["dist_media"] = soma / pares
    e["diametro"] = diam
    e["par_diametro"] = (g.rotulos[par_diam[0]], g.rotulos[par_diam[1]])
    origem = indice.get("[ALB] Blonde — Frank Ocean",
                        next(v for v in range(g.n) if tipo[v] == "ALB" and cena[v] == "rnb"))
    candidatos = [v for v in range(g.n) if tipo[v] == "ALB" and cena[v] == "mpb"
                  and g.rotulos[v].endswith("Caetano Veloso")]
    destino = indice.get("[ALB] Transa — Caetano Veloso",
                         candidatos[0] if candidatos else
                         next(v for v in range(g.n) if tipo[v] == "ALB" and cena[v] == "mpb"))
    dist, pred = bfs_dist(g, origem)
    caminho, v = [], destino
    while v is not None:
        caminho.append(v)
        v = pred[v]
    caminho.reverse()
    e["caminho"] = [(g.rotulos[v], None if i == 0 else g.peso(caminho[i - 1], v))
                    for i, v in enumerate(caminho)]

    # coleta: álbuns brutos, com gênero e selecionados; votos por cena
    col = []
    votos_cena = defaultdict(list)
    sem_genero_cena = defaultdict(lambda: [0, 0])
    for a in brutos:
        sel = escolher_albuns(a["albuns"], 4)
        com_g = [x for x in a["albuns"] if x.get("genres")]
        col.append({"nome": a["nome"], "cena": a["cena"], "estudio": len(a["albuns"]),
                    "com_genero": len(com_g), "selecionados": len(sel),
                    "tags_artista": len(a["genres"])})
        sem_genero_cena[a["cena"]][0] += len(a["albuns"]) - len(com_g)
        sem_genero_cena[a["cena"]][1] += len(a["albuns"])
        for x in sel:
            votos_cena[a["cena"]].append(sum(t["count"] for t in x["genres"]))
    e["coleta"] = col
    e["votos_cena"] = {c: sum(v) / len(v) for c, v in votos_cena.items()}
    e["sem_genero_cena"] = dict(sem_genero_cena)
    e["data_coleta"] = sorted({a.get("coletado_em", "") for a in brutos})
    ag = [p for p in pesos_rel["ALB-GEN"] + pesos_rel["ART-GEN"]]
    e["gen_custo_zero"] = (sum(1 for p in ag if p == 0.0), len(ag))
    zero_cena = defaultdict(lambda: [0, 0])
    for v in range(g.n):
        if tipo[v] == "ALB":
            for w, p in g.vizinhos(v):
                if tipo[w] == "GEN":
                    zero_cena[cena[v]][1] += 1
                    zero_cena[cena[v]][0] += p == 0.0
    e["zero_cena"] = dict(zero_cena)

    # exemplo numérico: Blonde (Frank Ocean) e artista Tim Maia
    frank = next(a for a in brutos if a["nome"] == "Frank Ocean")
    blonde = next(x for x in frank["albuns"] if x["title"] == "Blonde")
    e["ex_album"] = ("Blonde", "Frank Ocean", blonde.get("first-release-date", "")[:4],
                     exemplo_pesos(g, indice, "[ALB] Blonde — Frank Ocean", blonde["genres"]))
    tim = next(a for a in brutos if a["nome"] == "Tim Maia")
    e["ex_artista"] = ("Tim Maia", exemplo_pesos(g, indice, "[ART] Tim Maia", tim["genres"]))
    sel_tim = escolher_albuns(tim["albuns"], 4)
    e["ex_tim_rotulos"] = rotular_albuns(sel_tim, "Tim Maia")
    return e


def exemplo_pesos(g, indice, rotulo, genres):
    """Linhas (gênero, votos, afinidade, peso, situação) de uma entidade."""
    top = dict(afinidades(genres, 5))
    maximo = max(t["count"] for t in genres)
    linhas = []
    v = indice[rotulo]
    for t in sorted(genres, key=lambda t: (-t["count"], t["name"])):
        rg = f"[GEN] {t['name']}"
        if t["name"] not in top:
            situacao = "fora do top-5 (descartada)"
            af = t["count"] / maximo
            peso = None
        elif rg not in indice:
            situacao = "gênero com < 2 ligações (não vira vértice)"
            af = top[t["name"]]
            peso = None
        else:
            af = top[t["name"]]
            peso = g.peso(v, indice[rg])
            situacao = "aresta no grafo"
        linhas.append((t["name"], t["count"], maximo, af, peso, situacao))
    return linhas


def rodar_testes():
    """Executa a suíte unittest do projeto e devolve (por_arquivo, total, ok)."""
    pasta = os.path.join(RAIZ, "testes")
    sys.path.insert(0, pasta)
    suite = unittest.TestLoader().discover(pasta, top_level_dir=pasta)
    por_arquivo = Counter()

    def varrer(s):
        for t in s:
            if isinstance(t, unittest.TestSuite):
                varrer(t)
            else:
                por_arquivo[t.id().split(".")[0]] += 1
    varrer(suite)
    buf = io.StringIO()
    res = unittest.TextTestRunner(stream=buf, verbosity=0).run(suite)
    return por_arquivo, res.testsRun, res.wasSuccessful()


def historico_git():
    try:
        saida = subprocess.run(["git", "-C", RAIZ, "log", "--reverse", "--date=format:%d/%m/%Y",
                                "--format=%ad|%h|%s"], capture_output=True, text=True, check=True)
        return [linha.split("|", 2) for linha in saida.stdout.splitlines() if linha]
    except (OSError, subprocess.CalledProcessError):
        return []


# =====================================================================
# 2. Auxiliares de formatação (python-docx)
# =====================================================================
class Relatorio:
    def __init__(self, doc):
        self.doc = doc
        self.nfig = 0
        self.ntab = 0
        self._estilos()

    def _estilos(self):
        estilos = self.doc.styles
        for nome, tam, nivel in (("Heading 1", 13, 0), ("Heading 2", 12, 1)):
            try:
                st = estilos[nome]
            except KeyError:
                st = estilos.add_style(nome, WD_STYLE_TYPE.PARAGRAPH)
            st.base_style = estilos["Normal"]
            st.font.name = FONTE
            st.font.size = Pt(tam)
            st.font.bold = True
            st.font.color.rgb = RGBColor(0, 0, 0)
            pf = st.paragraph_format
            pf.space_before = Pt(14 if nivel == 0 else 10)
            pf.space_after = Pt(6)
            pf.keep_with_next = True
            ppr = st.element.get_or_add_pPr()
            ol = OxmlElement("w:outlineLvl")
            ol.set(qn("w:val"), str(nivel))
            ppr.append(ol)
            st.element.get_or_add_rPr()
            rfonts = st.element.rPr.find(qn("w:rFonts"))
            if rfonts is None:
                rfonts = OxmlElement("w:rFonts")
                st.element.rPr.append(rfonts)
            for att in ("w:ascii", "w:hAnsi", "w:cs"):
                rfonts.set(qn(att), FONTE)

    # ---- texto
    def _runs(self, p, texto, tam=11, italico=False):
        """Aceita **negrito** e _itálico_ simples dentro do texto."""
        partes = texto.split("**")
        for i, parte in enumerate(partes):
            sub = parte.split("__")
            for j, s in enumerate(sub):
                if not s:
                    continue
                r = p.add_run(s)
                r.font.name = FONTE
                r._element.rPr.rFonts.set(qn("w:hAnsi"), FONTE)
                r.font.size = Pt(tam)
                r.bold = i % 2 == 1
                r.italic = italico or j % 2 == 1
        return p

    def par(self, texto, recuo=True, alinhamento=WD_ALIGN_PARAGRAPH.JUSTIFY, tam=11,
            italico=False, depois=6):
        p = self.doc.add_paragraph()
        p.alignment = alinhamento
        pf = p.paragraph_format
        pf.first_line_indent = Cm(1.25) if recuo else None
        pf.space_after = Pt(depois)
        pf.line_spacing = 1.15
        return self._runs(p, texto, tam, italico)

    def item(self, texto, marcador="•"):
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        pf = p.paragraph_format
        pf.left_indent = Cm(1.0)
        pf.first_line_indent = Cm(-0.5)
        pf.space_after = Pt(3)
        pf.line_spacing = 1.15
        return self._runs(p, f"{marcador}\t{texto}" if marcador else texto)

    def h1(self, texto):
        p = self.doc.add_paragraph(texto.upper(), style="Heading 1")
        return p

    def h2(self, texto):
        return self.doc.add_paragraph(texto, style="Heading 2")

    def quebra(self):
        self.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    def legenda(self, texto, antes=6):
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(antes)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        rotulo, _, resto = texto.partition(" – ")
        r = self._runs(p, f"**{rotulo}** – {resto}" if resto else texto, tam=10)
        return r

    def fonte(self, texto="Fonte: autoria própria."):
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(10)
        return self._runs(p, texto, tam=9)

    # ---- tabelas e figuras
    def tabela(self, titulo, cabecalho, linhas, larguras=None, fonte="Fonte: autoria própria.",
               tam=9):
        self.ntab += 1
        self.legenda(f"Tabela {self.ntab} – {titulo}")
        t = self.doc.add_table(rows=1, cols=len(cabecalho))
        t.style = self.doc.styles["Table Grid"]
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for c, texto in enumerate(cabecalho):
            cel = t.rows[0].cells[c]
            cel.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            self._runs(cel.paragraphs[0], f"**{texto}**", tam=tam)
            sombra = OxmlElement("w:shd")
            sombra.set(qn("w:val"), "clear")
            sombra.set(qn("w:fill"), "D9D9D9")
            cel._tc.get_or_add_tcPr().append(sombra)
        # repete o cabeçalho em quebras de página
        trpr = t.rows[0]._tr.get_or_add_trPr()
        th = OxmlElement("w:tblHeader")
        th.set(qn("w:val"), "true")
        trpr.append(th)
        for linha in linhas:
            cels = t.add_row().cells
            for c, texto in enumerate(linha):
                self._runs(cels[c].paragraphs[0], str(texto), tam=tam)
        if larguras:
            t.autofit = False
            for c, larg in enumerate(larguras):
                t.columns[c].width = Cm(larg)
            for linha in t.rows:
                for c, larg in enumerate(larguras):
                    linha.cells[c].width = Cm(larg)
        if len(linhas) <= 16:  # tabela curta: não quebra entre páginas
            for linha in t.rows[:-1]:
                for cel in linha.cells:
                    for par in cel.paragraphs:
                        par.paragraph_format.keep_with_next = True
        self.fonte(fonte)
        return t

    def figura(self, caminho, titulo, fonte="Fonte: autoria própria.", largura_max=15.5,
               altura_max=11.5):
        self.nfig += 1
        self.legenda(f"Figura {self.nfig} – {titulo}")
        w, h = Image.open(caminho).size
        largura = min(largura_max, altura_max * w / h)
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.space_after = Pt(2)
        p.add_run().add_picture(caminho, width=Cm(largura))
        self.fonte(fonte)

    def figuras_lado_a_lado(self, itens, largura=7.7, altura_max=19.0):
        """Duas figuras em colunas (tabela sem bordas), cada uma com a sua
        legenda numerada e a fonte - usado para capturas de tela altas."""
        t = self.doc.add_table(rows=1, cols=len(itens))
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        for c, (caminho, titulo) in enumerate(itens):
            self.nfig += 1
            cel = t.rows[0].cells[c]
            cel.width = Cm(largura + 0.3)
            t.columns[c].width = Cm(largura + 0.3)
            p = cel.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(3)
            rotulo = f"Figura {self.nfig}"
            self._runs(p, f"**{rotulo}** – {titulo}", tam=9)
            w, h = Image.open(caminho).size
            larg = min(largura, altura_max * w / h)
            p2 = cel.add_paragraph()
            p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p2.add_run().add_picture(caminho, width=Cm(larg))
            p3 = cel.add_paragraph()
            p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
            self._runs(p3, "Fonte: autoria própria.", tam=9)
        # linha não se divide entre páginas
        trpr = t.rows[0]._tr.get_or_add_trPr()
        cs = OxmlElement("w:cantSplit")
        cs.set(qn("w:val"), "true")
        trpr.append(cs)
        self.doc.add_paragraph().paragraph_format.space_after = Pt(4)

    def marcador_figura(self, titulo, texto):
        self.nfig += 1
        self.legenda(f"Figura {self.nfig} – {titulo}")
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = self._runs(p, f"**{texto}**", tam=11)
        for run in r.runs:
            run.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
        self.fonte("Fonte: autoria própria, dados do MusicBrainz.")


# =====================================================================
# 3. Preparação do template
# =====================================================================
def trocar_texto(p, texto):
    """Troca o texto do parágrafo mantendo a formatação do 1º run."""
    runs = p.runs
    runs[0].text = texto
    for r in runs[1:]:
        r._element.getparent().remove(r._element)


def preparar_template():
    doc = Document(TEMPLATE)
    corpo = doc.element.body
    elems = list(corpo)
    # mantém: parágrafos 0-4 (título "Relatório do Projeto" / "Parte"), tabela
    # de integrantes e o título grande "Relatório"; apaga as instruções
    tabela = doc.tables[0]._tbl
    pos_tab = elems.index(tabela)
    for el in elems[pos_tab + 3:]:
        if el.tag != qn("w:sectPr"):
            corpo.remove(el)
    ps = doc.paragraphs
    trocar_texto(ps[3], "Parte 2")
    trocar_texto(ps[6], TITULO)   # parágrafo que continha "Relatório"
    # tabela de integrantes: 1 linha preenchida
    t = doc.tables[0]
    for linha in list(t.rows)[2:]:
        t._tbl.remove(linha._tr)
    for c, texto in enumerate((NOME, RA)):
        cel = t.rows[1].cells[c]
        par = cel.paragraphs[0]
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = par.add_run(texto)
        r.font.name = FONTE
        r.font.size = Pt(10)
    # corrige a grafia "Teoría" do cabeçalho original do template
    for secao in doc.sections:
        for par in secao.header.paragraphs:
            for r in par.runs:
                if "Teoría" in r.text:
                    r.text = r.text.replace("Teoría", "Teoria")
    # margem superior maior: o cabeçalho do template (4 linhas + logotipos)
    # invadia o corpo do texto nas páginas seguintes
    for secao in doc.sections:
        secao.top_margin = Cm(3.6)
    # numeração de página no rodapé
    rodape = doc.sections[0].footer
    p = rodape.paragraphs[0] if rodape.paragraphs else rodape.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = p.add_run()
    for tipo, texto in (("begin", None), (None, "PAGE"), ("end", None)):
        if tipo:
            fc = OxmlElement("w:fldChar")
            fc.set(qn("w:fldCharType"), tipo)
            run._r.append(fc)
        else:
            it = OxmlElement("w:instrText")
            it.set(qn("xml:space"), "preserve")
            it.text = texto
            run._r.append(it)
    run.font.name = FONTE
    run.font.size = Pt(9)
    return doc


# =====================================================================
# 4. Conteúdo
# =====================================================================
def escrever(doc, e):
    R = Relatorio(doc)
    g = e["g"]
    pt, pr = e["por_tipo"], e["por_relacao"]
    comp = e["componentes"]
    conexo = len(comp) == 1

    # ---------------------------------------------------------- identificação
    R.par(f"**Integrante:** {NOME} – RA {RA} – {EMAIL}", recuo=False,
          alinhamento=WD_ALIGN_PARAGRAPH.CENTER, depois=2, tam=10)
    R.par("Ciência da Computação – Turma 6ºD – Teoria dos Grafos – "
          "Prof. Dr. Ivan Carlos Alcântara de Oliveira", recuo=False,
          alinhamento=WD_ALIGN_PARAGRAPH.CENTER, depois=2, tam=10)
    R.par("Faculdade de Computação e Informática – Universidade Presbiteriana Mackenzie – "
          "São Paulo, setembro de 2026", recuo=False, alinhamento=WD_ALIGN_PARAGRAPH.CENTER,
          depois=10, tam=10)
    R.par(f"**Título da aplicação:** Descoberta Musical por Grafos – Álbuns, Artistas e Gêneros. "
          f"**Repositório:** {GITHUB}", recuo=False, alinhamento=WD_ALIGN_PARAGRAPH.CENTER,
          depois=12)

    # ---------------------------------------------------------- resumo
    R.h1("Resumo")
    R.par(
        "Este relatório apresenta a segunda parte do projeto da disciplina de Teoria dos Grafos: "
        "a modelagem, como grafo, de um problema real de descoberta musical. Atendendo ao parecer "
        "da Parte 1, o escopo foi reduzido e os usuários foram retirados do modelo; o grafo passou "
        "a conter exclusivamente álbuns, artistas e gêneros, obtidos de metadados públicos da base "
        f"colaborativa MusicBrainz (MUSICBRAINZ, [2026]). A partir de {len(e['coleta'])} artistas "
        "semente – oito do R&B alternativo/hip-hop norte-americano e oito da Música Popular "
        f"Brasileira (MPB) – foi construído um grafo tripartido, não orientado e ponderado nas "
        f"arestas (tipo 2), com {e['n']} vértices ({pt['ART']} artistas, {pt['ALB']} álbuns e "
        f"{pt['GEN']} gêneros) e {e['m']} arestas. O peso de cada aresta é um custo de descoberta, "
        "definido como 1 menos a afinidade entre as entidades, em que a afinidade de gênero é "
        "derivada dos votos da comunidade do MusicBrainz. O grafo é representado por matriz de "
        "adjacência em Python, manipulado por uma aplicação de console com menu de dez opções "
        "(leitura e gravação de arquivo, inserção e remoção de vértices e arestas, exibição e "
        f"conexidade) e validado por {e['testes_total']} testes automatizados. A análise mostra "
        f"um grafo {'conexo' if conexo else 'desconexo'}, de densidade {fmt(e['densidade'], 3)}, "
        f"em que gêneros como {', '.join(x['nome'] for x in e['generos_ponte'][:3])} funcionam "
        "como pontes entre as duas cenas musicais. A próxima etapa aplicará o algoritmo de "
        "Dijkstra para encontrar a trilha de descoberta de menor custo entre dois álbuns.")
    R.par("**Palavras-chave:** teoria dos grafos; grafo tripartido; matriz de adjacência; "
          "descoberta musical; MusicBrainz.", recuo=False)

    # ---------------------------------------------------------- 1 introdução
    R.h1("1 Introdução")
    R.h2("1.1 Contextualização")
    R.par(
        "A forma de consumir música mudou profundamente com as plataformas de streaming. O "
        "acesso a catálogos com dezenas de milhões de faixas ampliou a oferta, mas também tornou "
        "a descoberta de novos artistas dependente de sistemas de recomendação e de listas "
        "automáticas. Datta, Knox e Bronnenberg (2018) mostram que a adoção do streaming altera "
        "de forma mensurável o que as pessoas ouvem e a variedade do que descobrem. Nesse "
        "cenário, entender como álbuns, artistas e gêneros se relacionam é um problema "
        "computacional concreto: as relações entre essas entidades formam naturalmente uma rede, "
        "e a Teoria dos Grafos oferece o vocabulário e os algoritmos para representá-la e "
        "percorrê-la (BONDY; MURTY, 2010).")
    R.par(
        "Este projeto é a versão reduzida, para a disciplina, do Trabalho de Conclusão de Curso "
        "do autor, que estuda uma plataforma social de álbuns com usuários reais. Aqui fica "
        "apenas a camada de conteúdo – álbum, artista e gênero –, que é pública, não envolve "
        "dados pessoais e já basta para um problema de grafos bem delimitado.")
    R.h2("1.2 Justificativa")
    R.par(
        "Metadados musicais públicos, como os do MusicBrainz, registram não só quem gravou cada "
        "álbum, mas também como a comunidade classifica álbuns e artistas em gêneros, por meio "
        "de votos. Essa informação permite medir quão fortemente um álbum pertence a um gênero e, "
        "portanto, quão \"perto\" dois álbuns estão um do outro passando por gêneros e artistas "
        "em comum. Um grafo ponderado com esses dados permite responder a perguntas de "
        "descoberta – por exemplo, quais gêneros ligam o R&B contemporâneo à MPB dos anos 1970 – "
        "sem depender de histórico de usuários, o que evita o problema de partida a frio "
        "(cold start) dos sistemas de recomendação baseados em interação (LIKA; KOLOMVATSOS; "
        "HADJIEFTHYMIADES, 2014) e dispensa o tratamento de dados pessoais regulado pela Lei "
        "Geral de Proteção de Dados (BRASIL, 2018).")
    R.h2("1.3 Objetivo")
    R.par(
        "**Objetivo geral:** modelar, como grafo tripartido ponderado, as relações entre álbuns, "
        "artistas e gêneros de duas cenas musicais reais e desenvolver um protótipo que carregue, "
        "edite, exiba e analise esse grafo, preparando a função central do próximo bimestre: a "
        "\"trilha de descoberta\" de menor custo entre dois álbuns.")
    R.par("**Objetivos específicos:**", recuo=False, depois=3)
    for texto in (
            "coletar, da API pública do MusicBrainz, os álbuns de estúdio e os votos de gênero de "
            "16 artistas semente, sem nenhum dado de usuário;",
            "definir com precisão os tipos de vértice, os tipos de aresta e o significado do peso;",
            "gerar o arquivo grafo.txt (tipo 2) com pelo menos 80 vértices e 200 arestas;",
            "implementar a classe do grafo por matriz de adjacência e a aplicação com menu a–j;",
            "testar a aplicação e analisar a estrutura do grafo (graus, densidade, conexidade e "
            "gêneros que ligam as cenas)."):
        R.item(texto)
    R.h2("1.4 Atendimento ao parecer da Parte 1")
    R.par(
        "A proposta da Parte 1 recebeu nota 8,0, com a recomendação de reduzir o escopo, retirar "
        f"os usuários e trabalhar \"exclusivamente com álbuns, artistas e gêneros\". A Tabela {R.ntab + 1} "
        "relaciona cada ponto do parecer à resposta dada nesta etapa.")
    R.tabela(
        "Pontos do parecer da Parte 1 e como foram atendidos",
        ["Ponto do parecer", "Resposta na Parte 2", "Onde"],
        [["Escopo amplo demais (plataforma social, recomendação, comunidades, clusterização)",
          "Escopo reduzido a um problema central: modelar a rede álbum–artista–gênero e, na "
          "próxima etapa, encontrar a trilha de descoberta de menor custo (Dijkstra).",
          "Seções 1.3 e 7"],
         ["Evitar coleta de usuários (procedimentos éticos)",
          "Usuários retirados do modelo; apenas metadados públicos de álbuns, artistas e "
          "gêneros do MusicBrainz.", "Seções 4 e 5.1"],
         ["Definir precisamente os tipos de vértice e de aresta",
          "Três tipos de vértice com prefixo no rótulo e três tipos de aresta com semântica "
          "própria; arestas entre vértices do mesmo tipo são proibidas.", "Seção 5.2, Tabelas 3 e 4"],
         ["Explicar o significado dos pesos",
          "Peso = custo de descoberta = 1 − afinidade; afinidade calculada a partir dos votos "
          "de gênero, com exemplo numérico real.", "Seção 5.2, Tabela 5"],
         ["Garantir ≥ 80 vértices e ≥ 200 arestas",
          f"Grafo real com {e['n']} vértices e {e['m']} arestas, verificado por teste automático.",
          "Seções 5.5 e 5.6"],
         ["Contextualização extensa em relação à delimitação computacional",
          "Contextualização reduzida e voltada ao problema computacional.", "Seção 1.1"]],
        larguras=[5.0, 8.5, 2.5])

    # ---------------------------------------------------------- 2 fundamentação
    R.h1("2 Fundamentação teórica")
    R.par(
        "Um **grafo** G = (V, E) é formado por um conjunto de vértices V e um conjunto de arestas "
        "E, em que cada aresta liga um par de vértices (BONDY; MURTY, 2010; DIESTEL, 2010). O "
        "grafo é **não orientado** quando a aresta {v, w} não tem sentido, isto é, liga v a w e "
        "w a v ao mesmo tempo; é **ponderado nas arestas** quando cada aresta recebe um valor "
        "numérico (peso ou custo). Na classificação usada na disciplina, um grafo não orientado "
        "com peso nas arestas é do **tipo 2**, que é o tipo adotado neste projeto.")
    R.par(
        "Um grafo é **k-partido** quando seus vértices podem ser divididos em k conjuntos "
        "disjuntos de modo que nenhuma aresta ligue dois vértices do mesmo conjunto; com k = 3, "
        "diz-se **tripartido**. Redes com vários tipos de vértice e de aresta também são "
        "estudadas como redes de informação heterogêneas, em que o tipo de cada elemento carrega "
        "significado e orienta a análise (SHI et al., 2017).")
    R.par(
        "O **grau** d(v) de um vértice é o número de arestas incidentes a ele; em um grafo não "
        "orientado, a soma dos graus é 2m, em que m é o número de arestas, de modo que o grau "
        "médio é 2m/n. A **densidade** de um grafo simples é a razão entre o número de arestas "
        "existentes e o máximo possível, 2m/(n(n − 1)). Um **caminho** é uma sequência de "
        "vértices em que vértices consecutivos são adjacentes; seu comprimento é o número de "
        "arestas e, em grafos ponderados, seu custo é a soma dos pesos. A **distância** entre "
        "dois vértices é o comprimento do menor caminho entre eles, e o **diâmetro** é a maior "
        "distância entre pares de vértices.")
    R.par(
        "Um grafo não orientado é **conexo** quando existe caminho entre todo par de vértices; "
        "caso contrário, divide-se em **componentes conexas**, subgrafos conexos maximais. As "
        "componentes podem ser encontradas por **busca em largura** (BFS): a partir de um "
        "vértice não visitado, visitam-se todos os alcançáveis, camada a camada, usando uma fila; "
        "cada busca iniciada em um vértice ainda não visitado revela uma nova componente "
        "(CORMEN et al., 2001; SZWARCFITER, 1988). As categorias de conexidade C0 a C3, o "
        "algoritmo FCONEX e o **grafo reduzido** dizem respeito a grafos orientados, em que a "
        "alcançabilidade depende do sentido das arestas; por isso não se aplicam a este grafo, "
        "que é não orientado.")
    R.par(
        "Um grafo pode ser armazenado por **matriz de adjacência** – uma matriz n × n em que a "
        "posição (i, j) indica a aresta entre i e j – ou por **lista de adjacência**, que guarda "
        "para cada vértice apenas os seus vizinhos. A matriz ocupa O(n²) de memória, mas responde "
        "em O(1) se uma aresta existe e qual o seu peso; a lista ocupa O(n + m) e é mais econômica "
        "em grafos esparsos (CORMEN et al., 2001). Em um grafo não orientado a matriz é "
        "simétrica. Com n na casa das centenas, a matriz cabe com folga na memória e segue a "
        "estrutura trabalhada em aula, razão pela qual foi escolhida.")
    R.par(
        "Por fim, o problema do **caminho mínimo** busca o caminho de menor custo entre dois "
        "vértices. O algoritmo de Dijkstra o resolve quando todos os pesos são não negativos "
        "(CORMEN et al., 2001). Esse requisito orientou a definição do peso deste projeto como "
        "custo em [0, 1], e não como similaridade: quanto menor o peso, mais próximas estão as "
        "entidades, e um caminho de custo baixo corresponde a uma sequência de passos de "
        "descoberta \"naturais\".")

    # ---------------------------------------------------------- 3 trabalhos relacionados
    R.h1("3 Trabalhos relacionados")
    R.par(
        "Grafos bipartidos e multipartidos são a base de vários sistemas de recomendação em larga "
        "escala. O **GraphJet**, do Twitter, mantém em memória um grafo bipartido de interações "
        "entre usuários e tweets e gera recomendações em tempo real por meio de passeios "
        "aleatórios nesse grafo (SHARMA et al., 2016). O **Pixie**, do Pinterest, também usa "
        "passeios aleatórios com reinício sobre um grafo bipartido de pins e quadros para "
        "recomendar conteúdo a centenas de milhões de usuários (EKSOMBATCHAI et al., 2018). Já o "
        "**PinSage** combina essa estrutura com redes neurais convolucionais em grafos, "
        "aprendendo representações dos itens a partir da vizinhança amostrada por passeios "
        "aleatórios (YING et al., 2018).")
    R.par(
        "No estudo da estrutura de grandes redes, Ugander et al. (2011) analisaram o grafo "
        "social do Facebook – distribuição de graus, distâncias e conexidade – e mostraram que "
        "quase todos os usuários ativos pertencem a uma única componente gigante. Blondel et al. "
        "(2008) propuseram o método de Louvain, que detecta comunidades maximizando a "
        "modularidade e é aplicável a redes com milhões de vértices. Shi et al. (2017) revisam a "
        "análise de redes de informação heterogêneas, nas quais vértices e arestas de tipos "
        "diferentes – como autor, obra e tema – são tratados de forma distinta, exatamente o "
        "caso do grafo álbum–artista–gênero deste projeto.")
    R.par(
        "No domínio musical, Van den Oord, Dieleman e Schrauwen (2013) recomendam músicas a "
        "partir do conteúdo de áudio para contornar a falta de histórico de uso; o presente "
        "projeto persegue o mesmo objetivo – recomendar sem dados de usuário – usando, em vez do "
        "áudio, a estrutura de metadados. A fonte de dados é o MusicBrainz, enciclopédia musical "
        "aberta e colaborativa mantida pela MetaBrainz Foundation, que expõe artistas, grupos de "
        "lançamento (álbuns) e gêneros votados pela comunidade por meio de uma API web pública "
        "(MUSICBRAINZ, [2026]). Diferentemente dos sistemas citados, que operam com bilhões de "
        "arestas e dados de interação, este trabalho é um protótipo didático, com dados "
        "exclusivamente públicos e foco em uma modelagem explícita e interpretável dos pesos.")

    # ---------------------------------------------------------- 4 metodologia
    R.h1("4 Metodologia")
    R.par("O trabalho foi organizado em oito etapas, todas automatizadas por scripts do "
          "repositório, de modo que qualquer resultado deste relatório pode ser reproduzido:")
    for texto in (
            "**Seleção da semente:** 16 artistas escolhidos pelo autor, oito de R&B "
            "alternativo/hip-hop e oito de MPB, registrados em coleta/artistas_semente.txt com a "
            "cena de cada um. Quando a busca por nome encontra um homônimo (Steve Lacy, o "
            "saxofonista de jazz, em vez do músico de R&B), o identificador (MBID) é fixado no "
            "arquivo.",
            "**Coleta:** coleta/coletar_musicbrainz.py consulta a API do MusicBrainz, respeitando "
            "o limite de uma requisição por segundo, e grava um JSON por artista em "
            "dados/brutos, com os gêneros votados do artista e de cada álbum de estúdio.",
            "**Filtragem:** apenas grupos de lançamento do tipo primário \"Album\" sem tipo "
            "secundário (excluem-se coletâneas, discos ao vivo e trilhas); por entidade, apenas "
            "os cinco gêneros mais votados; por artista, até quatro álbuns com gênero, os mais "
            "votados primeiro.",
            "**Construção:** coleta/montar_grafo.py cria os vértices e as arestas, calcula os "
            "pesos, descarta gêneros ligados a menos de duas entidades e grava dados/grafo.txt, "
            "dados/vertices.csv e dados/arestas.csv.",
            "**Validação:** o script verifica n ≥ 80 e m ≥ 200 e os testes conferem o tipo 2 e a "
            "tripartição; a leitura com a própria classe da aplicação garante que o arquivo é "
            "válido.",
            "**Aplicação:** src/app.py oferece o menu a–j sobre a classe GrafoMatrizPonderado.",
            "**Testes:** testes automatizados com unittest e roteiros de uso do menu, "
            "registrados em imagens (ao menos dois testes por opção).",
            "**Visualização e análise:** visualizacao/visualizar.py desenha o grafo (Plotly) e o "
            "exporta para o Gephi; ferramentas/gerar_relatorio.py calcula as estatísticas e "
            "gera este relatório."):
        R.item(texto)

    # ---------------------------------------------------------- 5 resultados
    R.h1("5 Resultados parciais")
    R.h2("5.1 Coleta dos dados")
    total_est = sum(c["estudio"] for c in e["coleta"])
    total_cg = sum(c["com_genero"] for c in e["coleta"])
    total_sel = sum(c["selecionados"] for c in e["coleta"])
    menos4 = [c["nome"] for c in e["coleta"] if c["selecionados"] < 4]
    R.par(
        f"A coleta foi feita em {', '.join(d.split('-')[2] + '/' + d.split('-')[1] + '/' + d.split('-')[0] for d in e['data_coleta'] if d)} "
        "pela API web do MusicBrainz, que devolve JSON e não exige autenticação. Para cada "
        "artista, o coletor (i) busca o identificador pelo nome, (ii) obtém os gêneros votados "
        "do artista e (iii) pagina os grupos de lançamento do tipo álbum, pedindo os gêneros de "
        "cada um. O campo de gêneros da API contém apenas as etiquetas (tags) que constam na "
        "lista oficial de gêneros do MusicBrainz, cada uma com o número de votos recebidos. "
        f"Ao todo foram obtidos {total_est} álbuns de estúdio, dos quais {total_cg} têm ao menos "
        f"um gênero votado; após a filtragem, {total_sel} álbuns entraram no grafo. "
        + (f"Os artistas {', '.join(menos4)} têm menos de quatro álbuns com gênero votado e, por "
           "isso, contribuem com menos álbuns. " if menos4 else "")
        + f"A Tabela {R.ntab + 1} resume a coleta por artista.")
    R.tabela(
        "Resumo da coleta por artista semente",
        ["Artista", "Cena", "Álbuns de estúdio", "Com gênero votado", "No grafo",
         "Gêneros do artista"],
        [[c["nome"], NOMES_CENA[c["cena"]], c["estudio"], c["com_genero"], c["selecionados"],
          c["tags_artista"]] for c in e["coleta"]]
        + [["Total", "", total_est, total_cg, total_sel, ""]],
        larguras=[4.2, 2.6, 2.3, 2.5, 1.7, 2.4],
        fonte="Fonte: autoria própria, dados do MusicBrainz.")

    R.h2("5.2 Modelagem do problema como grafo")
    R.par(
        "O problema é modelado como um grafo **tripartido, não orientado e ponderado nas arestas "
        "(tipo 2)**. As três partes são os artistas, os álbuns e os gêneros; o tipo de cada "
        f"vértice fica codificado no próprio rótulo, por um prefixo, e a Tabela {R.ntab + 1} apresenta essa "
        "definição com as quantidades reais do grafo.")
    R.tabela(
        "Tipos de vértice",
        ["Tipo", "Prefixo do rótulo", "Significado", "Exemplo", "Quantidade"],
        [["Artista", "[ART]", "Artista semente (pessoa ou grupo) de uma das duas cenas",
          "[ART] Gal Costa", pt["ART"]],
         ["Álbum", "[ALB]", "Álbum de estúdio do artista (grupo de lançamento), no formato "
          "título — artista", "[ALB] Blonde — Frank Ocean", pt["ALB"]],
         ["Gênero", "[GEN]", "Gênero musical oficial do MusicBrainz ligado a pelo menos duas "
          "entidades", "[GEN] tropicália", pt["GEN"]],
         ["Total", "", "", "", e["n"]]],
        larguras=[1.6, 1.8, 6.0, 4.4, 2.2])
    R.par(
        f"Há três tipos de aresta, um para cada par de partes (Tabela {R.ntab + 1}). O peso de toda aresta é "
        "um **custo de descoberta**: peso = 1 − a, arredondado a duas casas, em que a ∈ (0, 1] é "
        "a **afinidade** entre as duas entidades. Para as arestas de gênero, a afinidade é "
        "relativa ao gênero mais votado da própria entidade: a(e, g) = votos(e, g) / "
        "max votos(e, g′), considerando apenas os cinco gêneros mais votados da entidade e "
        "desempatando por ordem alfabética.")
    cz, ct = e["gen_custo_zero"]
    R.tabela(
        "Tipos de aresta, semântica e peso",
        ["Relação", "Semântica", "Afinidade a", "Peso (custo)", "Quantidade"],
        [["Álbum – Artista", "Autoria: o álbum foi gravado pelo artista", "1,0 (sempre)", "0,00",
          pr["ALB-ART"]],
         ["Álbum – Gênero", "A comunidade classifica o álbum no gênero",
          "votos(álbum, g) / máx. de votos do álbum", "1 − a ∈ [0; 1)", pr["ALB-GEN"]],
         ["Artista – Gênero", "O artista transita pelo gênero ao longo da carreira",
          "votos(artista, g) / máx. de votos do artista", "1 − a ∈ [0; 1)", pr["ART-GEN"]],
         ["Total", "", "", "", e["m"]]],
        larguras=[2.6, 4.6, 4.0, 2.4, 2.4])
    R.par(
        f"**Exemplo numérico com dados reais.** A Tabela {R.ntab + 1} mostra o cálculo para o álbum "
        f"{e['ex_album'][0]} ({e['ex_album'][1]}, {e['ex_album'][2]}). O gênero mais votado dá o "
        "denominador; cada gênero recebe afinidade proporcional aos seus votos e o peso da "
        "aresta é o complemento dessa afinidade.")
    linhas = []
    for nome, votos, maximo, af, peso, sit in e["ex_album"][3]:
        linhas.append([nome, votos, f"{votos}/{maximo} = {fmt(af)}",
                       "—" if peso is None else f"1 − {fmt(af)} = {fmt(peso)}", sit])
    R.tabela(f"Cálculo dos pesos das arestas de gênero do álbum {e['ex_album'][0]}",
             ["Gênero", "Votos", "Afinidade", "Peso", "Situação"], linhas,
             larguras=[3.4, 1.4, 3.0, 3.2, 5.0],
             fonte="Fonte: autoria própria, dados do MusicBrainz.")
    ex = e["ex_album"][3]
    R.par(
        f"Assim, o caminho que vai de {e['ex_album'][0]} ao gênero {ex[0][0]} tem custo "
        f"{fmt(ex[0][4] or 0)} (é a classificação mais forte do álbum), enquanto a ligação com "
        f"{ex[-1][0]} custa {fmt(ex[-1][4]) if ex[-1][4] is not None else '—'}. A aresta de "
        "autoria Blonde – Frank Ocean tem custo 0,00, a ligação mais forte possível. O mesmo "
        "cálculo vale para artistas: com o artista Tim Maia, todos os gêneros votados têm o "
        "mesmo número de votos e, por isso, todas as suas arestas de gênero recebem custo 0,00 – "
        "um efeito da escassez de votos discutido na Seção 5.5.")
    R.par("**Justificativas de modelagem.**", recuo=False, depois=3)
    for texto in (
            "**Não orientado:** as relações de autoria e de classificação são simétricas – se o "
            "álbum pertence ao gênero, o gênero contém o álbum –, e a descoberta pode percorrê-las "
            "nos dois sentidos.",
            "**Peso na aresta (e não no vértice):** o que varia é a força da ligação entre duas "
            "entidades (quantos votos a comunidade deu àquele gênero para aquele álbum), e não "
            "uma propriedade isolada de um vértice. Por isso o tipo é o 2.",
            "**Tripartido:** duas entidades do mesmo tipo nunca se ligam diretamente; a "
            "proximidade entre dois álbuns surge por meio de um artista ou de um gênero em "
            "comum. Isso deixa cada aresta com uma semântica única e verificável, que a classe "
            "do grafo impõe ao recusar arestas entre vértices do mesmo tipo.",
            "**Custo = 1 − afinidade:** o custo é não negativo e menor para ligações mais "
            "fortes, requisito do algoritmo de Dijkstra, que será aplicado na próxima etapa para "
            "achar a trilha de descoberta de menor custo.",
            "**\"Sem aresta\" = None:** como custo 0,00 é um peso válido (autoria, gênero mais "
            "votado), o valor 0 não pode significar ausência de aresta na matriz; usa-se o "
            "valor None do Python.",
            "**Filtros:** limitar a cinco gêneros por entidade e exigir que o gênero ligue ao "
            "menos duas entidades elimina etiquetas isoladas, que não contribuiriam para "
            "nenhum caminho entre entidades diferentes."):
        R.item(texto)

    R.h2("5.3 Representação computacional e estruturas de dados")
    R.par(
        "O grafo é implementado pela classe GrafoMatrizPonderado (src/grafo_matriz.py), "
        "construída a partir da classe de matriz de adjacência vista em aula. Suas estruturas "
        "são: n e m (números de vértices e de arestas); adj, uma lista de listas n × n de "
        "números reais em que adj[v][w] guarda o peso da aresta {v, w} ou None quando ela não "
        "existe (a matriz é mantida simétrica); e rotulos, um vetor de textos em que rotulos[v] "
        f"é o rótulo do vértice v, com o prefixo do tipo. A Tabela {R.ntab + 1} relaciona as operações.")
    R.tabela(
        "Operações da classe GrafoMatrizPonderado",
        ["Método", "O que faz"],
        [["insereV(rotulo)", "Acrescenta uma linha e uma coluna com None e devolve o novo índice."],
         ["removeV(v)", "Remove a linha e a coluna de v e todas as arestas incidentes; os "
          "vértices seguintes têm o índice decrementado."],
         ["insereA(v, w, peso)", "Grava o peso em adj[v][w] e adj[w][v]; recusa laço, aresta "
          "repetida, índice inválido, peso fora de [0, 1] e aresta entre vértices do mesmo tipo."],
         ["removeA(v, w)", "Volta adj[v][w] e adj[w][v] para None."],
         ["vizinhos(v), grau(v), tipoVertice(v)", "Consultas: vizinhos com peso, grau e tipo "
          "(pelo prefixo do rótulo)."],
         ["componentes(), ehConexo()", "Componentes conexas por busca em largura; conexo se "
          "houver uma só."],
         ["textoLista(), textoMatriz()", "Exibição como lista de adjacência com rótulos e "
          "pesos, ou como matriz compacta."]],
        larguras=[5.0, 11.0])
    R.par(
        "O arquivo dados/grafo.txt segue o formato do enunciado: na primeira linha o tipo do "
        "grafo (2); na segunda, n; em seguida, n linhas no formato índice \"rótulo\"; depois, m; "
        "e, por fim, m linhas \"v w peso\", com cada aresta gravada uma única vez. O módulo "
        "src/arquivo_grafo.py lê o arquivo (recusando outros tipos com mensagem), grava o grafo "
        "da memória no mesmo formato e formata o conteúdo em tabelas para a opção g do menu. A "
        f"aplicação src/app.py implementa o menu da Tabela {R.ntab + 1}; entradas inválidas – índice fora "
        "do intervalo, peso não numérico, aresta inexistente, fim da entrada – geram mensagens, "
        "nunca exceções.")
    R.tabela(
        "Opções do menu da aplicação",
        ["Opção", "Função", "Implementação"],
        [["a", "Ler dados do arquivo grafo.txt", "arquivo_grafo.ler"],
         ["b", "Gravar dados no arquivo grafo.txt", "arquivo_grafo.gravar"],
         ["c", "Inserir vértice (tipo e nome)", "insereV"],
         ["d", "Inserir aresta (v, w, peso)", "insereA"],
         ["e", "Remover vértice", "removeV"],
         ["f", "Remover aresta", "removeA"],
         ["g", "Mostrar conteúdo do arquivo", "arquivo_grafo.formatarConteudo"],
         ["h", "Mostrar grafo (lista ou matriz)", "textoLista / textoMatriz"],
         ["i", "Apresentar a conexidade (componentes)", "componentes (BFS)"],
         ["j", "Encerrar a aplicação", "—"]],
        larguras=[1.5, 7.5, 6.0])
    R.par(
        f"**Organização do GitHub.** O repositório público ({GITHUB}) está organizado em "
        f"pastas por responsabilidade (Tabela {R.ntab + 1}). Todo arquivo-fonte começa com um cabeçalho que "
        "identifica o projeto, o integrante (nome e RA), a síntese do conteúdo e o histórico de "
        "alterações. As bibliotecas externas (NetworkX, Plotly, python-docx) são usadas apenas "
        "para visualização e geração do relatório; nenhum algoritmo da aplicação depende delas.")
    R.tabela(
        "Organização do repositório",
        ["Caminho", "Conteúdo"],
        [["src/grafo_matriz.py", "Classe GrafoMatrizPonderado (matriz de adjacência, tipo 2)"],
         ["src/arquivo_grafo.py", "Leitura, gravação e formatação do grafo.txt"],
         ["src/app.py", "Aplicação de console com o menu a–j"],
         ["coleta/", "Coletor do MusicBrainz, montagem do grafo e lista de artistas semente"],
         ["dados/", "grafo.txt, vertices.csv, arestas.csv e os JSON brutos da coleta"],
         ["testes/", "Testes automatizados (unittest)"],
         ["visualizacao/", "Figura (Plotly), HTML interativo e grafo.gexf para o Gephi"],
         ["ferramentas/", "Geradores dos prints de teste e deste relatório"],
         ["relatorio/", "Relatório (.docx) e figuras"]],
        larguras=[4.5, 11.5])
    hist = e["historico"]
    if hist:
        R.par("**Histórico de evolução.** O desenvolvimento foi registrado em commits "
              f"incrementais, listados na Tabela {R.ntab + 1} (o commit deste relatório é o último).")
        R.tabela("Histórico de commits do repositório", ["Data", "Commit", "Descrição"],
                 [list(h) for h in hist] + [["28/09/2026", "—", "Relatório da Parte 2"]],
                 larguras=[2.5, 2.0, 11.5])

    R.h2("5.4 Visualização do grafo")
    R.par(
        "O grafo foi desenhado com a biblioteca Plotly a partir do próprio grafo.txt, lido com a "
        "classe da aplicação; a disposição dos vértices usa o algoritmo de molas (spring layout) "
        "do NetworkX com semente fixa. A cor indica o tipo do vértice e a espessura da aresta, a "
        "afinidade (Figura 1). O mesmo grafo, com as mesmas posições e cores, foi exportado em "
        "formato GEXF e aberto no Gephi, uma das ferramentas indicadas pela disciplina "
        "(Figura 2). Uma versão interativa, com o nome e o grau de cada vértice ao passar o "
        "mouse, está em visualizacao/grafo_interativo.html.")
    R.figura(FIG_PLOTLY, f"Grafo tripartido álbum–artista–gênero ({e['n']} vértices, "
             f"{e['m']} arestas): artistas em vermelho, álbuns em azul e gêneros em amarelo",
             fonte="Fonte: autoria própria, dados do MusicBrainz.", altura_max=15, largura_max=16)
    if os.path.exists(FIG_GEPHI):
        R.figura(FIG_GEPHI, "Grafo no Gephi (arquivo visualizacao/grafo.gexf)",
                 fonte="Fonte: autoria própria, dados do MusicBrainz.", altura_max=12)
    else:
        R.marcador_figura("Grafo no Gephi (arquivo visualizacao/grafo.gexf)",
                          "[Inserir aqui o print do grafo no Gephi — visualizacao/grafo.gexf]")
    R.par(
        "A figura já evidencia a estrutura em duas regiões: na parte superior, o R&B e o "
        "hip-hop, organizados em torno de gêneros como hip hop, alternative r&b e contemporary "
        "r&b; na inferior, a MPB, concentrada em mpb, latin, bossa nova e samba. Entre as duas, "
        "poucos gêneros – soul, funk, pop e r&b – fazem a ligação.")

    R.h2("5.5 Análise do grafo")
    R.par(f"A Tabela {R.ntab + 1} reúne as medidas gerais do grafo, todas calculadas pelo script gerador "
          "deste relatório a partir de dados/grafo.txt.")
    R.tabela(
        "Medidas gerais do grafo",
        ["Medida", "Valor"],
        [["Tipo do grafo", "2 – não orientado com peso na aresta"],
         ["Número de vértices (n)", f"{e['n']} ({pt['ART']} artistas, {pt['ALB']} álbuns, "
                                     f"{pt['GEN']} gêneros)"],
         ["Número de arestas (m)", f"{e['m']} ({pr['ALB-ART']} álbum–artista, {pr['ALB-GEN']} "
                                   f"álbum–gênero, {pr['ART-GEN']} artista–gênero)"],
         ["Grau médio (2m/n)", fmt(e["grau_medio"])],
         ["Densidade 2m/(n(n − 1))", fmt(e["densidade"], 4)],
         ["Máximo de arestas possível no grafo tripartido", f"{e['m_max_tri']} "
          f"(ocupação de {fmt(100 * e['densidade_tri'], 1)}%)"],
         ["Componentes conexas", f"{len(comp)} – grafo {'CONEXO' if conexo else 'DESCONEXO'}"],
         ["Diâmetro (em número de arestas)", f"{e['diametro']} (entre {e['par_diametro'][0]} "
                                             f"e {e['par_diametro'][1]})"],
         ["Distância média entre pares (arestas)", fmt(e["dist_media"])],
         ["Arestas de gênero com custo 0,00", f"{cz} de {ct}"]],
        larguras=[6.5, 9.5])
    R.tabela(
        "Grau dos vértices por tipo",
        ["Tipo", "Quantidade", "Grau médio", "Grau mínimo", "Grau máximo", "Vértice de grau máximo"],
        [[NOMES_TIPO[t], pt[t], fmt(e["graus"][t]["media"]), e["graus"][t]["min"],
          e["graus"][t]["max"], e["graus"][t]["vmax"]] for t in ("ART", "ALB", "GEN")],
        larguras=[1.6, 2.3, 1.9, 1.9, 1.9, 6.4])
    R.tabela(
        "Os cinco gêneros de maior grau",
        ["Gênero", "Grau", "Ligações com R&B/hip-hop", "Ligações com MPB"],
        [[x["nome"], x["grau"], x["rnb"], x["mpb"]] for x in e["top_generos"]],
        larguras=[5.0, 2.0, 4.5, 4.5])
    R.par(
        f"O grafo é **{'conexo' if conexo else 'desconexo'}**"
        + (": existe um caminho entre quaisquer dois vértices, ou seja, partindo de qualquer "
           "álbum é possível chegar a qualquer outro, o que é pré-requisito para a trilha de "
           "descoberta da próxima etapa. " if conexo else ". ")
        + f"Com densidade {fmt(e['densidade'], 4)}, é esparso: das "
        f"{e['n'] * (e['n'] - 1) // 2} ligações possíveis entre pares de vértices, só "
        f"{e['m']} existem – mesmo considerando apenas os pares permitidos pela tripartição, "
        f"a ocupação é de {fmt(100 * e['densidade_tri'], 1)}%. O diâmetro de {e['diametro']} "
        f"arestas e a distância média de {fmt(e['dist_media'])} arestas indicam que as duas "
        "cenas, embora separadas, ficam a poucos passos uma da outra.")
    R.par(
        f"Os gêneros de maior grau são \"hubs\" de uma única cena (Tabela {R.ntab}): mpb e latin "
        "concentram a MPB, enquanto hip hop e os gêneros de r&b concentram a outra cena. Isso "
        "confirma que a classificação da comunidade separa bem as duas cenas. A pergunta mais "
        "interessante para a descoberta é, então, **quais vértices ligam as duas cenas**. Um "
        "gênero foi considerado ponte quando tem vizinhos (artistas ou álbuns) das duas cenas; "
        f"dos {pt['GEN']} gêneros, {len(e['generos_ponte'])} são pontes, "
        f"{e['generos_exclusivos']['rnb']} são exclusivos do R&B/hip-hop e "
        f"{e['generos_exclusivos']['mpb']} exclusivos da MPB (Tabela {R.ntab + 1}).")
    R.tabela(
        "Gêneros-ponte entre as duas cenas (ordenados pelo menor lado)",
        ["Gênero", "Grau", "Vizinhos R&B/hip-hop", "Vizinhos MPB"],
        [[x["nome"], x["grau"], x["rnb"], x["mpb"]] for x in e["generos_ponte"]],
        larguras=[5.0, 2.0, 4.5, 4.5])
    R.par(
        "Para identificar os artistas que sustentam essas pontes, somou-se a afinidade (1 − peso) "
        f"das arestas que ligam o artista e seus álbuns a gêneros-ponte. A Tabela {R.ntab + 1} mostra os "
        "três primeiros de cada cena.")
    R.tabela(
        "Artistas-ponte: ligação do artista e de seus álbuns com gêneros-ponte",
        ["Artista", "Cena", "Arestas", "Soma das afinidades", "Gêneros-ponte alcançados"],
        [[x["artista"], NOMES_CENA[x["cena"]], x["arestas"], fmt(x["afinidade"]),
          ", ".join(x["generos"])] for x in e["artistas_ponte"]],
        larguras=[3.5, 2.6, 1.6, 2.5, 5.8])
    top_r = next(x for x in e["artistas_ponte"] if x["cena"] == "rnb")
    top_m = next(x for x in e["artistas_ponte"] if x["cena"] == "mpb")
    if top_m["artista"] == "Tim Maia":
        frase_m = (" sua obra do início dos anos 1970, marcada pelo soul e pelo funk "
                   "norte-americanos, liga a MPB aos gêneros da outra cena")
    else:
        frase_m = f" alcança os gêneros-ponte {lista_pt(top_m['generos'])}"
    R.par(
        f"Do lado brasileiro, {top_m['artista']} é a principal ponte:{frase_m}. Do lado "
        f"norte-americano, {top_r['artista']} cumpre o papel simétrico, alcançando os "
        f"gêneros-ponte {lista_pt(top_r['generos'])}. O resultado é coerente com a história da música e "
        "mostra que o modelo captura relações reais a partir apenas dos votos de gênero.")
    cam = e["caminho"]
    R.par(
        f"Como prévia da próxima etapa, a busca em largura encontrou um caminho com o menor "
        f"número de arestas ({len(cam) - 1}) entre {cam[0][0]} e {cam[-1][0]}: "
        + " → ".join(f"{r}" + ("" if p is None else f" (custo {fmt(p)})") for r, p in cam)
        + f", de custo total {fmt(sum(p for _, p in cam if p is not None))}. A busca em largura "
        "ignora os pesos; o algoritmo de Dijkstra, na próxima etapa, poderá preferir um caminho "
        "mais longo, porém de menor custo total, isto é, formado por ligações mais fortes.")
    R.par("**Análise crítica e limitações.**", recuo=False, depois=3)
    vc = e["votos_cena"]
    sg = e["sem_genero_cena"]
    zc = e["zero_cena"]
    for texto in (
            f"**Viés de votos:** os gêneros refletem quem vota no MusicBrainz, comunidade de "
            f"perfil majoritariamente anglófono. Os álbuns selecionados do R&B/hip-hop somam em "
            f"média {fmt(vc['rnb'], 1)} votos de gênero, contra {fmt(vc['mpb'], 1)} nos álbuns "
            "de MPB.",
            f"**Poucos votos em álbuns brasileiros antigos:** {sg['mpb'][0]} dos {sg['mpb'][1]} "
            f"álbuns de estúdio da MPB coletados não têm nenhum gênero votado (contra "
            f"{sg['rnb'][0]} de {sg['rnb'][1]} no R&B/hip-hop). Com poucos votos, vários gêneros "
            f"empatam no máximo e recebem custo 0,00: isso ocorre em {zc['mpb'][0]} de "
            f"{zc['mpb'][1]} arestas álbum–gênero da MPB e em {zc['rnb'][0]} de {zc['rnb'][1]} "
            "do R&B/hip-hop, o que reduz o poder de discriminação dos pesos na MPB.",
            "**Corte em cinco gêneros com desempate alfabético:** quando há empate, gêneros "
            "igualmente votados podem ficar de fora apenas pela ordem alfabética (por exemplo, "
            "soul no álbum Tim Maia de 1972).",
            "**Recorte curado:** os 16 artistas foram escolhidos pelo autor, o que determina as "
            "cenas e as pontes encontradas; o grafo não representa o universo musical, e sim "
            "duas cenas escolhidas para tornar a descoberta entre elas o problema central.",
            "**Nomes de gêneros em inglês:** a lista oficial do MusicBrainz usa nomes em inglês "
            "(latin, singer-songwriter), inclusive para gêneros brasileiros, e alguns gêneros "
            "se sobrepõem (mpb e latin, r&b e contemporary r&b).",
            "**Retrato de uma data:** os dados são um retrato da base na data da coleta; votos "
            "novos podem alterar os pesos, por isso os JSON brutos foram versionados para que o "
            "resultado seja reproduzível."):
        R.item(texto)

    R.h2("5.6 Testes")
    pa = e["testes_por_arquivo"]
    R.par(
        f"A suíte de testes automatizados (unittest) tem {e['testes_total']} testes e foi "
        f"executada pelo script gerador deste relatório, com resultado "
        f"**{'todos aprovados' if e['testes_ok'] else 'FALHA'}**. A Tabela {R.ntab + 1} descreve o que "
        "cada arquivo verifica.")
    desc = {
        "test_grafo_matriz": "Inserção e simetria, peso 0,0 como aresta válida, recusa de "
                             "laço/repetida/mesmo tipo/peso inválido, remoção de aresta, remoção "
                             "de vértice com reindexação, componentes e tipo do vértice.",
        "test_arquivo_grafo": "Ida e volta ler → gravar → ler idêntica (também após remoções), "
                              "formato do texto, recusa de tipo diferente de 2 e formatação.",
        "test_montar_grafo": "Cálculo das afinidades, construção do grafo, desambiguação de "
                             "álbuns homônimos e mínimos do grafo real (n ≥ 80, m ≥ 200, tipo 2, "
                             "tripartição).",
        "test_app": "Menu completo simulando a entrada do usuário: título, operação sem grafo, "
                    "fluxo a–j, aresta de mesmo tipo recusada, índice fora do intervalo e fim "
                    "da entrada.",
    }
    R.tabela("Testes automatizados", ["Arquivo", "Testes", "O que verifica"],
             [[f"testes/{k}.py", pa[k], desc.get(k, "")] for k in sorted(pa)]
             + [["Total", e["testes_total"], ""]],
             larguras=[4.2, 1.5, 10.3])
    prints = sorted(glob.glob(os.path.join(PASTA_PRINTS, "*.png")))
    legendas = {}
    caminho_leg = os.path.join(PASTA_PRINTS, "legendas.json")
    if os.path.exists(caminho_leg):
        with open(caminho_leg, encoding="utf-8") as f:
            legendas = json.load(f)
    opcoes = sorted({os.path.basename(p).split("_")[2] for p in prints if p.count("_") >= 3})
    R.par(
        "Além dos testes automatizados, a aplicação foi exercitada com roteiros de uso do menu, "
        f"com ao menos dois testes para cada opção ({len(prints)} testes ao todo, cobrindo as "
        f"opções {', '.join(opcoes) if opcoes else '—'}), incluindo casos válidos e entradas "
        "inválidas. As capturas foram produzidas pelo script ferramentas/gerar_prints.py, que "
        "executa a aplicação real com as entradas do roteiro, ecoa cada entrada como em um "
        "terminal e registra a saída completa em imagem; todas as operações são feitas sobre "
        "cópias temporárias do grafo.txt. Saídas muito longas aparecem truncadas. As Figuras "
        f"{R.nfig + 1} a {R.nfig + len(prints)} mostram os testes.")
    # agrupa por opção do menu (NN_opcao_X_testeK.png); pares de capturas
    # altas ficam lado a lado, as demais ocupam a largura da página
    grupos = []
    for caminho in prints:
        partes = os.path.basename(caminho).split("_")
        chave = partes[2] if len(partes) >= 4 else caminho
        if grupos and grupos[-1][0] == chave:
            grupos[-1][1].append(caminho)
        else:
            grupos.append((chave, [caminho]))

    def titulo_de(caminho):
        nome = os.path.basename(caminho)
        return legendas.get(nome, nome).rstrip(".")

    def alta(caminho):
        w, h = Image.open(caminho).size
        return h / w >= 1.0

    for _, lista in grupos:
        if len(lista) == 2 and all(alta(c) for c in lista):
            R.figuras_lado_a_lado([(c, titulo_de(c)) for c in lista])
        else:
            for caminho in lista:
                R.figura(caminho, titulo_de(caminho), altura_max=9.8, largura_max=15.5)

    # ---------------------------------------------------------- 6 ODS
    R.h1("6 Objetivos de Desenvolvimento Sustentável")
    R.par("O projeto se relaciona com três Objetivos de Desenvolvimento Sustentável da Agenda "
          "2030 (IBGE, [2026]):")
    for texto in (
            "**ODS 9 – Indústria, inovação e infraestrutura:** desenvolve uma ferramenta "
            "computacional aberta, baseada em dados públicos e software livre, que modela e "
            "analisa uma rede de conhecimento musical; o código e os dados ficam disponíveis "
            "para reúso, contribuindo para a capacidade tecnológica e a inovação.",
            "**ODS 4 – Educação de qualidade:** a trilha de descoberta entre álbuns funciona como "
            "instrumento de acesso e formação cultural, apresentando ao ouvinte obras e gêneros "
            "que ele não conhece a partir do que já conhece; o próprio projeto é também material "
            "didático de Teoria dos Grafos, com dados reais.",
            "**ODS 11 (meta 11.4) – Proteger e salvaguardar o patrimônio cultural:** a MPB é "
            "parte do patrimônio cultural brasileiro. O modelo liga discos históricos, como os "
            "de Tim Maia, Gal Costa e Os Mutantes, a artistas contemporâneos, o que favorece "
            "que esse repertório seja redescoberto por novos públicos; a análise também "
            "evidencia a sub-representação dos álbuns brasileiros antigos nas bases abertas, "
            "um problema de preservação digital."):
        R.item(texto)

    # ---------------------------------------------------------- 7 próximas etapas
    R.h1("7 Próximas etapas")
    R.par(
        "No segundo bimestre, a função central do protótipo será a **trilha de descoberta**: "
        "dados um álbum de partida e um álbum de chegada, o algoritmo de Dijkstra, implementado "
        "sobre a mesma matriz de adjacência, encontrará o caminho de menor custo total, "
        "mostrando os artistas e gêneros intermediários e o custo de cada passo. Como os pesos "
        "estão em [0, 1], o requisito de pesos não negativos é satisfeito. Estão previstos "
        "ainda: nova opção no menu para a trilha, comparação entre o caminho de menor custo e o "
        "de menor número de arestas, e a ampliação do conjunto de artistas semente para testar "
        "a robustez dos gêneros-ponte encontrados. Usuários, detecção de comunidades e "
        "recomendação personalizada permanecem fora do escopo da disciplina.")

    # ---------------------------------------------------------- 8 referências
    R.h1("Referências")
    refs = [
        "BLONDEL, V. D.; GUILLAUME, J.-L.; LAMBIOTTE, R.; LEFEBVRE, E. Fast unfolding of "
        "communities in large networks. **Journal of Statistical Mechanics: Theory and "
        "Experiment**, v. 2008, n. 10, p. P10008, 2008. DOI: 10.1088/1742-5468/2008/10/P10008.",
        "BONDY, J. A.; MURTY, U. S. R. **Graph theory**. New York: Springer, 2010.",
        "BRASIL. Lei nº 13.709, de 14 de agosto de 2018. Lei Geral de Proteção de Dados "
        "Pessoais (LGPD). **Diário Oficial da União**, Brasília, DF, 2018. Disponível em: "
        "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm. Acesso em: "
        "28 set. 2026.",
        "CORMEN, T. H.; LEISERSON, C. E.; RIVEST, R. L.; STEIN, C. **Introduction to "
        "algorithms**. 2. ed. Cambridge, MA: MIT Press, 2001.",
        "DATTA, H.; KNOX, G.; BRONNENBERG, B. J. Changing their tune: how consumers' adoption "
        "of online streaming affects music consumption and discovery. **Marketing Science**, "
        "v. 37, n. 1, p. 5-21, 2018. DOI: 10.1287/mksc.2017.1051.",
        "DIESTEL, R. **Graph theory**. 4. ed. New York: Springer, 2010.",
        "EKSOMBATCHAI, C. et al. Pixie: a system for recommending 3+ billion items to 200+ "
        "million users in real-time. In: WORLD WIDE WEB CONFERENCE, 2018, Lyon. "
        "**Proceedings** [...]. New York: ACM, 2018. p. 1775-1784. DOI: "
        "10.1145/3178876.3186183.",
        "IBGE – INSTITUTO BRASILEIRO DE GEOGRAFIA E ESTATÍSTICA. **Indicadores Brasileiros "
        "para os Objetivos de Desenvolvimento Sustentável**. Rio de Janeiro: IBGE, [2026]. "
        "Disponível em: "
        "https://odsbrasil.gov.br/. Acesso em: 28 set. 2026.",
        "LIKA, B.; KOLOMVATSOS, K.; HADJIEFTHYMIADES, S. Facing the cold start problem in "
        "recommender systems. **Expert Systems with Applications**, v. 41, n. 4, pt. 2, "
        "p. 2065-2073, 2014. DOI: 10.1016/j.eswa.2013.09.005.",
        "MUSICBRAINZ. **MusicBrainz API**. [S. l.]: MetaBrainz Foundation, [2026]. Disponível em: "
        "https://musicbrainz.org/doc/MusicBrainz_API. Acesso em: 28 set. 2026.",
        "SHARMA, A.; JIANG, J.; BOMMANNAVAR, P.; LARSON, B.; LIN, J. GraphJet: real-time "
        "content recommendations at Twitter. **Proceedings of the VLDB Endowment**, v. 9, "
        "n. 13, p. 1281-1292, 2016. DOI: 10.14778/3007263.3007267.",
        "SHI, C.; LI, Y.; ZHANG, J.; SUN, Y.; YU, P. S. A survey of heterogeneous information "
        "network analysis. **IEEE Transactions on Knowledge and Data Engineering**, v. 29, "
        "n. 1, p. 17-37, 2017. DOI: 10.1109/TKDE.2016.2598561.",
        "SZWARCFITER, J. L. **Grafos e algoritmos computacionais**. 2. ed. Rio de Janeiro: "
        "Campus, 1988.",
        "UGANDER, J.; KARRER, B.; BACKSTROM, L.; MARLOW, C. **The anatomy of the Facebook "
        "social graph**. arXiv:1111.4503, 2011. Disponível em: https://arxiv.org/abs/1111.4503. "
        "Acesso em: 28 set. 2026.",
        "VAN DEN OORD, A.; DIELEMAN, S.; SCHRAUWEN, B. Deep content-based music "
        "recommendation. In: ADVANCES IN NEURAL INFORMATION PROCESSING SYSTEMS, 26., 2013. "
        "**Proceedings** [...]. 2013. p. 2643-2651.",
        "YING, R.; HE, R.; CHEN, K.; EKSOMBATCHAI, P.; HAMILTON, W. L.; LESKOVEC, J. Graph "
        "convolutional neural networks for web-scale recommender systems. In: ACM SIGKDD "
        "INTERNATIONAL CONFERENCE ON KNOWLEDGE DISCOVERY AND DATA MINING, 24., 2018, London. "
        "**Proceedings** [...]. New York: ACM, 2018. DOI: 10.1145/3219819.3219890.",
    ]
    for ref in refs:
        p = R.par(ref, recuo=False, alinhamento=WD_ALIGN_PARAGRAPH.LEFT, depois=8)
        p.paragraph_format.line_spacing = 1.0

    # ---------------------------------------------------------- apêndice
    R.h1("Apêndice A – Repositório no GitHub")
    R.par(f"Código-fonte, dados, testes, figuras e este relatório estão disponíveis, com acesso "
          f"público, em: **{GITHUB}**", recuo=False)
    R.par("Para reproduzir os resultados: instalar as dependências (pip install -r "
          "requirements.txt); executar a aplicação (python3 src/app.py); rodar os testes "
          "(python3 -m unittest discover -s testes); refazer a coleta e o grafo, se desejado "
          "(python3 coleta/coletar_musicbrainz.py e python3 coleta/montar_grafo.py); regenerar "
          "a visualização (python3 visualizacao/visualizar.py) e este relatório (python3 "
          "ferramentas/gerar_relatorio.py).", recuo=False)
    return R


def main():
    e = calcular_estatisticas()
    e["testes_por_arquivo"], e["testes_total"], e["testes_ok"] = rodar_testes()
    e["historico"] = historico_git()
    doc = preparar_template()
    R = escrever(doc, e)
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    doc.save(SAIDA)
    print(f"Relatório gravado em {SAIDA}")
    print(f"n={e['n']} m={e['m']} tipos={dict(e['por_tipo'])} relações={dict(e['por_relacao'])}")
    print(f"componentes={len(e['componentes'])} densidade={e['densidade']:.4f} "
          f"diâmetro={e['diametro']} dist_média={e['dist_media']:.2f}")
    print("gêneros-ponte:", [(x['nome'], x['rnb'], x['mpb']) for x in e['generos_ponte']])
    print("artistas-ponte:", [(x['artista'], round(x['afinidade'], 2)) for x in e['artistas_ponte']])
    print(f"testes={e['testes_total']} ok={e['testes_ok']} figuras={R.nfig} tabelas={R.ntab}")
    print("gephi.png:", "presente" if os.path.exists(FIG_GEPHI) else "AUSENTE (marcador inserido)")


if __name__ == "__main__":
    main()
