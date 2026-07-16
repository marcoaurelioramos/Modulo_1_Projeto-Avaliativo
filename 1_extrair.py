"""
1_extrair.py
-------------------
Faz o download do arquivo ZIP do Google Drive, extrai e insere os dados 
em lotes diretamente nas tabelas RAW correspondentes do PostgreSQL.
"""

import io
import zipfile
import sys
from pathlib import Path
import requests
import pandas as pd


PASTA_RAIZ_DETECTADA = Path(__file__).resolve().parent

import builtins
builtins.PASTA_RAIZ = PASTA_RAIZ_DETECTADA
# --------------------------------------------------------------------


from config import PASTA_DADOS, DRIVE_FILE_ID, ARQUIVOS, CSV_SEPARADOR, CSV_ENCODING, TAMANHO_BLOCO
from banco import conectar, inserir_em_lote


def baixar_arquivo_drive(file_id, destino_zip):
    """Baixa o arquivo do Google Drive usando o ID público."""
    print(f" Conectando ao Google Drive para baixar o arquivo ZIP (ID: {file_id})...")
    
    # URL de exportação direta do Google Drive para arquivos públicos
    url = f"https://docs.google.com/uc?export=download&id={file_id}&confirm=t"
    
    # Criar a pasta de dados se não existir
    PASTA_DADOS.mkdir(parents=True, exist_ok=True)
    
    with requests.Session() as session:
        resposta = session.get(url, stream=True, timeout=60)
        resposta.raise_for_status()
        
        # Salva o arquivo temporariamente na pasta configurada
        with open(destino_zip, "wb") as f:
            for chunk in resposta.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    
    print(f" Download concluído! Arquivo salvo em: {destino_zip}")


def processar_e_carregar_zip(destino_zip):
    """Abre o ZIP e carrega cada arquivo CSV mapeado nas tabelas do PostgreSQL."""
    print(" Conectando ao banco de dados...")
    conexao = conectar()
    
    try:
        with zipfile.ZipFile(destino_zip, "r") as z:
            arquivos_no_zip = z.namelist()
            print(f" Arquivos identificados dentro do ZIP: {arquivos_no_zip}")
            
            for chave_tipo, info in ARQUIVOS.items():
                csv_nome = info["csv"]
                tabela_destino = info["tabela_raw"]
                
                # Valida se o arquivo de configuração de fato bate com o nome dentro do ZIP
                arquivo_alvo = next((f for f in arquivos_no_zip if f.lower() == csv_nome.lower()), None)
                
                if not arquivo_alvo:
                    print(f" Aviso: Arquivo esperado '{csv_nome}' não foi encontrado dentro do ZIP. Pulando...")
                    continue
                
                print(f"\n Processando '{arquivo_alvo}' -> Tabela '{tabela_destino}'")
                
                with z.open(arquivo_alvo) as f:
                    lotes_pandas = pd.read_csv(
                        f,
                        sep=CSV_SEPARADOR,
                        encoding=CSV_ENCODING,
                        dtype=str,          # Garante que dados brutos entrem como texto nas tabelas RAW
                        chunksize=TAMANHO_BLOCO
                    )
                    
                    total_linhas_tabela = 0
                    primeiro_bloco = True
                    sql_insert = ""
                    
                    for bloco in lotes_pandas:
                        # Trata os nomes das colunas vindas do CSV (remove aspas e padroniza minúsculas)
                        bloco.columns = [
                            col.strip().lower()
                            .replace(' ', '_')
                            .replace('"', '')
                            .replace(';', '')
                            .replace('(', '')
                            .replace(')', '')
                            .replace('-', '')
                            for col in bloco.columns
                        ]
                        
                        # Cria dinamicamente a query de INSERT no primeiro bloco mapeado
                        if primeiro_bloco:
                            colunas = ", ".join(bloco.columns)
                            valores_placeholders = ", ".join(["%s"] * len(bloco.columns))
                            sql_insert = f"INSERT INTO {tabela_destino} ({colunas}) VALUES ({valores_placeholders})"
                            primeiro_bloco = False
                        
                        # Substitui valores NaN/Nulos do Pandas por None do Python (vira NULL no SQL)
                        bloco = bloco.where(pd.notnull(bloco), None)
                        
                        # Converte o bloco do DataFrame em uma lista de tuplas para a inserção em lote
                        linhas_tuplas = [tuple(x) for x in bloco.to_numpy()]
                        
                        inserir_em_lote(conexao, sql_insert, linhas_tuplas)
                        
                        total_linhas_tabela += len(linhas_tuplas)
                        print(f" Lote enviado: +{len(linhas_tuplas)} linhas inseridas... (Total acumulado: {total_linhas_tabela})")
                        
                print(f" Sucesso total! Tabela '{tabela_destino}' completamente carregada com {total_linhas_tabela} registros.")
                
    finally:
        conexao.close()
        print("\n Conexão com o banco de dados encerrada de forma segura.")


if __name__ == "__main__":
    caminho_zip_final = PASTA_DADOS / "viagens_2025_6meses.zip"
    
    try:
        #baixar_arquivo_drive(DRIVE_FILE_ID, caminho_zip_final)
        processar_e_carregar_zip(caminho_zip_final)
        print("\n FASE 1 CONCLUÍDA: Todos os dados foram ingeridos com sucesso nas tabelas RAW!")
    except Exception as erro:
        print(f"\n O pipeline falhou devido ao seguinte erro: {erro}")