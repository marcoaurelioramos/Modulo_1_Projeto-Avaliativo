"""
2_transformar.py
-------------------
Fase 2: Lê os dados brutos da camada RAW, realiza a limpeza, a conversão 
de tipos (datas, decimais) e insere ordenadamente na camada SILVER.
"""

from datetime import datetime
from config import POSTGRES_CONFIG
from banco import conectar


def limpar_decimal(valor_texto):
       #Converte o formato decimal brasileiro ('1.272,97') para float do Python.
    if not valor_texto or valor_texto.strip() in ("", "Sem informação", "null", "None"):
        return 0.00
    try:
        # Remove pontos de milhar e substitui a vírgula decimal por ponto
        texto_limpo = valor_texto.strip().replace(".", "").replace(",", ".")
        return float(texto_limpo)
    except ValueError:
        return 0.00


def limpar_data(data_texto):
       #Converte datas de DD/MM/AAAA para YYYY-MM-DD.
    if not data_texto or data_texto.strip() in ("", "Sem informação", "null", "None"):
        return None
    try:
        return datetime.strptime(data_texto.strip(), "%d/%m/%Y").date()
    except ValueError:
        try:
            # Caso a string já esteja no formato correto
            return datetime.strptime(data_texto.strip(), "%Y-%m-%d").date()
        except ValueError:
            return None


def transformar_viagens(conexao):
       #Processa a tabela raw_viagem e insere dados na tabela silver_viagem.
    print(" Transformando dados: raw_viagem silver_viagem...")
    
    cursor_ler = conexao.cursor()
    cursor_inserir = conexao.cursor()
    
    # 1. Limpa a tabela destino (CASCADE limpa os dependentes se necessário)
    cursor_inserir.execute("TRUNCATE TABLE silver_viagem CASCADE;")
    
    # 2. Busca os dados brutos da camada RAW (Sem acentuação nas colunas)
    cursor_ler.execute("""
        SELECT 
            identificador_do_processo_de_viagem, numero_da_proposta_pcdp, situacao, 
            viagem_urgente, codigo_do_orgao_superior, nome_do_orgao_superior, 
            nome, cargo, periodo_data_de_inicio, periodo_data_de_fim, destinos, motivo, 
            valor_diarias, valor_passagens, valor_devolucao, valor_outros_gastos
        FROM raw_viagem
    """)
    
    linhas_insercao = []
    
    for linha in cursor_ler.fetchall():
        id_viagem = linha[0]
        num_proposta = linha[1]
        situacao = linha[2]
        
        # --- HIGIENIZAÇÃO E BLINDAGEM CONTRA ESTOURO VARCHAR(5) ---
        valor_bruto = str(linha[3]).strip().title() if linha[3] else "Não"
        viagem_urgente = valor_bruto[:5]
        cod_orgao_superior = linha[4]
        nome_orgao_superior = linha[5] if linha[5] else "Sem Informação" # NOT NULL
        nome_viajante = linha[6]
        cargo = linha[7]
        
        # Conversão de datas
        dt_inicio = limpar_data(linha[8])
        dt_fim = limpar_data(linha[9])
        
        destinos = linha[10]
        motivo = linha[11]
        
        # Conversão de decimais
        v_diarias = max(0.00, limpar_decimal(linha[12])) # CHECK (valor_diarias >= 0)
        v_passagens = limpar_decimal(linha[13])
        v_devolucao = limpar_decimal(linha[14])
        v_outros = limpar_decimal(linha[15])
        
        # Colunas Calculadas
        v_total = v_diarias + v_passagens + v_outros - v_devolucao
        
        duracao = 0
        if dt_inicio and dt_fim:
            duracao = (dt_fim - dt_inicio).days
            if duracao < 0: 
                duracao = 0
        
        linhas_insercao.append((
            id_viagem, num_proposta, situacao, viagem_urgente, cod_orgao_superior,
            nome_orgao_superior, nome_viajante, cargo, dt_inicio, dt_fim, destinos,
            motivo, v_diarias, v_passagens, v_devolucao, v_outros, v_total, duracao
        ))
        
    sql_insert = """
        INSERT INTO silver_viagem (
            id_viagem, num_proposta, situacao, viagem_urgente, cod_orgao_superior,
            nome_orgao_superior, nome_viajante, cargo, data_inicio, data_fim, destinos,
            motivo, valor_diarias, valor_passagens, valor_devolucao, valor_outros_gastos,
            valor_total, duracao_dias
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    cursor_inserir.executemany(sql_insert, linhas_insercao)
    conexao.commit()
    print(f" Sucesso! {len(linhas_insercao)} registros migrados para silver_viagem.")


def transformar_pagamentos(conexao):
         # Processa a tabela raw_pagamento e insere dados na tabela silver_pagamento.
    print(" Transformando dados: raw_pagamento silver_pagamento...")
    
    cursor_ler = conexao.cursor()
    cursor_inserir = conexao.cursor()
    
    cursor_inserir.execute("TRUNCATE TABLE silver_pagamento CASCADE;")
    
    # Valida integridade referencial com a tabela silver_viagem (Sem acentuação)
    cursor_ler.execute("""
        SELECT p.identificador_do_processo_de_viagem, p.numero_da_proposta_pcdp, 
               p.nome_do_orgao_pagador, p.codigo_da_unidade_gestora_pagadora, p.tipo_de_pagamento, p.valor
        FROM raw_pagamento p
        WHERE EXISTS (SELECT 1 FROM silver_viagem v WHERE v.id_viagem = p.identificador_do_processo_de_viagem)
    """)
    
    linhas_insercao = []
    for linha in cursor_ler.fetchall():
        tipo_pagto = linha[4] if linha[4] else "Sem Informação" # NOT NULL
        valor = max(0.00, limpar_decimal(linha[5]))             # CHECK (valor >= 0)
        
        linhas_insercao.append((linha[0], linha[1], linha[2], linha[3], tipo_pagto, valor))
        
    sql_insert = """
        INSERT INTO silver_pagamento (
            id_viagem, num_proposta, nome_orgao_pagador, nome_ug_pagadora, tipo_pagamento, valor
        ) VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor_inserir.executemany(sql_insert, linhas_insercao)
    conexao.commit()
    print(f" Sucesso! {len(linhas_insercao)} registros migrados para silver_pagamento.")


def transformar_passagens(conexao):
       #Processa a tabela raw_passagem e insere dados na tabela silver_passagem.
    print(" Transformando dados: raw_passagem silver_passagem...")
    
    cursor_ler = conexao.cursor()
    cursor_inserir = conexao.cursor()
    
    cursor_inserir.execute("TRUNCATE TABLE silver_passagem CASCADE;")
    
    # Valida integridade referencial com a tabela silver_viagem
    cursor_ler.execute("""
        SELECT p.identificador_do_processo_de_viagem, p.meio_de_transporte, 
               p.pais_origem_ida, p.uf_origem_ida, p.cidade_origem_ida, 
               p.pais_destino_ida, p.uf_destino_ida, p.cidade_destino_ida, 
               p.valor_da_passagem, p.taxa_de_servico, p.data_emissao_compra
        FROM raw_passagem p
        WHERE EXISTS (SELECT 1 FROM silver_viagem v WHERE v.id_viagem = p.identificador_do_processo_de_viagem)
    """)
    
    linhas_insercao = []
    for linha in cursor_ler.fetchall():
        v_passagem = max(0.00, limpar_decimal(linha[8]))  # CHECK (valor_passagem >= 0)
        t_servico = max(0.00, limpar_decimal(linha[9]))   # CHECK (taxa_servico >= 0)
        dt_emissao = limpar_data(linha[10])
        
        linhas_insercao.append((
            linha[0], linha[1], linha[2], linha[3], linha[4], 
            linha[5], linha[6], linha[7], v_passagem, t_servico, dt_emissao
        ))
        
    sql_insert = """
        INSERT INTO silver_passagem (
            id_viagem, meio_transporte, pais_origem_ida, uf_origem_ida, cidade_origem_ida,
            pais_destino_ida, uf_destino_ida, cidade_destino_ida, valor_passagem, taxa_servico, data_emissao
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor_inserir.executemany(sql_insert, linhas_insercao)
    conexao.commit()
    print(f" Sucesso! {len(linhas_insercao)} registros migrados para silver_passagem.")


def transformar_trechos(conexao):
       # Processa a tabela raw_trecho e insere dados na tabela silver_trecho.
    print(" Transformando dados: raw_trecho silver_trecho...")
    
    cursor_ler = conexao.cursor()
    cursor_inserir = conexao.cursor()
    
    cursor_inserir.execute("TRUNCATE TABLE silver_trecho CASCADE;")
    
    # Valida integridade referencial com a tabela silver_viagem (Sem acentuação)
    cursor_ler.execute("""
        SELECT t.identificador_do_processo_de_viagem, t.sequencia_trecho, 
               t.origem_data, t.origem_uf, t.origem_cidade, 
               t.destino_data, t.destino_uf, t.destino_cidade, 
               t.meio_de_transporte, t.numero_diarias
        FROM raw_trecho t
        WHERE EXISTS (SELECT 1 FROM silver_viagem v WHERE v.id_viagem = t.identificador_do_processo_de_viagem)
    """)
    
    # Evita violação da constraint UNIQUE em (id_viagem, sequencia_trecho)
    chaves_processadas = set()
    linhas_insercao = []
    
    for linha in cursor_ler.fetchall():
        id_viagem = linha[0]
        try:
            seq_trecho = int(float(linha[1])) if linha[1] else 1
        except (ValueError, TypeError):
            continue
            
        chave_composta = (id_viagem, seq_trecho)
        if chave_composta in chaves_processadas:
            continue
            
        chaves_processadas.add(chave_composta)
        
        dt_origem = limpar_data(linha[2])
        dt_destino = limpar_data(linha[5])
        n_diarias = max(0.00, limpar_decimal(linha[9])) # CHECK (numero_diarias >= 0)
        
        linhas_insercao.append((
            id_viagem, seq_trecho, dt_origem, linha[3], linha[4],
            dt_destino, linha[6], linha[7], linha[8], n_diarias
        ))
        
    sql_insert = """
        INSERT INTO silver_trecho (
            id_viagem, sequencia_trecho, origem_data, origem_uf, origem_cidade,
            destino_data, destino_uf, destino_cidade, meio_transporte, numero_diarias
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor_inserir.executemany(sql_insert, linhas_insercao)
    conexao.commit()
    print(f" Sucesso! {len(linhas_insercao)} registros migrados para silver_trecho.")


def main():
    print(" Conectando ao PostgreSQL para a Fase 2...")
    conexao = conectar()
    
    try:
        transformar_viagens(conexao)
        transformar_pagamentos(conexao)
        transformar_passagens(conexao)
        transformar_trechos(conexao)
        print("\n FASE 2 CONCLUÍDA: Dados inseridos e Camada Silver e higienizada com sucesso!")
        
    except Exception as erro:
        conexao.rollback()
        print(f"\n Erro durante o pipeline de transformação: {erro}")
        raise
    finally:
        if conexao and not conexao.closed:
            conexao.close()
            print(" Conexão encerrada com segurança.")


if __name__ == "__main__":
    main()