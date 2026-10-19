# Processamento de Imagens — Laboratório M2.1

Entrega referente ao Laboratório M2.1 — Máscara binária e segmentação, da disciplina de Processamento de Imagens.

A implementação foi realizada em Python e tem como objetivo produzir máscaras binárias para segmentar aves em imagens digitais, comparando diferentes métodos de limiarização em condições favoráveis e difíceis.

**Dependências:**

- opencv-python
- numpy
- pytest

**Execução:**

A execução é feita via terminal, utilizando o módulo principal:

```bash
python src/pdi_lab/__main__.py --input <caminho_entrada> --output <caminho_saida> --operation segment --method <metodo>
```

A operação segment gera uma máscara binária da imagem de entrada.

**Parâmetros disponíveis:**

- --input: caminho da imagem de entrada.
- --output: caminho da máscara gerada.
- --operation: operação a executar. Para este laboratório, utilizar segment.
- --method: método de segmentação: fixed, otsu, adaptive ou hsv.
- --threshold: limiar em tons de cinza para o método fixo, entre 0 e 255. Valor padrão: 120.
- --block-size: tamanho da vizinhança para a limiarização adaptativa. Deve ser ímpar e maior ou igual a 3. Valor padrão: 11.
- --constant: constante subtraída da média local na limiarização adaptativa. Valor padrão: 2.
- --hsv-min: limites mínimos de matiz, saturação e valor para a seleção HSV.
- --hsv-max: limites máximos de matiz, saturação e valor para a seleção HSV.

**Segmentação por limiar fixo em tons de cinza:**

Imagem favorável:

```bash
python src/pdi_lab/__main__.py --input images/input/favoravel.png --output images/output/favoravel_fixed.png --operation segment --method fixed --threshold 120
```

Imagem difícil:

```bash
python src/pdi_lab/__main__.py --input images/input/dificil.png --output images/output/dificil_fixed.png --operation segment --method fixed --threshold 120
```

**Segmentação pelo método de Otsu:**

Imagem favorável:

```bash
python src/pdi_lab/__main__.py --input images/input/favoravel.png --output images/output/favoravel_otsu.png --operation segment --method otsu
```

Imagem difícil:

```bash
python src/pdi_lab/__main__.py --input images/input/dificil.png --output images/output/dificil_otsu.png --operation segment --method otsu
```

**Segmentação por limiarização adaptativa:**

Imagem favorável:

```bash
python src/pdi_lab/__main__.py --input images/input/favoravel.png --output images/output/favoravel_adaptive.png --operation segment --method adaptive --block-size 11 --constant 2
```

Imagem difícil:

```bash
python src/pdi_lab/__main__.py --input images/input/dificil.png --output images/output/dificil_adaptive.png --operation segment --method adaptive --block-size 11 --constant 2
```

**Segmentação por intervalo HSV:**

Exemplo de execução, utilizando os limites padrão da implementação:

```bash
python src/pdi_lab/__main__.py --input images/input/favoravel.png --output images/output/favoravel_hsv.png --operation segment --method hsv --hsv-min 0 100 100 --hsv-max 10 255 255
```

Os limites do exemplo são ilustrativos e devem ser ajustados às características das imagens utilizadas.

As operações abaixo utilizam as máscaras já geradas pelas etapas de segmentação e as processam para remover ruídos e realizar a contagem dos pássaros:

Análise da imagem favorável:

```bash
python -m pdi_lab --input images/output/favoravel_otsu.png --output results/favoravel --operation analyze --connectivity 8 --min-area 20 --invert
```

Análise da imagem difícil:

```bash
python -m pdi_lab --input images/output/dificil_fixed.png --output results/dificil --operation analyze --connectivity 8 --min-area 20 --invert
```

**Executar testes automatizados:**

```bash
python -m pytest
```


