# -*- coding: utf-8 -*-
"""
Projeto de Teoria dos Grafos - Parte 3
Descoberta Musical por Grafos: Álbuns, Artistas e Gêneros

Integrante: Luis Felipe Santos do Nascimento - RA 10420572

Síntese: aplicação de console com o menu de opções a-q, operando sobre o
grafo tripartido álbum-artista-gênero (matriz de adjacência, tipo 2) lido
de dados/grafo.txt. Opções a-i: manipulação do grafo (Parte 2); j-k:
solução do problema com Dijkstra (trilha de descoberta e recomendação);
l-p: características do grafo (graus, coloração, Euler, Hamilton,
bipartição/planaridade); q: encerrar.

Histórico de alterações:
  28/09/2026 - Luis Felipe - criação
  28/09/2026 - Luis Felipe - trata EOFError no laço principal, corrige
    captura de exceções em op_b e valida a opção do submenu de op_h
  28/09/2026 - Luis Felipe - normaliza CAMINHO_PADRAO (remove "src/.."
    do caminho exibido) e arredonda o peso lido em ler_real para 2 casas
    decimais, alinhando memória e arquivo
  19/11/2026 - Luis Felipe - Parte 3: opções j-p (Dijkstra, recomendação,
    graus, coloração por classe, Euler, Hamilton, bipartição/planaridade);
    encerrar passa para a opção q; vértices das opções j e k podem ser
    informados pelo índice ou por parte do nome
"""
import os

import algoritmos
from arquivo_grafo import formatarConteudo, gravar, ler

TITULO = "DESCOBERTA MUSICAL POR GRAFOS — Álbuns, Artistas e Gêneros"
CAMINHO_PADRAO = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dados", "grafo.txt")
)
OPCOES = [
    ("a", "Ler dados do arquivo grafo.txt"), ("b", "Gravar dados no arquivo grafo.txt"),
    ("c", "Inserir vértice"), ("d", "Inserir aresta"), ("e", "Remover vértice"),
    ("f", "Remover aresta"), ("g", "Mostrar conteúdo do arquivo"), ("h", "Mostrar grafo"),
    ("i", "Apresentar a conexidade do grafo"),
    ("j", "Trilha de descoberta de menor custo entre dois vértices (Dijkstra)"),
    ("k", "Recomendar álbuns próximos de um álbum (Dijkstra)"),
    ("l", "Característica: graus dos vértices"),
    ("m", "Característica: coloração de vértices (número de cores)"),
    ("n", "Característica: grafo euleriano / percurso euleriano"),
    ("o", "Característica: grafo hamiltoniano / caminho hamiltoniano"),
    ("p", "Característica: bipartição e planaridade"),
    ("q", "Encerrar a aplicação"),
]
PRECISA_GRAFO = set("bcdefhijklmnop")
TIPOS = {"1": "ALB", "2": "ART", "3": "GEN"}


class Aplicacao:
    def __init__(self, entrada, caminho_padrao):
        self.entrada = entrada
        self.caminho_padrao = caminho_padrao
        self.grafo = None

    # -------------------------------------------------------------- leitura
    def perguntar(self, texto):
        return self.entrada(texto).strip()

    def ler_inteiro(self, texto, minimo, maximo):
        """Lê inteiro em [minimo, maximo]; Enter vazio cancela (None)."""
        while True:
            valor = self.perguntar(texto)
            if valor == "":
                return None
            if valor.lstrip("-").isdigit():
                numero = int(valor)
                if minimo <= numero <= maximo:
                    return numero
                print(f"  Valor fora do intervalo [{minimo}, {maximo}].")
            else:
                print("  Entrada inválida: digite um número inteiro.")

    def ler_real(self, texto):
        """Lê peso real em [0, 1] (2 casas decimais); Enter vazio cancela (None)."""
        while True:
            valor = self.perguntar(texto).replace(",", ".")
            if valor == "":
                return None
            try:
                numero = float(valor)
                if 0.0 <= numero <= 1.0:
                    return round(numero, 2)
                print("  O peso (custo de descoberta) deve estar entre 0 e 1.")
            except ValueError:
                print("  Entrada inválida: digite um número real (ex.: 0.35).")

    def ler_vertice(self, texto):
        return self.ler_inteiro(texto, 0, self.grafo.n - 1)

    def buscar_vertice(self, texto, tipo=None):
        """Lê um vértice pelo índice OU por parte do rótulo (sem diferenciar
        maiúsculas). Com vários resultados, lista até 10 e pergunta de novo.
        `tipo` (ex.: "ALB") restringe a busca. Enter vazio cancela (None)."""
        while True:
            valor = self.perguntar(texto)
            if valor == "":
                return None
            if valor.isdigit():
                v = int(valor)
                if 0 <= v < self.grafo.n and (tipo is None or self.grafo.tipoVertice(v) == tipo):
                    return v
                print("  Índice inválido" + (f" (deve ser um vértice [{tipo}])." if tipo else "."))
                continue
            achados = [v for v, r in enumerate(self.grafo.rotulos)
                       if valor.lower() in r.lower()
                       and (tipo is None or self.grafo.tipoVertice(v) == tipo)]
            if len(achados) == 1:
                print(f"  -> {achados[0]} {self.grafo.rotulos[achados[0]]}")
                return achados[0]
            if not achados:
                print("  Nenhum vértice encontrado com esse nome.")
                continue
            print(f"  {len(achados)} vértices encontrados; digite o índice:")
            for v in achados[:10]:
                print(f"    {v:3d} {self.grafo.rotulos[v]}")
            if len(achados) > 10:
                print("    ...")

    def caminho(self):
        valor = self.perguntar(f"Caminho do arquivo [Enter = {self.caminho_padrao}]: ")
        return valor or self.caminho_padrao

    # -------------------------------------------------------------- opções
    def op_a(self):
        caminho = self.caminho()
        try:
            self.grafo = ler(caminho)
            print(f"Grafo lido: {self.grafo.n} vértices, {self.grafo.m} arestas.")
        except (OSError, ValueError) as erro:
            print(f"Não foi possível ler o arquivo: {erro}")

    def op_b(self):
        caminho = self.caminho()
        try:
            gravar(self.grafo, caminho)
            print(f"Grafo gravado em {caminho} ({self.grafo.n} vértices, {self.grafo.m} arestas).")
        except (OSError, ValueError) as erro:
            print(f"Não foi possível gravar: {erro}")

    def op_c(self):
        tipo = self.perguntar("Tipo do vértice (1 = álbum, 2 = artista, 3 = gênero): ")
        if tipo not in TIPOS:
            print("Tipo inválido. Operação cancelada.")
            return
        nome = self.perguntar("Nome: ").replace('"', "'")
        if not nome:
            print("Nome vazio. Operação cancelada.")
            return
        rotulo = f"[{TIPOS[tipo]}] {nome}"
        if rotulo in self.grafo.rotulos:
            print(f"Já existe o vértice {rotulo}.")
            return
        print(f"Vértice {self.grafo.insereV(rotulo)} inserido: {rotulo}")

    def op_d(self):
        v = self.ler_vertice("Vértice v: ")
        w = None if v is None else self.ler_vertice("Vértice w: ")
        peso = None if w is None else self.ler_real(
            "Peso (custo de descoberta, 0 a 1, 2 casas decimais): "
        )
        if peso is None:
            print("Operação cancelada.")
            return
        if self.grafo.insereA(v, w, peso):
            print(f"Aresta inserida: {self.grafo.rotulos[v]} <-> {self.grafo.rotulos[w]} (peso {peso:.2f})")
        else:
            print("Aresta não inserida: já existe, é um laço ou liga vértices do mesmo tipo "
                  "(o grafo é tripartido: álbum, artista e gênero).")

    def op_e(self):
        v = self.ler_vertice("Vértice a remover: ")
        if v is None:
            print("Operação cancelada.")
            return
        rotulo, grau = self.grafo.rotulos[v], self.grafo.grau(v)
        self.grafo.removeV(v)
        print(f"Removido {rotulo} e {grau} aresta(s) incidente(s). "
              f"Os vértices após {v} tiveram o índice reduzido em 1.")

    def op_f(self):
        v = self.ler_vertice("Vértice v: ")
        w = None if v is None else self.ler_vertice("Vértice w: ")
        if w is None:
            print("Operação cancelada.")
        elif self.grafo.removeA(v, w):
            print(f"Aresta removida: {self.grafo.rotulos[v]} <-> {self.grafo.rotulos[w]}")
        else:
            print("Não existe aresta entre esses vértices.")

    def op_g(self):
        caminho = self.caminho()
        try:
            print(formatarConteudo(caminho))
        except (OSError, ValueError) as erro:
            print(f"Não foi possível mostrar o arquivo: {erro}")

    def op_h(self):
        forma = self.perguntar("Mostrar como 1 = lista de adjacência, 2 = matriz de adjacência: ")
        if forma not in ("1", "2"):
            print("Opção inválida.")
            return
        print(self.grafo.textoMatriz() if forma == "2" else self.grafo.textoLista())

    def op_i(self):
        comps = self.grafo.componentes()
        print(f"O grafo é {'CONEXO' if len(comps) <= 1 else 'DESCONEXO'} "
              f"({len(comps)} componente(s) conexa(s)).")
        for k, comp in enumerate(sorted(comps, key=len, reverse=True), start=1):
            amostra = "; ".join(self.grafo.rotulos[v] for v in comp[:8])
            extra = " ..." if len(comp) > 8 else ""
            print(f"  Componente {k}: {len(comp)} vértice(s) - {amostra}{extra}")
        print("Obs.: grafo NÃO orientado - as categorias C0-C3, o algoritmo FCONEX e o grafo "
              "reduzido se aplicam a grafos orientados.")

    # -------------------------------------------------------------- Parte 3
    def mostrar_rota(self, rota):
        """Imprime cada passo da trilha com o custo da aresta e o acumulado."""
        acumulado = 0.0
        print(f"   {self.grafo.rotulos[rota[0]]}")
        for anterior, v in zip(rota, rota[1:]):
            peso = self.grafo.peso(anterior, v)
            acumulado += peso
            print(f"   -> {self.grafo.rotulos[v]}   (custo {peso:.2f}; acumulado {acumulado:.2f})")

    def op_j(self):
        origem = self.buscar_vertice("Vértice de partida (índice ou parte do nome): ")
        destino = None if origem is None else self.buscar_vertice(
            "Vértice de chegada (índice ou parte do nome): ")
        if destino is None:
            print("Operação cancelada.")
            return
        if origem == destino:
            print("Partida e chegada são o mesmo vértice: custo 0.00.")
            return
        custo, rota = algoritmos.trilha_descoberta(self.grafo, origem, destino)
        if not rota:
            print("Não existe caminho entre esses vértices (estão em componentes diferentes).")
            return
        print(f"Trilha de descoberta de menor custo ({len(rota) - 1} passo(s), "
              f"custo total {custo:.2f}):")
        self.mostrar_rota(rota)

    def op_k(self):
        album = self.buscar_vertice("Álbum de partida (índice ou parte do nome): ", tipo="ALB")
        if album is None:
            print("Operação cancelada.")
            return
        k = self.ler_inteiro("Quantos álbuns recomendar (1 a 10) [Enter = 5]: ", 1, 10) or 5
        recomendados = algoritmos.recomendar_albuns(self.grafo, album, k)
        if not recomendados:
            print("Nenhum álbum de outro artista é alcançável a partir deste álbum.")
            return
        print(f"Álbuns de outros artistas mais próximos de {self.grafo.rotulos[album]}:")
        for posicao, (custo, v, rota) in enumerate(recomendados, start=1):
            via = " -> ".join(self.grafo.rotulos[x].split("] ", 1)[1] for x in rota[1:-1])
            print(f"  {posicao}. {self.grafo.rotulos[v]}  custo {custo:.2f}  (via {via})")

    def op_l(self):
        r = algoritmos.resumo_graus(self.grafo)
        nomes = {"ART": "Artistas", "ALB": "Álbuns", "GEN": "Gêneros"}
        print(f"Soma dos graus = {r['soma']} = 2 x m = 2 x {self.grafo.m} (lema do aperto de mãos)")
        print(f"Grau médio = {r['soma'] / self.grafo.n:.2f}   vértices isolados: {len(r['isolados'])}"
              f"   vértices de grau ímpar: {r['impares']}")
        for tipo, d in r["por_tipo"].items():
            print(f"  {nomes[tipo]:9s} ({d['qtd']:2d}): mín {d['min']:2d}  máx {d['max']:2d}  "
                  f"média {d['media']:.2f}  | maior grau: {self.grafo.rotulos[d['vmax']]}")
        print("Distribuição (grau: quantidade de vértices):")
        print("  " + "  ".join(f"{d}:{q}" for d, q in r["distribuicao"].items()))

    def op_m(self):
        classes = algoritmos.coloracao_por_classe(self.grafo)
        valida = algoritmos.coloracao_valida(self.grafo, classes)
        print("Coloração por classe, com vértices rerotulados por grau decrescente:")
        for c, classe in enumerate(classes, start=1):
            tipos = {}
            for v in classe:
                tipos[self.grafo.tipoVertice(v)] = tipos.get(self.grafo.tipoVertice(v), 0) + 1
            resumo = ", ".join(f"{q} {t}" for t, q in sorted(tipos.items()))
            amostra = "; ".join(self.grafo.rotulos[v] for v in classe[:3])
            print(f"  Cor {c}: {len(classe)} vértice(s) ({resumo}) - ex.: {amostra} ...")
        print(f"Cores usadas: {len(classes)}   coloração válida: {'sim' if valida else 'NÃO'}")
        tri = algoritmos.encontrar_triangulo(self.grafo)
        if tri:
            print("Triângulo (exige >= 3 cores): " + " - ".join(self.grafo.rotulos[v] for v in tri))
            if len(classes) == 3:
                print("Número cromático = 3 (3 cores bastam e o triângulo impede 2).")

    def op_n(self):
        conexo = self.grafo.ehConexo()
        r = algoritmos.analise_euler(self.grafo, conexo)
        print(f"Conexo: {'sim' if conexo else 'não'}   vértices de grau ímpar: {len(r['impares'])}")
        amostra = "; ".join(f"{self.grafo.rotulos[v]} (grau {self.grafo.grau(v)})"
                            for v in r["impares"][:4])
        if amostra:
            print(f"  ex.: {amostra} ...")
        print(f"Resultado: {r['situacao']}")
        print("Teorema de Euler: ciclo euleriano <=> conexo e 0 vértices de grau ímpar; "
              "percurso aberto <=> exatamente 2.")
        if r["impares"] and conexo:
            print(f"Seriam necessárias ao menos {r['eulerizar']} arestas extras para eulerizar "
                  "o grafo (cada aresta corrige 2 vértices ímpares).")

    def op_o(self):
        conexo = self.grafo.ehConexo()
        r = algoritmos.analise_hamilton(self.grafo, conexo)
        n = self.grafo.n
        print(f"Dirac (todo grau >= n/2 = {n / 2:.1f}): {'satisfeita' if r['dirac'] else 'não satisfeita'}"
              f" (grau mínimo = {r['grau_min']})")
        print(f"Ore (d(u) + d(v) >= n = {n} para não adjacentes): "
              f"{'satisfeita' if r['ore'] else 'não satisfeita'}")
        print(f"Maior parte independente: [{r['tipo_maior']}] com {r['tam_maior']} vértices "
              f"(nenhuma aresta entre eles).")
        print(f"  ciclo hamiltoniano exige |S| <= n/2 = {n / 2:.1f}; "
              f"caminho exige |S| <= (n+1)/2 = {(n + 1) / 2:.1f}")
        print(f"Resultado: {r['conclusao']}")

    def op_p(self):
        bip, aresta = algoritmos.eh_bipartido(self.grafo)
        r = algoritmos.analise_planaridade(self.grafo)
        if bip:
            print("Bipartido: SIM (2-coloração por busca em largura).")
        else:
            v, w = aresta
            print(f"Bipartido: NÃO - a 2-coloração falha na aresta {self.grafo.rotulos[v]} - "
                  f"{self.grafo.rotulos[w]} (ciclo ímpar).")
        if r["triangulo"]:
            print("  Triângulo encontrado: " + " - ".join(self.grafo.rotulos[v] for v in r["triangulo"]))
        print("Tripartido: SIM - não há arestas entre vértices do mesmo tipo (ART, ALB, GEN).")
        print(f"Planaridade: m = {self.grafo.m} e 3n - 6 = {r['limite']} -> {r['conclusao']}")

    # -------------------------------------------------------------- laço
    def menu(self):
        print("\n" + "=" * len(TITULO))
        print(TITULO)
        print("=" * len(TITULO))
        for letra, texto in OPCOES:
            print(f"  {letra}) {texto}")

    def executar(self):
        while True:
            try:
                self.menu()
                opcao = self.perguntar("Opção: ").lower()
                if opcao == "q":
                    print("Encerrando a aplicação. Até logo!")
                    return
                if opcao not in dict(OPCOES):
                    print("Opção inválida.")
                    continue
                if opcao in PRECISA_GRAFO and self.grafo is None:
                    print("Nenhum grafo carregado. Use a opção a) primeiro.")
                    continue
                getattr(self, f"op_{opcao}")()
            except EOFError:
                print("Encerrando a aplicação. Até logo!")
                return


def executar(entrada=input, caminho_padrao=CAMINHO_PADRAO):
    Aplicacao(entrada, caminho_padrao).executar()


if __name__ == "__main__":
    executar()
