# -*- coding: utf-8 -*-
"""
Projeto de Teoria dos Grafos - Parte 3
Descoberta Musical por Grafos: Álbuns, Artistas e Gêneros

Integrante: Luis Felipe Santos do Nascimento - RA 10420572

Síntese: testes das técnicas da Parte 3 (src/algoritmos.py) - Dijkstra,
recomendação, graus, coloração por classe, Euler, Hamilton, bipartição e
planaridade - em grafos pequenos com resposta conhecida e no grafo real.

Histórico de alterações:
  19/11/2026 - Luis Felipe - criação
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import algoritmos as A  # noqa: E402
from arquivo_grafo import ler  # noqa: E402
from grafo_matriz import GrafoMatrizPonderado  # noqa: E402

CAMINHO_REAL = os.path.join(os.path.dirname(__file__), "..", "dados", "grafo.txt")


def grafo_dijkstra():
    """Dois artistas, dois álbuns e dois gêneros. O caminho direto
    ALB X -> GEN rock -> ALB Y custa 0,9 + 0,9 = 1,8; o caminho mais longo
    X -> GEN soul -> ART B -> Y custa 0,1 + 0,2 + 0,1 = 0,4."""
    g = GrafoMatrizPonderado()
    for r in ["[ART] A", "[ART] B", "[ALB] X — A", "[ALB] Y — B", "[GEN] soul", "[GEN] rock"]:
        g.insereV(r)
    g.insereA(0, 2, 0.1)   # A - X (autoria)
    g.insereA(1, 3, 0.1)   # B - Y (autoria)
    g.insereA(2, 5, 0.9)   # X - rock
    g.insereA(3, 5, 0.9)   # Y - rock
    g.insereA(2, 4, 0.1)   # X - soul
    g.insereA(1, 4, 0.2)   # B - soul
    return g


class TestDijkstra(unittest.TestCase):
    def test_prefere_menor_custo_a_menos_arestas(self):
        g = grafo_dijkstra()
        custo, rota = A.trilha_descoberta(g, 2, 3)
        self.assertAlmostEqual(custo, 0.4)
        self.assertEqual(rota, [2, 4, 1, 3])

    def test_inalcancavel(self):
        g = grafo_dijkstra()
        g.insereV("[GEN] isolado")
        self.assertEqual(A.trilha_descoberta(g, 0, 6), (A.INFINITO, []))

    def test_recomendacao_exclui_mesmo_artista(self):
        g = grafo_dijkstra()
        g.insereV("[ALB] Z — A")
        g.insereA(0, 6, 0.1)
        recs = A.recomendar_albuns(g, 2, k=5)
        self.assertEqual([v for _, v, _ in recs], [3])   # Z é do mesmo artista
        self.assertAlmostEqual(recs[0][0], 0.4)


class TestCaracteristicas(unittest.TestCase):
    def test_graus(self):
        r = A.resumo_graus(grafo_dijkstra())
        self.assertEqual(r["soma"], 12)          # 2 x 6 arestas
        self.assertEqual(r["impares"], 2)        # A (grau 1) e X (grau 3)
        self.assertEqual(r["graus"], [1, 2, 3, 2, 2, 2])

    def test_coloracao_triangulo(self):
        g = GrafoMatrizPonderado()
        for r in ["[ART] A", "[ALB] X — A", "[GEN] soul"]:
            g.insereV(r)
        g.insereA(0, 1, 0.1)
        g.insereA(1, 2, 0.1)
        g.insereA(0, 2, 0.1)
        classes = A.coloracao_por_classe(g)
        self.assertEqual(len(classes), 3)
        self.assertTrue(A.coloracao_valida(g, classes))
        self.assertIsNotNone(A.encontrar_triangulo(g))
        self.assertFalse(A.eh_bipartido(g)[0])

    def test_euler(self):
        g = grafo_dijkstra()
        r = A.analise_euler(g, True)
        self.assertEqual(r["impares"], [0, 2])   # A (grau 1) e X (grau 3)
        self.assertIn("SEMIEULERIANO", r["situacao"])

    def test_hamilton_parte_grande(self):
        # estrela: 1 artista e 3 álbuns -> parte ALB com 3 > (4 + 1)/2
        g = GrafoMatrizPonderado()
        g.insereV("[ART] A")
        for i in range(3):
            g.insereV(f"[ALB] {i} — A")
            g.insereA(0, i + 1, 0.1)
        r = A.analise_hamilton(g, True)
        self.assertTrue(r["sem_caminho"])
        self.assertIn("nem caminho", r["conclusao"])

    def test_planaridade_k5_sem_tipos(self):
        g = GrafoMatrizPonderado()
        for i in range(5):
            g.insereV(f"v{i}")        # sem prefixo de tipo: aceita qualquer aresta
        for i in range(5):
            for j in range(i + 1, 5):
                g.insereA(i, j, 0.5)
        self.assertIn("NÃO PLANAR", A.analise_planaridade(g)["conclusao"])  # 10 > 9


class TestGrafoReal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = ler(CAMINHO_REAL)

    def test_nenhum_par_de_albuns_com_custo_zero(self):
        g = self.g
        albuns = [v for v in range(g.n) if g.tipoVertice(v) == "ALB"]
        for a in albuns[:10]:
            dist, _ = A.dijkstra(g, a)
            for b in albuns:
                if b != a:
                    self.assertGreaterEqual(dist[b], 0.2 - 1e-9)

    def test_caracteristicas_reais(self):
        g = self.g
        classes = A.coloracao_por_classe(g)
        self.assertTrue(A.coloracao_valida(g, classes))
        self.assertEqual(len(classes), 3)
        self.assertFalse(A.eh_bipartido(g)[0])
        self.assertIn("NÃO PLANAR", A.analise_planaridade(g)["conclusao"])
        self.assertIn("NÃO HAMILTONIANO", A.analise_hamilton(g, True)["conclusao"])
        self.assertEqual(A.resumo_graus(g)["soma"], 2 * g.m)


if __name__ == "__main__":
    unittest.main()
