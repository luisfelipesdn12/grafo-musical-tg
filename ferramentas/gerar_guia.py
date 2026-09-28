# -*- coding: utf-8 -*-
"""
Projeto de Teoria dos Grafos - Parte 2
Descoberta Musical por Grafos: Álbuns, Artistas e Gêneros

Integrante: Luis Felipe Santos do Nascimento - RA 10420572

Síntese: gera relatorio/Guia_Apresentacao.docx - guia de apoio para a
apresentação ao vivo de 5 minutos (01/10) do projeto. Reúne roteiro
cronometrado (blocos que somam <= 5:00) com frases-chave por bloco, a
sequência exata de comandos da demonstração ao vivo no menu a-j de
src/app.py (com as saídas esperadas, conferidas rodando a aplicação uma
vez sobre dados/grafo.txt real), checklist pré-apresentação e perguntas
prováveis da banca com respostas curtas. Os índices de vértice usados na
demo ("[ART] Frank Ocean", "[GEN] soul" etc.) foram obtidos em tempo de
execução a partir do grafo real, nunca fixados a olho.

Uso:  .venv/bin/python ferramentas/gerar_guia.py

Histórico de alterações:
  28/09/2026 - Luis Felipe - criação
"""
import os
import sys

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "src"))

from arquivo_grafo import ler  # noqa: E402

CAMINHO_GRAFO = os.path.join(RAIZ, "dados", "grafo.txt")
CAMINHO_SAIDA = os.path.join(RAIZ, "relatorio", "Guia_Apresentacao.docx")

AZUL_ESCURO = RGBColor(0x1F, 0x3B, 0x57)
CINZA_CLARO = "D9E2EC"


# --------------------------------------------------------------------- dados
def indices_reais():
    """Índices/estatísticas conferidos no grafo real (dados/grafo.txt), para
    que a tabela da demo e o texto de resultados nunca fiquem "a olho"."""
    g = ler(CAMINHO_GRAFO)
    idx = {r: i for i, r in enumerate(g.rotulos)}
    return {
        "n": g.n,
        "m": g.m,
        "idx_frank_ocean": idx["[ART] Frank Ocean"],
        "idx_gen_soul": idx["[GEN] soul"],
        "componentes": len(g.componentes()),
    }


# ------------------------------------------------------------- construção docx
def definir_estilos(doc):
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10.5)
    for secao in doc.sections:
        secao.top_margin = Cm(1.8)
        secao.bottom_margin = Cm(1.6)
        secao.left_margin = Cm(2.0)
        secao.right_margin = Cm(2.0)


def sombrear_celula(celula, cor_hex):
    tc_pr = celula._tc.get_or_add_tcPr()
    shd = tc_pr.makeelement(qn("w:shd"), {qn("w:val"): "clear", qn("w:color"): "auto", qn("w:fill"): cor_hex})
    tc_pr.append(shd)


def titulo(doc, texto, nivel=1):
    p = doc.add_heading(texto, level=nivel)
    for run in p.runs:
        run.font.color.rgb = AZUL_ESCURO
    return p


def paragrafo(doc, texto, negrito=False, tamanho=10.5, espaco_depois=4):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(espaco_depois)
    run = p.add_run(texto)
    run.bold = negrito
    run.font.size = Pt(tamanho)
    return p


def tabela(doc, cabecalho, linhas, larguras=None, tamanho_fonte=9.5):
    t = doc.add_table(rows=1, cols=len(cabecalho))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = True
    for j, texto in enumerate(cabecalho):
        celula = t.rows[0].cells[j]
        celula.text = ""
        run = celula.paragraphs[0].add_run(texto)
        run.bold = True
        run.font.size = Pt(tamanho_fonte)
        sombrear_celula(celula, CINZA_CLARO)
    for linha in linhas:
        cels = t.add_row().cells
        for j, valor in enumerate(linha):
            cels[j].text = ""
            run = cels[j].paragraphs[0].add_run(str(valor))
            run.font.size = Pt(tamanho_fonte)
    if larguras:
        for j, largura in enumerate(larguras):
            for linha_t in t.rows:
                linha_t.cells[j].width = largura
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def lista_bullets(doc, itens, tamanho=10.5):
    for item in itens:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.space_after = Pt(2)
        run = p.add_run(item)
        run.font.size = Pt(tamanho)


# ---------------------------------------------------------------------- main
def gerar():
    dados = indices_reais()
    v_novo = dados["n"]  # índice que o novo vértice recebe ao ser inserido (c)
    idx_frank = dados["idx_frank_ocean"]
    idx_soul = dados["idx_gen_soul"]
    n, m = dados["n"], dados["m"]
    assert dados["componentes"] == 1, "grafo real deveria ser conexo"

    doc = Document()
    definir_estilos(doc)

    # ------------------------------------------------------------- cabeçalho
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("Projeto de Teoria dos Grafos - Parte 2")
    run.bold = True
    run.font.size = Pt(15)
    run.font.color.rgb = AZUL_ESCURO

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("Descoberta Musical por Grafos: Álbuns, Artistas e Gêneros")
    run.bold = True
    run.font.size = Pt(12.5)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("Guia de Apresentação Oral (5 minutos - 01/10/2026)")
    run.italic = True
    run.font.size = Pt(11.5)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(10)
    run = p.add_run("Integrante: Luis Felipe Santos do Nascimento - RA 10420572")
    run.font.size = Pt(10.5)

    titulo(doc, "Síntese", nivel=2)
    paragrafo(
        doc,
        "Este guia organiza os 5 minutos de apresentação oral do projeto (grafo tripartido "
        f"não orientado e ponderado - tipo 2 - com {n} vértices e {m} arestas, representando "
        "álbuns, artistas e gêneros musicais, cujo peso é o custo de descoberta = 1 - afinidade). "
        "Reúne roteiro cronometrado com frases-chave por bloco, a sequência exata de comandos da "
        "demonstração ao vivo (conferida rodando a aplicação sobre o grafo real), checklist "
        "pré-apresentação e respostas curtas às perguntas mais prováveis da banca.",
    )

    titulo(doc, "Histórico de alterações", nivel=2)
    paragrafo(doc, "28/09/2026 - Luis Felipe - criação", tamanho=10)

    doc.add_page_break()

    # -------------------------------------------------------- roteiro cronometrado
    titulo(doc, "1. Roteiro cronometrado (total: 5:00)", nivel=1)
    paragrafo(
        doc,
        "Seis blocos que somam exatamente 5 minutos. Praticar com cronômetro visível; se algum "
        "bloco atrasar, cortar primeiro a leitura da tabela de arestas em g) e ir direto à lista "
        "de adjacência em h).",
        tamanho=9.5,
    )
    tabela(
        doc,
        ["Tempo", "Bloco", "O que dizer (frases-chave)", "O que mostrar"],
        [
            (
                "0:00–0:45",
                "Problema e ajuste\npós-parecer",
                "• “O projeto modela álbuns, artistas e gêneros como um grafo tripartido, "
                "para calcular o custo de descoberta entre eles.”\n"
                "• “Na Parte 1 o parecer (nota 8,0) apontou escopo amplo demais e uso de "
                "dados de usuários; reformulamos para trabalhar só com conteúdo público: álbum, "
                "artista e gênero.”",
                "Tela com o título da aplicação (app.py) ou slide de abertura",
            ),
            (
                "0:45–1:45",
                "Modelagem",
                "• “É um grafo tipo 2: não orientado, com peso na aresta, e tripartido - "
                "nunca liga dois vértices do mesmo tipo.”\n"
                "• “O peso é o custo de descoberta = 1 − afinidade; afinidade é o quanto uma "
                "tag foi votada em relação à tag mais votada daquela entidade. Autoria "
                "álbum–artista tem afinidade 1, custo 0.”",
                "Tabela de tipos de aresta (ALB-ART, ALB-GEN, ART-GEN) do relatório/spec",
            ),
            (
                "1:45–2:15",
                "Coleta",
                "• “Os dados vêm da API pública do MusicBrainz: 16 artistas-semente (8 de "
                "R&B/hip-hop, 8 de MPB), até 4 álbuns ‘Album’ por artista, gêneros com pelo menos "
                "2 votos.”\n"
                "• “Não coletamos nenhum dado de usuário - só metadados abertos, respondendo "
                "direto à crítica ética do parecer.”",
                f"Um JSON de dados/brutos/ ou as estatísticas n={n}, m={m}",
            ),
            (
                "2:15–3:45",
                "Demo ao vivo",
                "• “Vou ler o grafo real, mostrar o conteúdo, inserir um vértice e uma "
                "aresta, checar a conexidade, remover, checar de novo e gravar numa cópia.”",
                "Terminal (comandos exatos na seção 2) + aba já aberta com o HTML Plotly",
            ),
            (
                "3:45–4:30",
                "Resultados e\nlimitações",
                f"• “O grafo tem {n} vértices e {m} arestas, é conexo num único componente e "
                "não tem vértice de articulação - é uma malha robusta.”\n"
                "• “Gêneros como soul e r&b ligam diretamente artistas das duas cenas - Tim "
                "Maia e Anderson .Paak; funk e pop ligam via álbuns.”\n"
                "• “Limitação: amostra pequena e curada, tags dependem da comunidade do "
                "MusicBrainz, é um retrato estático de 28/09/2026.”",
                "HTML Plotly com hover nos vértices-ponte (soul / Tim Maia / Anderson .Paak)",
            ),
            (
                "4:30–5:00",
                "Próximas etapas",
                "• “No 2º bimestre implementamos Dijkstra sobre esses pesos, para achar a "
                "‘trilha de descoberta’ de menor custo entre dois álbuns.”\n"
                "• “Este protótipo é a camada de conteúdo de um TCC maior, que no futuro "
                "incorpora usuários reais sob procedimentos éticos.”",
                "Encerrar; agradecer",
            ),
        ],
        larguras=[Cm(1.7), Cm(2.1), Cm(8.3), Cm(4.4)],
    )

    # ------------------------------------------------------- sequência de comandos
    titulo(doc, "2. Sequência exata de comandos da demo ao vivo", nivel=1)
    paragrafo(
        doc,
        "IMPORTANTE - demo segura: a gravação (opção b) NUNCA é feita em dados/grafo.txt durante "
        "a apresentação; usar sempre o caminho /tmp/demo.txt. Todos os passos abaixo foram "
        "executados uma vez com `.venv/bin/python src/app.py` sobre o dados/grafo.txt real "
        "(sem alterá-lo) para conferir as saídas.",
        negrito=False,
        tamanho=9.5,
    )
    tabela(
        doc,
        ["#", "Opção", "Entrada digitada", "Saída esperada (resumo)"],
        [
            ("1", "a", "Enter (caminho padrão)", f"“Grafo lido: {n} vértices, {m} arestas.”"),
            ("2", "g", "Enter (caminho padrão)", "Tabela: “Vértices: 109  Arestas: 349” + lista Nº/Tipo/Rótulo + lista v/w/peso/ligação"),
            ("3", "h", "1", f"Lista de adjacência (ex.: {idx_frank:3d} [ART] Frank Ocean -> vizinhos com peso)"),
            ("4", "c", "2  ·  Erykah Badu", f"“Vértice {v_novo} inserido: [ART] Erykah Badu”"),
            ("5", "d", f"{v_novo}  ·  {idx_soul}  ·  0.20", "“Aresta inserida: [ART] Erykah Badu <-> [GEN] soul (peso 0.20)”"),
            ("6", "i", "(sem entrada)", "“O grafo é CONEXO (1 componente(s) conexa(s)).”"),
            ("7", "e", f"{v_novo}", "“Removido [ART] Erykah Badu e 1 aresta(s) incidente(s). Os vértices após "
             f"{v_novo} tiveram o índice reduzido em 1.”"),
            ("8", "i", "(sem entrada)", "“O grafo é CONEXO (1 componente(s) conexa(s)).” - mesma conclusão de antes"),
            ("9", "b", "/tmp/demo.txt", f"“Grafo gravado em /tmp/demo.txt ({n} vértices, {m} arestas).”"),
            ("10", "j", "(sem entrada)", "“Encerrando a aplicação. Até logo!”"),
            ("11", "—", "(fora da app) abrir visualizacao/grafo_interativo.html numa aba", "Grafo interativo Plotly; passar o mouse pelos vértices-ponte"),
        ],
        larguras=[Cm(0.8), Cm(1.3), Cm(4.3), Cm(10.1)],
    )
    paragrafo(
        doc,
        f"Por que esses índices: {v_novo} é o índice que o novo vértice “[ART] Erykah Badu” recebe "
        f"ao ser inserido (o grafo real carregado tem {n} vértices, índices 0..{n - 1}; insereV "
        f"sempre acrescenta no final). O índice {idx_soul} é o de “[GEN] soul” no grafo real "
        "(conferido em tempo de execução, não fixado a olho) - um dos gêneros-ponte entre as duas "
        "cenas (ver seção 3). Como não há vértice de articulação no grafo, os dois “i)” do roteiro "
        "dão o mesmo resultado (CONEXO): o ponto não é criar uma quebra, é mostrar que "
        "inserir/remover não corrompe a estrutura nem a conexidade.",
        tamanho=9,
    )

    # ---------------------------------------------------------------- checklist
    titulo(doc, "3. Checklist pré-apresentação", nivel=1)
    lista_bullets(
        doc,
        [
            "venv ativo e testado: `.venv/bin/python src/app.py` roda sem erro a partir da raiz do repositório.",
            "dados/grafo.txt é o original do repositório (rodar `git status` e, se houver qualquer "
            "alteração, `git checkout dados/grafo.txt` antes de começar).",
            "A gravação de teste (opção b) aponta para /tmp/demo.txt - nunca para dados/grafo.txt.",
            "visualizacao/grafo_interativo.html já aberto numa aba do navegador, testado (zoom e "
            "hover funcionando), antes de começar a falar.",
            "Fonte do terminal aumentada (facilita a leitura da banca) e janela em tela cheia.",
            "Cronômetro visível (celular ou relógio) marcando os 6 blocos do roteiro.",
            "Este guia impresso ou aberto em uma segunda tela, não a que está sendo compartilhada.",
            "Sequência de comandos da seção 2 praticada ao menos uma vez de ponta a ponta.",
            "Conexão de internet não é necessária durante a apresentação (app roda 100% local).",
        ],
        tamanho=10,
    )

    # ------------------------------------------------------------- perguntas
    titulo(doc, "4. Perguntas prováveis da banca", nivel=1)
    tabela(
        doc,
        ["Pergunta", "Resposta curta"],
        [
            ("Por que grafo não orientado?",
             "As relações modeladas (autoria álbum-artista, classificação álbum-gênero, "
             "trânsito artista-gênero) são simétricas - não há sentido de direção entre as "
             "entidades, e a “descoberta” pode partir de qualquer lado."),
            ("Por que matriz de adjacência (e não lista)?",
             f"n é pequeno ({n} vértices), então o custo O(n²) de espaço é aceitável; a classe "
             "é baseada na GrafoND de aula (matriz), com acesso a aresta em O(1), o que "
             "simplifica a checagem de tripartição a cada inserção."),
            ("Por que peso = 1 − afinidade?",
             "Para medir a “distância”/custo de percorrer uma aresta: quanto maior a afinidade "
             "(mais votos relativos na tag, ou autoria direta), menor o custo. Isso já prepara o "
             "terreno para o Dijkstra do 2º bimestre (menor custo = trilha de descoberta mais direta)."),
            ("Por que sem usuários?",
             "Atendendo ao parecer da Parte 1: comunidades de usuários reais exigiriam dados "
             "pessoais e procedimentos éticos. Reduzimos o escopo a conteúdo público - álbum, "
             "artista e gênero."),
            ("Por que MusicBrainz?",
             "Base de metadados musicais pública e colaborativa, com API REST documentada, sem "
             "dados de usuários, e tags de gênero com contagem de votos - o que permite calcular "
             "a afinidade real usada no peso."),
            ("Por que FCONEX não se aplica?",
             "FCONEX (fecho transitivo, componentes fortemente conexas C0-C3) é definido para "
             "grafos ORIENTADOS. Nosso grafo é tipo 2 (não orientado); o equivalente aqui é a "
             "conexidade simples via BFS/componentes conexas, calculada na opção i)."),
            ("Como garante a tripartição?",
             "insereA() compara tipoVertice(v) e tipoVertice(w) (lido do prefixo do rótulo - "
             "[ALB]/[ART]/[GEN]) e recusa a aresta se forem iguais; a checagem vale tanto para "
             "arestas carregadas do arquivo quanto para as inseridas pelo menu."),
            (f"Como garante ≥ 80 vértices e ≥ 200 arestas?",
             f"coleta/montar_grafo.py valida n≥80 e m≥200 ao final da montagem; hoje o "
             f"grafo real tem n={n}, m={m} (bem acima do mínimo). Se ficasse abaixo, a reserva "
             "era aumentar álbuns por artista/artistas-semente ou usar o dataset LFM-2b."),
            ("O que mudou desde a Parte 1?",
             "Saiu o vértice “usuário” e tudo que dependia de dados pessoais (recomendação, "
             "comunidades, clusterização). O grafo foi reduzido a álbum-artista-gênero; arestas e "
             "pesos agora têm significado preciso e documentado (afinidade/custo de descoberta), "
             "em vez de “relações de proximidade” genéricas; os dados passaram a ser reais, "
             "coletados via API pública."),
            ("Quais as limitações do projeto?",
             "Amostra pequena e curada (16 artistas-semente, até 4 álbuns cada) não representa a "
             "indústria toda; os gêneros dependem das tags votadas pela comunidade do MusicBrainz "
             "(podem ser incompletas ou tendenciosas); afinidade é uma proxy de popularidade da "
             "tag, não uma medida musicológica; o grafo é um retrato estático (28/09/2026), sem "
             "atualização automática."),
        ],
        larguras=[Cm(6.0), Cm(10.8)],
    )

    # ------------------------------------------------------------ referência rápida
    titulo(doc, "5. Referência rápida - gêneros e artistas-ponte", nivel=1)
    paragrafo(
        doc,
        "Verificado em dados/arestas.csv + dados/vertices.csv (campo “cena” de "
        "dados/brutos/*.json): [GEN] soul e [GEN] r&b têm arestas ART-GEN diretas com artistas "
        "das duas cenas - os artistas-ponte diretos são [ART] Tim Maia (MPB) e "
        "[ART] Anderson .Paak (R&B/hip-hop), ambos ligados a [GEN] soul. [GEN] funk e [GEN] pop "
        "também ligam as duas cenas, mas por arestas ALB-GEN (álbuns de artistas de ambos os "
        "lados usam essas tags), não diretamente por ART-GEN.",
        tamanho=9.5,
    )

    doc.save(CAMINHO_SAIDA)
    print(f"Gerado: {CAMINHO_SAIDA}")
    print(f"n={n} m={m} idx_frank_ocean={idx_frank} idx_gen_soul={idx_soul} v_novo={v_novo}")


if __name__ == "__main__":
    gerar()
