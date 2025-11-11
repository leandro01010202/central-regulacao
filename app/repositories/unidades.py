from typing import Any, Dict, List, Optional

from app.extensions import mysql


def _obter_conexao():
    """
    Obtém uma nova conexão com o banco de dados MySQL a partir da extensão configurada.
    """
    return mysql.get_connection()


def listar_todas() -> List[Dict[str, Any]]:
    """
    Retorna todas as unidades cadastradas, ordenadas alfabeticamente.
    """
    conexao = _obter_conexao()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT
            id,
            nome,
            codigo,
            telefone,
            endereco,
            ativo
        FROM unidades_saude
        ORDER BY nome
        """
    )
    unidades = cursor.fetchall()
    cursor.close()
    conexao.close()
    return unidades


def listar_unidades_ativas() -> List[Dict[str, Any]]:
    """
    Retorna apenas as unidades com flag ativo = 1.
    """
    conexao = _obter_conexao()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT
            id,
            nome,
            codigo,
            telefone,
            endereco,
            ativo
        FROM unidades_saude
        WHERE ativo = 1
        ORDER BY nome
        """
    )
    unidades = cursor.fetchall()
    cursor.close()
    conexao.close()
    return unidades


def criar_unidade(
    nome: str,
    ativa: bool,
    codigo: Optional[str] = None,
    telefone: Optional[str] = None,
    endereco: Optional[str] = None,
) -> int:
    """
    Cria uma nova unidade e retorna o ID gerado.
    """
    conexao = _obter_conexao()
    cursor = conexao.cursor()
    cursor.execute(
        """
        INSERT INTO unidades_saude (
            nome,
            codigo,
            telefone,
            endereco,
            ativo
        )
        VALUES (%s, %s, %s, %s, %s)
        """,
        (nome, codigo, telefone, endereco, int(ativa)),
    )
    conexao.commit()
    novo_id = cursor.lastrowid
    cursor.close()
    conexao.close()
    return novo_id


def obter_por_id(unidade_id: int) -> Optional[Dict[str, Any]]:
    """
    Recupera uma unidade pelo ID.
    """
    conexao = _obter_conexao()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT
            id,
            nome,
            codigo,
            telefone,
            endereco,
            ativo
        FROM unidades_saude
        WHERE id = %s
        """,
        (unidade_id,),
    )
    unidade = cursor.fetchone()
    cursor.close()
    conexao.close()
    return unidade


def atualizar_unidade(
    unidade_id: int,
    nome: str,
    ativa: bool,
    codigo: Optional[str] = None,
    telefone: Optional[str] = None,
    endereco: Optional[str] = None,
) -> None:
    """
    Atualiza os dados de uma unidade existente.
    """
    conexao = _obter_conexao()
    cursor = conexao.cursor()
    cursor.execute(
        """
        UPDATE unidades_saude
        SET
            nome = %s,
            codigo = %s,
            telefone = %s,
            endereco = %s,
            ativo = %s
        WHERE id = %s
        """,
        (nome, codigo, telefone, endereco, int(ativa), unidade_id),
    )
    conexao.commit()
    cursor.close()
    conexao.close()


def definir_status(unidade_id: int, ativa: bool) -> None:
    """
    Atualiza apenas o status (ativo/inativo) de uma unidade.
    """
    conexao = _obter_conexao()
    cursor = conexao.cursor()
    cursor.execute(
        """
        UPDATE unidades_saude
        SET ativo = %s
        WHERE id = %s
        """,
        (int(ativa), unidade_id),
    )
    conexao.commit()
    cursor.close()
    conexao.close()