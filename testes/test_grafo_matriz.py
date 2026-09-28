import sys, os, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from grafo_matriz import GrafoMatrizPonderado


def grafo_exemplo():
    g = GrafoMatrizPonderado()
    for r in ["[ART] A", "[ALB] X — A", "[GEN] soul", "[ART] B", "[GEN] samba"]:
        g.insereV(r)
    g.insereA(0, 1, 0.0)   # A - X
    g.insereA(1, 2, 0.25)  # X - soul
    g.insereA(3, 2, 0.5)   # B - soul
    return g  # vertice 4 (samba) isolado


class TestGrafo(unittest.TestCase):
    def test_insere_e_simetria(self):
        g = grafo_exemplo()
        self.assertEqual((g.n, g.m), (5, 3))
        self.assertEqual(g.peso(1, 2), 0.25)
        self.assertEqual(g.peso(2, 1), 0.25)
        self.assertIsNone(g.peso(0, 2))

    def test_peso_zero_e_aresta(self):
        g = grafo_exemplo()
        self.assertEqual(g.peso(0, 1), 0.0)
        self.assertEqual(g.grau(0), 1)

    def test_recusa_invalidas(self):
        g = grafo_exemplo()
        self.assertFalse(g.insereA(0, 1, 0.3))   # ja existe
        self.assertFalse(g.insereA(2, 2, 0.1))   # laco
        self.assertFalse(g.insereA(0, 3, 0.1))   # ART-ART
        self.assertFalse(g.insereA(0, 99, 0.1))  # indice invalido
        self.assertFalse(g.insereA(1, 4, 1.5))   # peso fora de [0,1]
        self.assertEqual(g.m, 3)

    def test_remove_aresta(self):
        g = grafo_exemplo()
        self.assertTrue(g.removeA(2, 1))
        self.assertIsNone(g.peso(1, 2))
        self.assertEqual(g.m, 2)
        self.assertFalse(g.removeA(2, 1))

    def test_remove_vertice_reindexa(self):
        g = grafo_exemplo()
        self.assertTrue(g.removeV(2))  # soul: remove 2 arestas
        self.assertEqual((g.n, g.m), (4, 1))
        self.assertEqual(g.rotulos, ["[ART] A", "[ALB] X — A", "[ART] B", "[GEN] samba"])
        self.assertEqual(g.peso(0, 1), 0.0)
        for i in range(g.n):
            for j in range(g.n):
                self.assertEqual(g.adj[i][j], g.adj[j][i])
        self.assertFalse(g.removeV(10))

    def test_componentes(self):
        g = grafo_exemplo()
        self.assertEqual(g.componentes(), [[0, 1, 2, 3], [4]])
        self.assertFalse(g.ehConexo())
        g.insereA(3, 4, 0.1)
        self.assertTrue(g.ehConexo())

    def test_tipo_vertice(self):
        g = grafo_exemplo()
        self.assertEqual([g.tipoVertice(i) for i in range(3)], ["ART", "ALB", "GEN"])


if __name__ == "__main__":
    unittest.main()
