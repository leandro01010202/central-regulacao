from typing import Optional

from app.extensions import mysql


def obter_por_id(paciente_id: int) -> Optional[dict]:
    query = "SELECT * FROM pacientes WHERE id = %s"
    with mysql.get_cursor() as (_, cursor):
        cursor.execute(query, (paciente_id,))
        return cursor.fetchone()


def obter_por_cpf(cpf: str) -> Optional[dict]:
    cpf_sanitized = "".join(filter(str.isdigit, cpf or ""))
    query = "SELECT * FROM pacientes WHERE cpf = %s"
    with mysql.get_cursor() as (_, cursor):
        cursor.execute(query, (cpf_sanitized,))
        return cursor.fetchone()


def criar_paciente(dados: dict) -> int:
    query = """
        INSERT INTO pacientes
        (nome, cpf, data_nascimento, telefone_principal, telefone_secundario,
         email, cartao_sus, endereco, unidade_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    valores = (
        dados["nome"],
        "".join(filter(str.isdigit, dados["cpf"])),
        dados.get("data_nascimento"),
        dados.get("telefone_principal"),
        dados.get("telefone_secundario"),
        dados.get("email"),
        dados.get("cartao_sus"),
        dados.get("endereco"),
        dados.get("unidade_id"),
    )
    with mysql.get_cursor() as (_, cursor):
        cursor.execute(query, valores)
        return cursor.lastrowid


def atualizar_paciente(paciente_id: int, dados: dict):
    query = """
        UPDATE pacientes
        SET nome=%s,
            data_nascimento=%s,
            telefone_principal=%s,
            telefone_secundario=%s,
            email=%s,
            cartao_sus=%s,
            endereco=%s,
            unidade_id=%s
        WHERE id=%s
    """
    valores = (
        dados["nome"],
        dados.get("data_nascimento"),
        dados.get("telefone_principal"),
        dados.get("telefone_secundario"),
        dados.get("email"),
        dados.get("cartao_sus"),
        dados.get("endereco"),
        dados.get("unidade_id"),
        paciente_id,
    )
    with mysql.get_cursor() as (_, cursor):
        cursor.execute(query, valores)