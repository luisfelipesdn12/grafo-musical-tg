# Descoberta Musical por Grafos — Álbuns, Artistas e Gêneros

Projeto da disciplina **Teoria dos Grafos** (Faculdade de Computação e Informática, Universidade
Presbiteriana Mackenzie) — Prof. Dr. Ivan Carlos Alcântara de Oliveira.

**Integrante:** Luis Felipe Santos do Nascimento — RA 10420572

## Objetivo

O projeto modela, como um grafo, o universo de descoberta musical formado por artistas, seus
álbuns de estúdio e os gêneros musicais associados a cada um, a partir de dados públicos da API do
MusicBrainz. Este é o escopo reduzido definido após o retorno recebido na Parte 1: em vez de dados
de usuário (histórico de audição, playlists, recomendações personalizadas), o grafo passou a
conter apenas metadados públicos — artistas, álbuns e gêneros —, o que manteve o problema tratável
e os dados totalmente verificáveis a partir de uma API aberta.

## Modelo do grafo

Grafo **não orientado, com peso nas arestas** (tipo 2), tripartido entre três tipos de vértice.
Estado atual: **109 vértices** e **349 arestas**, **conexo** (uma única componente).

Na Parte 3 (versão final), o problema é **resolvido com o algoritmo de Dijkstra** (trilha de
descoberta de menor custo e recomendação de álbuns) e cinco técnicas da disciplina revelam
características do grafo (graus, coloração, Euler, Hamilton, bipartição/planaridade).

### Vértices

| Prefixo do rótulo | Significado | Quantidade |
|---|---|---|
| `[ART]` | Artista (dos 16 artistas semente coletados) | 16 |
| `[ALB]` | Álbum de estúdio de um dos artistas | 56 |
| `[GEN]` | Gênero musical votado pela comunidade do MusicBrainz | 37 |

### Arestas

| Ligação | Semântica | Peso |
|---|---|---|
| artista — álbum | autoria: o álbum é do artista | `0.10` (custo mínimo de um passo) |
| artista — gênero | o artista está associado ao gênero | `0.10 + 0.90 × (1 − afinidade)` |
| álbum — gênero | o álbum está associado ao gênero | `0.10 + 0.90 × (1 − afinidade)` |

Não há arestas entre vértices do mesmo tipo (grafo tripartido) nem entre um artista e um álbum de
outro artista — a aresta de autoria liga cada álbum apenas ao seu próprio artista.

**Afinidade:** para cada artista/álbum, calculada a partir dos votos de gênero (`genres[].count`)
retornados pelo MusicBrainz — apenas os `top-k` gêneros mais votados (k = 5) entram como candidatos
a aresta, e a afinidade de cada um é a razão entre seus votos e os votos do gênero mais votado
daquele artista/álbum:

```
afinidade(g) = votos(g) / votos(gênero mais votado)      # em [0, 1]
```

**Peso da aresta (custo de descoberta):**

```
peso = 0.10 + 0.90 × (1 − afinidade)     # em [0.10, 1.00]
```

Na Parte 2 o peso era `1 − afinidade` e a autoria custava 0; como o gênero mais votado de cada
entidade tem afinidade 1, todos os álbuns ficavam ligados por caminhos de custo zero. Com o custo
mínimo de 0,10 por passo, nenhuma trilha entre álbuns diferentes custa menos de 0,20.

Quanto maior a afinidade (gênero mais consensual para aquele artista/álbum), menor o custo de
"descobrir" aquele gênero a partir dele — pensando em um algoritmo de caminho mínimo (ex.:
Dijkstra) como uma trilha de descoberta musical.

### Visualização

![Grafo tripartido álbum-artista-gênero](visualizacao/grafo.png)

Vermelho = artista, azul-petróleo = álbum, laranja = gênero. Versão interativa (zoom, pan e hover
com o rótulo completo de cada vértice) em [`visualizacao/grafo_interativo.html`](visualizacao/grafo_interativo.html).

## Como executar

Requer Python 3.12+. A partir da raiz do repositório:

```bash
python3 -m venv .venv
source .venv/bin/activate       # Linux/macOS
pip install -r requirements.txt
```

**Aplicação de console** (menu a-q sobre `dados/grafo.txt`):
```bash
python3 src/app.py
```

**Testes automatizados** (38 testes unitários/integração, `unittest`):
```bash
python3 -m unittest discover -s testes -v
```

**Coleta dos dados brutos** na API pública do MusicBrainz (grava um JSON por artista em
`dados/brutos/`; retomável — pula artistas já coletados):
```bash
python3 coleta/coletar_musicbrainz.py
```

**Montagem do grafo** a partir dos dados brutos (gera `dados/grafo.txt`, `dados/vertices.csv` e
`dados/arestas.csv`; aceita opcionalmente o número máximo de álbuns por artista, padrão 4):
```bash
python3 coleta/montar_grafo.py [max_albuns]
```

**Visualização** (gera `visualizacao/grafo_interativo.html`, `visualizacao/grafo.png` e
`visualizacao/grafo.gexf`, este último para abrir no Gephi):
```bash
python3 visualizacao/visualizar.py
```

**Prints de teste da aplicação** (gera as capturas de tela do menu usadas no relatório):
```bash
python3 ferramentas/gerar_prints.py
```

### Menu da aplicação (`src/app.py`)

| Opção | Ação |
|---|---|
| a | Ler dados do arquivo `grafo.txt` |
| b | Gravar dados no arquivo `grafo.txt` |
| c | Inserir vértice |
| d | Inserir aresta |
| e | Remover vértice |
| f | Remover aresta |
| g | Mostrar conteúdo do arquivo |
| h | Mostrar grafo (lista ou matriz de adjacência) |
| i | Apresentar a conexidade do grafo |
| j | Trilha de descoberta de menor custo entre dois vértices (Dijkstra) |
| k | Recomendar álbuns próximos de um álbum (Dijkstra) |
| l | Característica: graus dos vértices |
| m | Característica: coloração de vértices (coloração por classe) |
| n | Característica: grafo euleriano / percurso euleriano |
| o | Característica: grafo hamiltoniano / caminho hamiltoniano |
| p | Característica: bipartição e planaridade |
| q | Encerrar a aplicação |

Nas opções j e k, o vértice pode ser informado pelo índice ou por parte do nome.

### Resultados da Parte 3

| Técnica | Resultado |
|---|---|
| Dijkstra (j) | Blonde (Frank Ocean) → Domingo (Caetano Veloso): 5 passos, custo 0,50 |
| Recomendação (k) | 5 álbuns de outros artistas mais próximos de um álbum, com a trilha de cada um |
| Graus (l) | soma = 698 = 2m; 52 vértices de grau ímpar; maior grau: gênero mpb (30) |
| Coloração (m) | 3 cores; há triângulo, logo χ(G) = 3 |
| Euler (n) | não admite ciclo nem percurso euleriano |
| Hamilton (o) | 56 álbuns independentes > (n+1)/2 = 55: não admite ciclo nem caminho hamiltoniano |
| Bipartição/planaridade (p) | não bipartido (triângulo); m = 349 > 3n − 6 = 321: não planar |

## Estrutura do repositório

| Caminho | Conteúdo |
|---|---|
| `src/grafo_matriz.py` | Classe `GrafoMatrizPonderado` — grafo não orientado com peso na aresta (tipo 2), matriz de adjacência |
| `src/arquivo_grafo.py` | Leitura/gravação de `dados/grafo.txt` no formato do enunciado e formatação para exibição |
| `src/algoritmos.py` | Dijkstra, recomendação e técnicas de investigação (graus, coloração, Euler, Hamilton, bipartição, planaridade) |
| `src/app.py` | Aplicação de console com o menu a-q |
| `coleta/coletar_musicbrainz.py` | Coleta na API pública do MusicBrainz (artistas, álbuns, gêneros votados) |
| `coleta/montar_grafo.py` | Monta o grafo tripartido a partir dos dados brutos e grava `dados/` |
| `coleta/artistas_semente.txt` | Lista dos 16 artistas semente da coleta |
| `dados/grafo.txt` | Grafo no formato do enunciado (tipo, vértices, arestas) |
| `dados/vertices.csv`, `dados/arestas.csv` | Exportação tabular do grafo |
| `dados/brutos/` | Um JSON por artista, como recebido do MusicBrainz |
| `testes/` | Testes automatizados (`unittest`) de `src/` e `coleta/montar_grafo.py` |
| `visualizacao/visualizar.py` | Gera o HTML interativo (Plotly), o PNG e o GEXF (Gephi) do grafo |
| `visualizacao/grafo.png`, `grafo_interativo.html`, `grafo.gexf` | Saídas da visualização |
| `ferramentas/gerar_prints.py` | Gera as capturas de tela do menu a-q usadas no relatório |
| `ferramentas/gerar_relatorio.py` | Gera `relatorio/Relatorio_Projeto_TG_Parte3.docx` (relatório final) |
| `relatorio/` | Relatórios (Parte 2 e final) e figuras usadas neles |

## Fonte dos dados

Dados coletados na API pública do [MusicBrainz](https://musicbrainz.org/) (`ws/2`, sem
autenticação, sem dados de usuário) — apenas os "core data" (artistas, álbuns/release-groups e
gêneros votados pela comunidade), que o MusicBrainz licencia sob
[CC0](https://musicbrainz.org/doc/About/Data_License) (domínio público). Data da coleta: conforme
o campo `coletado_em` de cada arquivo em `dados/brutos/*.json`.

## Relatório e vídeo

- **Relatório final (Parte 3):** [`relatorio/Relatorio_Projeto_TG_Parte3.docx`](relatorio/Relatorio_Projeto_TG_Parte3.docx)
  ([PDF](relatorio/Relatorio_Projeto_TG_Parte3.pdf))
- **Relatório da Parte 2:** [`relatorio/Relatorio_Projeto_TG_Parte2.docx`](relatorio/Relatorio_Projeto_TG_Parte2.docx)
  ([PDF](relatorio/Relatorio_Projeto_TG_Parte2.pdf))
- **Vídeo (YouTube):** a publicar.

## Trabalhos futuros

Ampliar a semente de artistas para testar a robustez dos gêneros-ponte e usar outras fontes de
afinidade (por exemplo, colaborações entre artistas) para reduzir os empates de custo causados
pela escassez de votos de gênero.

## Observações de ambiente

- `pip install -r requirements.txt` já inclui `numpy`, necessário internamente pelo
  `networkx.spring_layout` usado em `visualizacao/visualizar.py`.
- O `kaleido` 0.2.1 (usado para exportar `visualizacao/grafo.png`) não funciona se o `.venv`
  estiver em um caminho com espaços (ex.: `.../teoria dos grafos/...`). Se `visualizar.py` avisar
  que não conseguiu gerar o PNG, as opções são: (a) recriar o `.venv` em um caminho sem espaços, ou
  (b) abrir `visualizacao/grafo_interativo.html` no navegador e usar o botão de câmera (canto
  superior direito do gráfico) para baixar o PNG manualmente. O HTML e o GEXF são sempre gerados
  normalmente, independentemente desse problema.
