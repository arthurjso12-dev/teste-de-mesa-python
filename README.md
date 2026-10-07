# Mesa Automática para Python

Aplicativo educacional para acompanhar a execução de trechos de Python em um teste de mesa. A interface mostra a validação do código e uma tabela com as linhas executadas, os valores das variáveis e os detalhes de cada passo.

## Requisitos

- Python 3.12 ou superior
- Tkinter, normalmente incluído na instalação do Python para Windows

O projeto usa apenas módulos da biblioteca padrão do Python; não é necessário instalar pacotes com `pip`.

## Executar a interface gráfica

Na pasta do projeto, execute:

```powershell
python app_teste_mesa.py
```

Digite ou carregue um código, informe os valores de entrada separados por vírgula e selecione **Executar teste de mesa**. O exemplo incluído pode ser aberto pelo botão **Carregar exemplo**.

## Usar pela linha de comando

Analisar um arquivo Python:

```powershell
python mesa_automatica.py --file exemplo.py --inputs 7
```

Analisar código diretamente:

```powershell
python mesa_automatica.py --code "x = int(input())\ny = x + 5" --inputs 7
```

## O que aparece na tabela

- **Linha**: número da linha executada no código.
- **Código**: instrução correspondente.
- **Variáveis**: valores conhecidos naquele passo.
- **Detalhes**: operação realizada, condição avaliada ou saída simulada.

## Recursos suportados

O analisador inclui atribuições, `if`/`else`, `while`, `for` com `range` e listas, além de `input()`, `print()`, `int()`, `float()`, `str()` e `len()`. Ele é um recurso didático com suporte limitado à linguagem Python, não um interpretador completo.

## Arquivos do projeto

- `app_teste_mesa.py`: interface gráfica.
- `mesa_automatica.py`: mecanismo de análise e geração da tabela.
- `exemplo.py`: código de exemplo.
- `README.md`: documentação e instruções.
