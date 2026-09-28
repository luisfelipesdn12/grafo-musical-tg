# -*- coding: utf-8 -*-
"""
Projeto de Teoria dos Grafos - Parte 2
Descoberta Musical por Grafos: Álbuns, Artistas e Gêneros

Integrante: Luis Felipe Santos do Nascimento - RA 10420572

Síntese: testes de integração da aplicação de console (menu a-j) - fluxo
completo de leitura, inserção/remoção de vértices e arestas, gravação,
exibição e conexidade, simulando a entrada do usuário.

Histórico de alterações:
  28/09/2026 - Luis Felipe - criação
  28/09/2026 - Luis Felipe - insere o diretório do teste no sys.path
    para que "python -m unittest" a partir da raiz também encontre
    test_grafo_matriz
"""
import sys, os, io, unittest, tempfile, shutil
from contextlib import redirect_stdout
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import app
from arquivo_grafo import gravar, ler
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_grafo_matriz import grafo_exemplo


def rodar(respostas, caminho):
    it = iter(respostas)
    buf = io.StringIO()
    with redirect_stdout(buf):
        app.executar(entrada=lambda _="": next(it), caminho_padrao=caminho)
    return buf.getvalue()


class TestApp(unittest.TestCase):
    def setUp(self):
        self.diretorio = tempfile.mkdtemp()
        self.caminho = os.path.join(self.diretorio, "grafo.txt")
        gravar(grafo_exemplo(), self.caminho)

    def tearDown(self):
        shutil.rmtree(self.diretorio, ignore_errors=True)

    def test_titulo_e_sair(self):
        self.assertIn(app.TITULO, rodar(["j"], self.caminho))

    def test_sem_grafo(self):
        self.assertIn("Nenhum grafo carregado", rodar(["h", "j"], self.caminho))

    def test_fluxo_completo(self):
        # c: insere [GEN] rock (indice 5); d: 5-1 com peso "abc" (invalido,
        # pede de novo) e depois 0.3 -> GEN-ALB aceita; f: remove A-X;
        # e: remove A (ja sem arestas); b: grava; i: samba isolado -> DESCONEXO
        saida = rodar(["a", "", "c", "3", "rock", "d", "5", "1", "abc", "0.3",
                       "f", "0", "1", "e", "0", "b", "", "i", "j"], self.caminho)
        self.assertIn("inválida", saida)
        g = ler(self.caminho)
        self.assertEqual((g.n, g.m), (5, 3))
        self.assertIn("[GEN] rock", g.rotulos)
        self.assertNotIn("[ART] A", g.rotulos)
        self.assertIn("DESCONEXO", saida)

    def test_aresta_mesmo_tipo_recusada(self):
        saida = rodar(["a", "", "d", "0", "3", "0.1", "j"], self.caminho)
        self.assertIn("não inserida", saida)

    def test_indice_fora(self):
        saida = rodar(["a", "", "e", "99", "", "j"], self.caminho)
        self.assertIn("fora do intervalo", saida)

    def test_eof_encerra_sem_erro(self):
        # entrada esgota (sem "j") e levanta EOFError, simulando Ctrl+D:
        # a aplicação deve encerrar como na opção j, sem propagar a exceção.
        respostas = iter(["a", ""])

        def entrada(_=""):
            try:
                return next(respostas)
            except StopIteration:
                raise EOFError("EOF when reading a line")

        buf = io.StringIO()
        with redirect_stdout(buf):
            app.executar(entrada=entrada, caminho_padrao=self.caminho)
        self.assertIn("Encerrando a aplicação. Até logo!", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
