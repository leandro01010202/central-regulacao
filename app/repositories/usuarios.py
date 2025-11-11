from __future__ import annotations

from typing import Any, Optional

from app.extensions import mysql


def _sanitizar_cpf(cpf: Optional[str]) -> str:
    return "".join(filter(str.isdigit, cpf or ""))


def listar_todos(incluir_inativos: bool = True) -> list[dict]:
    query = """
        SELECT u.*, un.nome AS unidade_nome
        FROM usuarios u
        LEFT JOIN unidades_saude un ON un.id = u.unidade_id
    """
    params: list[Any] = []
    if not incluir_inativos:
        query += " WHERE u.ativo = 1"
    query += " ORDER BY u.nome ASC"

    with mysql.get_cursor() as (_, cursor):
        cursor.execute(query, tuple(params))
        return cursor.fetchall()


def obter_por_cpf(
    cpf: str,
    *,
    incluir_inativos: bool = True,
    ignorar_usuario_id: Optional[int] = None,
) -> Optional[dict]:
    cpf_sanitized = _sanitizar_cpf(cpf)

    query = """
        SELECT u.*, un.nome AS unidade_nome
        FROM usuarios u
        LEFT JOIN unidades_saude un ON un.id = u.unidade_id
        WHERE u.cpf = %s
    """
    params: list[Any] = [cpf_sanitized]

    if not incluir_inativos:
        query += " AND u.ativo = 1"

    if ignorar_usuario_id is not None:
        query += " AND u.id <> %s"
        params.append(ignorar_usuario_id)

    with mysql.get_cursor() as (_, cursor):
        cursor.execute(query, tuple(params))
        return cursor.fetchone()


def obter_por_id(usuario_id: int) -> Optional[dict]:
    query = """
        SELECT u.*, un.nome AS unidade_nome
        FROM usuarios u
        LEFT JOIN unidades_saude un ON un.id = u.unidade_id
        WHERE u.id = %s
    """
    with mysql.get_cursor() as (_, cursor):
        cursor.execute(query, (usuario_id,))
        return cursor.fetchone()


def criar_usuario(
    nome: str,
    cpf: str,
    senha_hash: str,
    role: str,
    unidade_id: Optional[int] = None,
    ativo: int = 1,
) -> int:
    query = """
        INSERT INTO usuarios (nome, cpf, senha_hash, role, unidade_id, ativo)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    cpf_sanitized = _sanitizar_cpf(cpf)

    with mysql.get_cursor() as (_, cursor):
        cursor.execute(query, (nome, cpf_sanitized, senha_hash, role, unidade_id, ativo))
        return cursor.lastrowid


def atualizar_usuario(usuario_id: int, **campos: Any) -> None:
    if not campos:
        return

    campos_normalizados: dict[str, Any] = {}

    for chave, valor in campos.items():
        if chave == "cpf":
            campos_normalizados[chave] = _sanitizar_cpf(valor)
        else:
            campos_normalizados[chave] = valor

    colunas = [f"{coluna} = %s" for coluna in campos_normalizados.keys()]
    valores = list(campos_normalizados.values())

    query = f"UPDATE usuarios SET {', '.join(colunas)} WHERE id = %s"
    valores.append(usuario_id)

    with mysql.get_cursor() as (_, cursor):
        cursor.execute(query, tuple(valores))