# -*- coding: utf-8 -*-
"""
Projeto de Teoria dos Grafos - Parte 2
Descoberta Musical por Grafos: Álbuns, Artistas e Gêneros

Integrante: Luis Felipe Santos do Nascimento - RA 10420572

Síntese: testes unitários de montar_grafo - cálculo de afinidades por
gênero e montagem do grafo tripartido a partir dos dados brutos, além do
teste de sanidade sobre o dados/grafo.txt real gerado pela coleta.

Histórico de alterações:
  28/09/2026 - Luis Felipe - criação
"""

import sys, os, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "coleta"))
from montar_grafo import construir, afinidades


def gen(**kw):
    return [{"name": k.replace("_", " "), "count": v} for k, v in kw.items()]


ARTISTAS = [
    {"nome": "A", "genres": gen(soul=4, funk=2),
     "albuns": [{"title": "X", "first-release-date": "2000", "genres": gen(soul=2)},
                {"title": "Y \"live\"", "first-release-date": "2001", "genres": gen(funk=1, rock=1)}]},
    {"nome": "B", "genres": gen(soul=1, samba=3),
     "albuns": [{"title": "Z", "first-release-date": "1970", "genres": gen(samba=5, soul=5)}]},
]


class TestMontar(unittest.TestCase):
    def test_afinidades(self):
        self.assertEqual(afinidades(gen(a=4, b=2, c=1), 2), [("a", 1.0), ("b", 0.5)])

    def test_construir(self):
        g = construir(ARTISTAS)
        self.assertEqual(g.rotulos[:2], ["[ART] A", "[ART] B"])
        self.assertIn("[ALB] Y 'live' — A", g.rotulos)
        # rock ligado a 1 entidade só -> descartado
        self.assertNotIn("[GEN] rock", g.rotulos)
        self.assertIn("[GEN] samba", g.rotulos)
        a, x = g.rotulos.index("[ART] A"), g.rotulos.index("[ALB] X — A")
        self.assertEqual(g.peso(a, x), 0.0)
        soul, b = g.rotulos.index("[GEN] soul"), g.rotulos.index("[ART] B")
        self.assertEqual(g.peso(b, soul), 0.67)  # 1 - 1/3
        for v in range(g.n):
            for w, _ in g.vizinhos(v):
                self.assertNotEqual(g.tipoVertice(v), g.tipoVertice(w))


class TestGrafoReal(unittest.TestCase):
    def test_minimos(self):
        from arquivo_grafo import ler
        caminho = os.path.join(os.path.dirname(__file__), "..", "dados", "grafo.txt")
        g = ler(caminho)
        self.assertGreaterEqual(g.n, 80)
        self.assertGreaterEqual(g.m, 200)


if __name__ == "__main__":
    unittest.main()
