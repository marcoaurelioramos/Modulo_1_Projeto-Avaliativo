"""
1_extrair_.py
--------------
Importante:
As tabelas Raw precisam ter a mesma quantidade e a mesma ordem de colunas
dos CSVs, pois o INSERT é feito por posição.
"""

import zipfile
from pathlib import Path

import pandas as pd
import requests

from banco import conectar, inserir_em_lote
from config import (
    ARQUIVOS,
    CSV_ENCODING,
    CSV_SEPARADOR,
    DRIVE_FILE_ID,
    PASTA_DADOS,
    TAMANHO_BLOCO,
)


def baixar_arquivo_drive(file_id, destino_zip):
    """Baixa o arquivo ZIP do Google Drive para a pasta data."""

    PASTA_DADOS.mkdir(parents=True, exist_ok=True)

    if destino_zip.exists():
        print(f"Arquivo ZIP já existe em: {destino_zip}")
        return

    print("Baixando arquivo ZIP do Google Drive...")

    url = "https://docs.google.com/uc?export=download"

    with requests.Session() as sessao:
        resposta = sessao.get(
            url,
            params={"id": file_id},
            stream=True,
            timeout=60,
        )

        resposta.raise_for_status()

        token = None
        for chave, valor in resposta.cookies.items():
            if chave.startswith("download_warning"):
                token = valor
                break

        if token:
            resposta = sessao.get(
                url,
                params={"id": file_id, "confirm": token},
                stream=True,
                timeout=60,
            )
            resposta.raise_for_status()

        with open(destino_zip, "wb") as arquivo:
            for pedaco in resposta.iter_content(chunk_size=8192):
                if pedaco:
                    arquivo.write(pedaco)

    print(f"Download concluído: {destino_zip}")


def executar_sql(conexao, comando_sql):
    """Executa um comando SQL simples."""

    cursor = conexao.cursor()
    cursor.execute(comando_sql)
    conexao.commit()
    cursor.close()


def localizar_csv_no_zip(zip_aberto, nome_csv):
    """
    A função usa Path(arquivo).name porque o CSV pode estar dentro
    de uma pasta interna no ZIP.
    """

    for arquivo in zip_aberto.namelist():
        if Path(arquivo).name.lower() == nome_csv.lower():
            return arquivo

    return None


def carregar_csv(conexao, zip_aberto, nome_csv, tabela_raw):
    """Lê um CSV dentro do ZIP e carrega na tabela Raw correspondente."""

    arquivo_csv = localizar_csv_no_zip(zip_aberto, nome_csv)

    if arquivo_csv is None:
        print(f"Aviso: o arquivo {nome_csv} não foi encontrado no ZIP.")
        return

    print(f"\nProcessando {nome_csv} -> {tabela_raw}")

    # Limpa a tabela antes de carregar novamente.
    executar_sql(conexao, f"TRUNCATE TABLE {tabela_raw};")

    total_linhas = 0

    with zip_aberto.open(arquivo_csv) as arquivo:
        pedacos = pd.read_csv(
            arquivo,
            sep=CSV_SEPARADOR,
            encoding=CSV_ENCODING,
            dtype=str,
            keep_default_na=False,
            chunksize=TAMANHO_BLOCO,
        )

        for pedaco in pedacos:
            # Um marcador %s para cada coluna do CSV.
            marcadores = ", ".join(["%s"] * len(pedaco.columns))

            comando_insert = f"INSERT INTO {tabela_raw} VALUES ({marcadores})"

            linhas = [tuple(linha) for linha in pedaco.to_numpy()]

            inserir_em_lote(conexao, comando_insert, linhas)

            total_linhas += len(linhas)

            print(
                f"Lote enviado: {len(linhas)} linhas "
                f"(total acumulado: {total_linhas})"
            )

    print(f"Tabela {tabela_raw} carregada com {total_linhas} registros.")


def processar_zip(caminho_zip):
    """Abre o ZIP e carrega os 4 CSVs nas tabelas Raw."""

    print("\nConectando ao PostgreSQL...")
    conexao = conectar()
    print("Conexão realizada com sucesso.")

    try:
        with zipfile.ZipFile(caminho_zip, "r") as zip_aberto:
            print("Arquivos encontrados no ZIP:")
            for arquivo in zip_aberto.namelist():
                print(f"- {arquivo}")

            for info_arquivo in ARQUIVOS.values():
                carregar_csv(
                    conexao=conexao,
                    zip_aberto=zip_aberto,
                    nome_csv=info_arquivo["csv"],
                    tabela_raw=info_arquivo["tabela_raw"],
                )

        print("\nFase 1 concluída: Tabelas Raw carregadas com sucesso.")

    except Exception:
        conexao.rollback()
        raise

    finally:
        if conexao is not None and not conexao.closed:
            conexao.close()
            print("Conexão com o PostgreSQL encerrada.")


def main():
    """Executa a Fase 1: download + carga Raw."""

    caminho_zip = PASTA_DADOS / "viagens_2025_6meses.zip"

    try:
        baixar_arquivo_drive(DRIVE_FILE_ID, caminho_zip)
        processar_zip(caminho_zip)

    except Exception as erro:
        print(f"\nO pipeline falhou devido ao seguinte erro: {erro}")
        raise

if __name__ == "__main__":
    main()
