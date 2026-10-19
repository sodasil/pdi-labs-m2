## Declaração de IA

**Ferramenta:** ChatGPT

**Finalidade:** Suporte na sintaxe do python, na estruturação dos testes e na validação de erros.

**Partes Afetadas:** __main__.py e test_pdi_lab.py

**Forma de Validação:** Executar comandos no terminal verificando se retornam 0 e executar os testes com pytest.

**Modificações Realizadas:** Correções pontuais de sintaxe no geral, estruturação de test_pdi_lab.py cobrindo os cenários mínimos e validação do tratamento de erros e das condições de entrada.

**Registro:** 

    Pergunta: Como estruturar testes automatizados com pytest para cobrir os cenários mínimos exigidos?
    Orientação: Criar funções iniciadas com `test_` em um arquivo dedicado, utilizando asserções (`assert`) sobre matrizes sintéticas e incorporando margens de tolerância para validar conversões numéricas em ponto flutuante para `uint8`.
    Uso: Estruturação dos testes em test_pdi_lab.py.

    Pergunta: Como validar erros e tratar entradas inválidas na segmentação de imagens?
    Orientação: Verificar se a imagem de entrada foi carregada corretamente, validar os parâmetros dos métodos de segmentação, conferir as dimensões e os valores permitidos nas máscaras e tratar erros durante a leitura e a gravação dos arquivos.
    Uso: Implementado em __main__.py para validar as entradas, verificar as máscaras geradas e tratar exceções.