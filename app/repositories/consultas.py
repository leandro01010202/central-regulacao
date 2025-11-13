from typing import List, Optional
from app.extensions import mysql  # usa o mesmo banco de exames


def listar_para_agendador_consultas(
    tipo_regulacao: str,
    ano: Optional[int] = None,
    mes: Optional[int] = None,
    prioridade: Optional[str] = None
) -> List[dict]:
    """
    Lista consultas disponíveis para agendamento (usando o mesmo banco de exames)
    """
    if tipo_regulacao not in ("municipal", "estadual"):
        return []

    status_validos = ("APROVADO", "AGENDAMENTO_EM_ANDAMENTO")

    query = """
        SELECT 
            c.id,
            c.status,
            c.tentativas_contato,
            c.data_consulta,
            c.horario_consulta,
            c.local_consulta,
            c.prioridade,
            p.nome AS paciente_nome,
            p.cpf AS paciente_cpf,
            p.telefone_principal,
            c.especialidade
        FROM consultas c
        JOIN pacientes p ON p.id = c.paciente_id
        WHERE c.status IN (%s, %s)
          AND c.tipo_regulacao = %s
    """
    params = [status_validos[0], status_validos[1], tipo_regulacao]

    # Filtros opcionais
    if ano:
        query += " AND YEAR(c.data_consulta) = %s"
        params.append(ano)
    if mes:
        query += " AND MONTH(c.data_consulta) = %s"
        params.append(mes)
    if prioridade:
        query += " AND c.prioridade = %s"
        params.append(prioridade)

    query += " ORDER BY c.prioridade ASC, c.data_consulta DESC"

    with mysql.get_cursor(dictionary=True) as (_, cursor):
        cursor.execute(query, tuple(params))
        return cursor.fetchall()
