# Relatório — Laboratório M2.1: Máscara binária e segmentação

## Objetivo

O objetivo deste laboratório é implementar e avaliar métodos de segmentação de imagens, produzindo máscaras binárias para identificar os objetos de interesse. Foram utilizados quatro métodos: limiarização fixa, método de Otsu, limiarização adaptativa e segmentação por intervalo de cores HSV.

## Objeto de interesse e imagens

O objeto de interesse são os pássaros presentes nas imagens utilizadas nos experimentos.

Foram utilizadas duas imagens:

- **Imagem favorável (favoravel.png):** utilizada para avaliar o comportamento dos métodos em condições favoráveis.
- **Imagem difícil (dificil.png):** utilizada para analisar as limitações da segmentação quando a separação entre o objeto e o fundo é mais complexa.

## Métodos e parâmetros

### Limiarização fixa

O método converte a imagem para escala de cinza e aplica um limiar definido pelo usuário, valor padrão 120.

Com THRESH_BINARY pixels com intensidade superior ao limiar são classificados como brancos enquanto pixels com intensidade menor ou igual são classificados como pretos.

### Método de Otsu

O método de Otsu converte a imagem para escala de cinza e determina automaticamente um limiar com base na distribuição de intensidades dos pixels permitindo comparar a seleção automática do limiar com o valor fixo definido manualmente.

### Limiarização adaptativa

A limiarização adaptativa utiliza regiões locais da imagem para determinar os limiares, foi utilizado o método gaussiano adaptativo.

Os parâmetros padrão são:

Tamanho do bloco: 11 e
Constante: 2.

O tamanho do bloco deve ser ímpar e maior ou igual a 3. A constante influencia o resultado da classificação local.

### Segmentação por HSV

O método converte a imagem do espaço de cores BGR para HSV e seleciona os pixels dentro dos intervalos de matiz, saturação e valor definidos pelo usuário.

Os intervalos padrão são:

- HSV mínimo: (0, 100, 100)
- HSV máximo: (10, 255, 255)

### Polaridade da máscara

Os métodos fixo, otsu e adaptativo utilizam a classificação binária convencional onde os pixels acima do limiar são brancos.

## Resultados quantitativos

| Imagem | Método | Pixels brancos |
|---|---|---:|
| Favorável | Fixo | 99,49% |
| Favorável | Otsu | 99,36% |
| Favorável | Adaptativo | 99,56% |
| Favorável | HSV | 0,16% |
| Difícil | Fixo | 81,80% |
| Difícil | Otsu | 70,25% |
| Difícil | Adaptativo | 81,50% |
| Difícil | HSV | 0,00% |

A proporção de pixels brancos equivale a quantidade de pixels classificados como primeiro plano dividida pelo total de pixels da imagem.

Na imagem favorável os métodos em escala de cinza classificaram quase toda a imagem como branca, então a classificação atual pode não estar isolando os objetos corretamente.

Na imagem difícil os métodos fixo e adaptativo produziram proporções semelhantes e o otsu produziu uma proporção menor.

O método hsv produziu máscaras quase vazias com os intervalos padrão.

### a) Em quais condições o limiar fixo funciona ou falha?

O limiar fixo é simples e permite controlar diretamente a separação entre pixels claros e escuros e funciona bem quando existe contraste suficiente entre o objeto e o fundo. Mas quando as intensidades do objeto e do fundo são parecidas ou quando tem variações de iluminação um único limiar pode não separar adequadamente as regiões que é percepitível na imagem difícil.

### b) Qual parâmetro é mais sensível?

No método fixo o limiar controla a classificação dos pixels e na limiarização adaptativa o tamanho do bloco e a constante também influenciam a máscara, no hsv os limites de matiz, saturação e valor definem as cores selecionadas.

### c) Quais erros podem afetar a contagem de objetos no M2.2?

Falsos positivos quando pixels do fundo são classificados como parte do objeto e falsos negativos quando pixels pertencentes aos pássaros são classificados como fundo.

## Conclusão M2.1

Os experimentos permitem comparar diferentes estratégias de segmentação e observar como os resultados variam conforme o método e seus parâmetros.

A limiarização fixa utiliza um valor definido manualmente, o otsu seleciona automaticamente um limiar, a limiarização adaptativa considera variações locais e o hsv seleciona pixels com base em intervalos de cor.

Os resultados indicam que as configurações testadas ainda precisam ser avaliadas visualmente para determinar se isolam corretamente os pássaros. A proporção de pixels brancos não é suficiente para determinar sua qualidade. A configuração escolhida para o M2.2 vai ser a que tiver a melhor separação entre os objetos e menos erros.

---

# M2.2: Componentes conexos e sequência morfológica

## Objetivo

Ampliar o projeto M2.1 para realizar a limpeza da máscara binária através de uma sequência morfológica justificada, rotular os componentes conexos, exportar estatísticas individuais em CSV e avaliar quantitativa e visualmente a contagem final dos objetos em condições favoráveis e difíceis.

## Polaridade e Conectividade

Para as operações de morfologia e rotulação as máscaras foram processadas garantindo que o objeto de interesse seja branco e o fundo preto utilizando o parâmetro --invert durante a chamada da CLI.

A rotulação por componentes conexos foi executada e comparada na máscara inicial sem filtro com as seguintes diferenças teóricas e práticas:
- Conectividade 4: Considera apenas vizinhos ortogonais
- Conectividade 8: Considera vizinhos ortogonais e diagonais

| Imagem Original | Contagem Conectividade 4 | Contagem Conectividade 8 |
| :--- | :---: | :---: |
| **Favorável (`favoravel_otsu.png`)** | 32 componentes brutos | 28 componentes brutos |
| **Difícil (`dificil_fixed.png`)** | 632 componentes brutos | 528 componentes brutos |

Justificativa da escolha: Na conectividade 4 pixels em posição diagonal nas pontas das asas dos pássaros ou nas bordas das nuvens são tratados como objetos separados quebrando as estruturas e fragmentando o contorno. Na conectividade 8 essas conexões diagonais são reconhecidas unindo o corpo do pássaro e resultando em uma contagem menor e mais coerente com a forma real do objeto entao a conectividade 8 foi definida como padrão para a análise final.

## Sequência Morfológica Justificada

Foi aplicada uma sequência morfológica com as seguintes características:
- Parâmetros Base: Elemento Estruturante Elíptico (ellipse) tamanho 3x3, 1 iteração
- Ordem das Operações: Abertura (opening) -> Fechamento (closing)

**Justificativa das escolhas e defeitos visados:**
1. Abertura: Buscou eliminar ruídos isolados, pequenos pontos brancos no céu e diferenças conectadas ao fundo. Foi observado que essa removeu o micro-ruído sem perder o corpo central da ave.
2. Fechamento: Aplicado logo após a abertura para corrigir defeitos internos com o objetivo de preencher buracos pretos dentro da área branca das asas e consolidar micro-fraturas nos contornos garantindo que o pássaro seja detectado como um único componente.

## Filtragem por Área e Recontagem

Foi adotado um critério explícito de filtragem por área: --min-area 20. Qualquer componente conexo com área inferior a 20 foi descartado como ruído.

**Tabela Comparativa Antes e Depois:**

| Imagem / Etapa | Comp. Brutos (Sem Filtro) | Comp. Filtrados ($\ge 20$ px) | Área Total Primeiro Plano |
| :--- | :---: | :---: | :---: |
| **Favorável - Inicial (Pré-morfologia)** | 28 | 13 | 11.240 px |
| **Favorável - Final (Pós-morfologia)** | 13 | 13 | 11.180 px |
| **Difícil - Inicial (Pré-morfologia)** | 528 | 45 | 428.910 px |
| **Difícil - Final (Pós-morfologia)** | 382 | 38 | 425.400 px |

**Observações sobre as mudanças:**
1. Na imagem favorável a aplicação da morfologia reduziu os componentes brutos de 28 para 13. Ao aplicar o filtro de área no resultado final os 13 objetos foram classificados corretamente como aves maiores que 20 pixels. A área total se manteve estável, indicando ausência de degradação estrutural.
2. Na imagem difícil a morfologia reduziu de 528 para 382. Após a aplicação do filtro de área de 20 px restaram 38 grandes componentes, mostrando como o limiar fixo sofre com variações de luminosidade.

## Limitações

A contagem de objetos gerada pelo algoritmo via componentes conexos não equivale necessariamente à quantidade real de pássaros. Foram observados dois efeitos indesejados principais:

1. Sobreposição: Na imagem favorável a sequência morfológica limpou a máscara de forma excepcional mas quando dois pássaros estão voando de forma sobreposta o algoritmo de conectividade os rotula como um único componente. Isso faz com que a contagem automática seja inferior à percepção humana.
2. Oclusão e interferência do fundo: Na imagem difícil as nuvens espessas têm faixas de cor que se confundem com as aves. O resultado final gerou enormes manchas rótulas que engoliram os pássaros prejudicando totalmente a contagem e separação real dos objetos. 

A sequência morfológica ajudou no caso favorável ao limpar o céu mas não conseguiu resolver o problema de sobreposição entre aves ou separar as aves das nuvens complexas no caso difícil o que exigiria técnicas superiores.