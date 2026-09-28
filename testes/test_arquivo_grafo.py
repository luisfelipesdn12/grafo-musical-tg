# -*- coding: utf-8 -*-
"""
Projeto de Teoria dos Grafos - Parte 2
Descoberta Musical por Grafos: Álbuns, Artistas e Gêneros

Integrante: Luis Felipe Santos do Nascimento - RA 10420572

Síntese: testes unitários para leitura e gravação do arquivo grafo.txt
no formato especificado (tipo, n, vértices, m, arestas) e formatação
de conteúdo para exibição no menu.

Histórico de alterações:
  28/09/2026 - Luis Felipe - criação
  28/09/2026 - Luis Felipe - usa "with open" para fechar o arquivo (evita
    ResourceWarning) e insere o diretório do teste no sys.path para que
    "python -m unittest" a partir da raiz também encontre
    test_grafo_matriz
"""
import sys, os, unittest, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from arquivo_grafo import ler, gravar, formatarConteudo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_grafo_matriz import grafo_exemplo


class TestArquivo(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.caminho = os.path.join(self.dir, "grafo.txt")

    def test_ida_e_volta(self):
        g = grafo_exemplo()
        g.insereV("[ALB] Construção — Chico Buarque")
        gravar(g, self.caminho)
        h = ler(self.caminho)
        self.assertEqual(h.rotulos, g.rotulos)
        self.assertEqual(h.adj, g.adj)
        self.assertEqual((h.n, h.m), (g.n, g.m))

    def test_formato_texto(self):
        gravar(grafo_exemplo(), self.caminho)
        with open(self.caminho, encoding="utf-8") as arq:
            linhas = arq.read().splitlines()
        self.assertEqual(linhas[0:3], ["2", "5", '0 "[ART] A"'])
        self.assertEqual(linhas[7], "3")
        self.assertIn("0 1 0.00", linhas)

    def test_ida_e_volta_apos_remover(self):
        g = grafo_exemplo()
        g.removeV(1)
        gravar(g, self.caminho)
        self.assertEqual(ler(self.caminho).adj, g.adj)

    def test_tipo_invalido(self):
        with open(self.caminho, "w") as f:
            f.write("6\n0\n0\n")
        with self.assertRaises(ValueError):
            ler(self.caminho)

    def test_formatar(self):
        gravar(grafo_exemplo(), self.caminho)
        texto = formatarConteudo(self.caminho)
        self.assertIn("[GEN] soul", texto)
        self.assertIn("0.25", texto)


if __name__ == "__main__":
    unittest.main()
