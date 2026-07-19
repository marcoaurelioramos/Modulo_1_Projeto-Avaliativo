# Pipeline de Dados: Viagens a Serviço (Portal da Transparência 2025)

## Sobre o Projeto
Este é o projeto avaliaivo do curso de Análise de Dados com Pyton da SCTEC. Ele consiste em um pipeline de dados automatizado (ETL) construído com a **Arquitetura Medallion** (camadas Raw, Silver e Gold) para processar, higienizar e analisar os gastos públicos com viagens a serviço do Governo Federal durante 6 meses do ano de 2025.

O objetivo principal é transformar dados brutos e desorganizados em informações estruturadas e insights visuais para a tomada de decisões e auditorias de transparência.

---

## Arquitetura do Pipeline

O projeto é modular e segue a ordem de execução indicada pela numeração dos arquivos:

1. **Fase 0 (`0_criar_banco.sql`)**: Criação do banco de dados `transparencia` e definição das tabelas Raw (dados brutos como texto) e Silver (dados tipados com constraints de integridade).
2. **Fase 1 (`1_extrair.py`)**: Download automatizado e idempotente do arquivo ZIP contendo os CSVs originais, carregando-os diretamente na camada Raw.
3. **Fase 2 (`2_transformar.py`)**: Pipeline de higienização e transformação dos dados (conversão de formatos regionais de moedas, tratamento de datas, remoção de duplicidades e cálculo de colunas de negócio).
4. **Fase 3 (`3_analise.ipynb`)**: Criação da camada Gold no banco de dados (Tabela física agregada e VIEW analítica) e geração de relatórios gráficos (Dataviz).

---

## Tecnologias e Técnicas Utilizadas

- **Linguagem Principal**: Python 3.10+
- **Banco de Dados**: PostgreSQL
- **Bibliotecas de Manipulação**: Pandas
- **Visualização de Dados**: Matplotlib e Seaborn
- **Técnicas de Engenharia**: Carga em lotes (chunks), idempotência (Truncate-and-Load), tratamento de exceções (resiliência) e isolamento de credenciais via `.env`.


---

## Como Executar o Projeto em Qualquer Máquina

Siga o passo a passo abaixo para garantir o isolamento do ambiente e o correto funcionamento do pipeline.

### 1. Clonar o Repositório
```Bash
git clone [https://github.com/marcoaurelioramos/Modulo_1_Projeto-Avaliativo.git](https://github.com/marcoaurelioramos/Modulo_1_Projeto-Avaliativo.git)
cd Modulo_1_Projeto-Avaliativo
```

### 2. Criar e Ativar o Ambiente Virtual (venv)
O uso da venv garante que as dependências do projeto não conflitem com outras bibliotecas instaladas no sistema global da máquina.

No Windows:

```Bash
python -m venv venv
.\venv\Scripts\activate
```


No Linux/macOS:

```Bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar as Dependências
Com o ambiente virtual ativo, instale os pacotes necessários utilizando o `requirements.txt`:

```Bash
pip install -r requirements.txt
```


### 4. Configurar as Variáveis de Ambiente (`.env`)
1. Copie o arquivo `.env.example` e renomeie a cópia para `.env`.
2. Abra o arquivo `.env` e preencha as credenciais de acesso ao seu PostgreSQL local, além do `DRIVE_FILE_ID` com o ID do arquivo de dados no Google Drive utilizado no projeto.

### 5. Executar o Pipeline
Siga rigorosamente a ordem sequencial de execução:

1. Abra seu cliente PostgreSQL e execute o script:

```Bash
psql -U seu_usuario -f 0_criar_banco.sql
```

2. Execute o script de extração:

```Bash
python 1_extrair.py
```

3. Execute o script de transformação:

```Bash
python 2_transformar.py
```

4. Abra o arquivo `3_analise.ipynb` no VS Code (certifique-se de selecionar o Kernel do seu ambiente virtual `venv`) e execute as células para processar a camada Gold e visualizar as respostas de negócio.


### Principais Insights Obtidos (Camada Gold)
- Padrões de Gasto: Identificação dos órgãos que representam o maior impacto orçamentário em diárias e passagens.

- Logística Operacional: Mapeamento do modal de transporte e das UFs de destino mais frequentes na administração pública.

- Análise de Eficiência: Relação entre a duração das viagens e o custo total médio envolvido por tipo de pagamento.

Elaborado por `Marco Aurélio Olinger Ramos` - 2026.
