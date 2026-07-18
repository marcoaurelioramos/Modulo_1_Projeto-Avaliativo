
-- ============================================================================
-- Criação do Banco de Dados.
-- executar este script no PostgreSQL para criar o banco de dados e as tabelas.
-- ============================================================================

CREATE DATABASE transparencia;


-- ==========================================================================================
-- Após criar o banco de dados, conecte-se a ele e execute os scripts de criação das tabelas.
-- ==========================================================================================


-- ============================================================================
-- 1. CAMADA RAW (Dados Brutos - Todos os campos VARCHAR, sem contraints)
-- ============================================================================


-- Tabela Raw Viagens
DROP TABLE IF EXISTS raw_viagem CASCADE;
CREATE TABLE raw_viagem (
    Identificador_do_processo_de_viagem VARCHAR,
    numero_da_proposta_PCDP VARCHAR,
    situacao VARCHAR,
    justificativa_urgencia_viagem VARCHAR,
    viagem_urgente VARCHAR,
    codigo_do_orgao_superior VARCHAR,
    nome_do_orgao_superior VARCHAR,
    codigo_orgao_solicitante VARCHAR,
    nome_orgao_solicitante VARCHAR,
    cpf_viajante VARCHAR,
    nome VARCHAR,
    cargo VARCHAR,
    funcao VARCHAR,
    descricao_funcao VARCHAR,
    periodo_data_de_inicio VARCHAR,
    periodo_data_de_fim VARCHAR,
    destinos VARCHAR,
    motivo VARCHAR,
    valor_diarias VARCHAR,
    valor_passagens VARCHAR,
    valor_outros_gastos VARCHAR,
    valor_devolucao VARCHAR
);

-- Tabela Raw Passagem
DROP TABLE IF EXISTS raw_passagem CASCADE;
CREATE TABLE raw_passagem (
    Identificador_do_processo_de_viagem VARCHAR,
    numero_da_proposta_PCDP VARCHAR,
    meio_de_transporte VARCHAR,
    pais_origem_ida VARCHAR,
    uf_origem_ida VARCHAR,
    cidade_origem_ida VARCHAR,
    pais_destino_ida VARCHAR,
    uf_destino_ida VARCHAR,
    cidade_destino_ida VARCHAR,
    pais_origem_volta VARCHAR,
    uf_origem_volta VARCHAR,
    cidade_origem_volta VARCHAR,
    pais_destino_volta VARCHAR,
    uf_destino_volta VARCHAR,
    cidade_destino_volta VARCHAR,
    valor_da_passagem VARCHAR,
    taxa_de_servico VARCHAR,
    data_emissao_compra VARCHAR,
    hora_da_emissao_compra VARCHAR
    
);

-- Tabela Raw Pagamento
DROP TABLE IF EXISTS raw_pagamento CASCADE;
CREATE TABLE raw_pagamento (
    Identificador_do_processo_de_viagem VARCHAR,
    numero_da_proposta_pcdp VARCHAR,
    codigo_orgao_superior VARCHAR,
    nome_do_orgao_superior VARCHAR,
    codigo_orgao_pagador VARCHAR,
    nome_do_orgao_pagador VARCHAR,
    codigo_da_unidade_gestora_pagadora VARCHAR,
    nome_da_unidade_gestora_pagadora VARCHAR,
    tipo_de_pagamento VARCHAR,
    valor VARCHAR
    
);

-- Tabela Raw Trecho
DROP TABLE IF EXISTS raw_trecho CASCADE;
CREATE TABLE raw_trecho (
    identificador_do_processo_de_viagem VARCHAR,
    numero_da_proposta_pcdp VARCHAR,
    sequencia_trecho VARCHAR,
    origem_data VARCHAR,
    origem_pais VARCHAR,
    origem_uf VARCHAR,
    origem_cidade VARCHAR,
    destino_data VARCHAR,
    destino_pais VARCHAR,
    destino_uf VARCHAR,
    destino_cidade VARCHAR,
    meio_de_transporte VARCHAR,
    numero_diarias VARCHAR,
    missao VARCHAR

);


-- ============================================================================
-- 2. CAMADA SILVER (Dados Tipados, Tratados, Chaves PK/FK e Constraints Inline)
-- ============================================================================

-- Tabela Silver Viagem
DROP TABLE IF EXISTS silver_viagem CASCADE;
CREATE TABLE silver_viagem (
    id_viagem VARCHAR(20) NOT NULL PRIMARY KEY,
    num_proposta VARCHAR(20),
    situacao VARCHAR(50),
    viagem_urgente VARCHAR(5),
    cod_orgao_superior VARCHAR(20),
    nome_orgao_superior VARCHAR(255) NOT NULL,
    nome_viajante VARCHAR(255),
    cargo VARCHAR(255),
    data_inicio DATE,
    data_fim DATE,
    destinos VARCHAR(4000),
    motivo VARCHAR(4000),
    valor_diarias DECIMAL(10,2) CHECK (valor_diarias >= 0),
    valor_passagens DECIMAL(10,2),
    valor_devolucao DECIMAL(10,2),
    valor_outros_gastos DECIMAL(10,2),
    valor_total DECIMAL(12,2),
    duracao_dias INT
);

-- Tabela Silver Passagem
DROP TABLE IF EXISTS silver_passagem CASCADE;
CREATE TABLE silver_passagem (
    id_passagem SERIAL PRIMARY KEY,
    id_viagem VARCHAR(20) NOT NULL REFERENCES silver_viagem(id_viagem),
    meio_transporte VARCHAR(50),
    pais_origem_ida VARCHAR(60),
    uf_origem_ida VARCHAR(40),
    cidade_origem_ida VARCHAR(80),
    pais_destino_ida VARCHAR(60),
    uf_destino_ida VARCHAR(40),
    cidade_destino_ida VARCHAR(80),
    valor_passagem DECIMAL(10,2) CHECK (valor_passagem >= 0),
    taxa_servico DECIMAL(10,2) CHECK (taxa_servico >= 0),
    data_emissao DATE
);

-- Tabela Silver Pagamento
DROP TABLE IF EXISTS silver_pagamento CASCADE;
CREATE TABLE silver_pagamento (
    id_pagamento SERIAL PRIMARY KEY,
    id_viagem VARCHAR(20) NOT NULL REFERENCES silver_viagem(id_viagem),
    num_proposta VARCHAR(20),
    nome_orgao_pagador VARCHAR(255),
    nome_ug_pagadora VARCHAR(255),
    tipo_pagamento VARCHAR(50) NOT NULL,
    valor DECIMAL(10,2) CHECK (valor >= 0)
);


-- Tabela Silver Trecho
DROP TABLE IF EXISTS silver_trecho CASCADE;
CREATE TABLE silver_trecho (
    id_trecho SERIAL PRIMARY KEY,
    id_viagem VARCHAR(20) NOT NULL REFERENCES silver_viagem(id_viagem),
    sequencia_trecho INT,
    origem_data DATE,
    origem_uf VARCHAR(40),
    origem_cidade VARCHAR(80),
    destino_data DATE,
    destino_uf VARCHAR(40),
    destino_cidade VARCHAR(80),
    meio_transporte VARCHAR(50),
    numero_diarias DECIMAL(10,2) CHECK (numero_diarias >= 0)
);