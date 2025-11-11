from typing import Optional, Sequence

from app.extensions import mysql


def listar_todos() -> Sequence[dict]:
    query = """
        SELECT
            id,
            nome
        FROM exames
        ORDER BY nome
    """
    with mysql.get_cursor() as (_, cursor):
        cursor.execute(query)
        return cursor.fetchall()


def listar_exames() -> Sequence[dict]:
    """
    Mantém compatibilidade com chamadas antigas.
    """
    return listar_todos()


def obter_por_id(exame_id: int) -> Optional[dict]:
    query = """
        SELECT
            id,
            nome
        FROM exames
        WHERE id = %s
        LIMIT 1
    """
    with mysql.get_cursor() as (_, cursor):
        cursor.execute(query, (exame_id,))
        return cursor.fetchone()


def criar_exame(nome: str) -> None:
    query = """
        INSERT INTO exames (nome)
        VALUES (%s)
    """
    with mysql.get_cursor() as (conn, cursor):
        cursor.execute(query, (nome,))
        conn.commit()


def atualizar_exame(exame_id: int, nome: str) -> None:
    query = """
        UPDATE exames
        SET nome = %s
        WHERE id = %s
    """
    with mysql.get_cursor() as (conn, cursor):
        cursor.execute(query, (nome, exame_id))
        conn.commit()