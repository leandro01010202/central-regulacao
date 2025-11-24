from datetime import datetime
from typing import Optional

from app.domain.status import StatusPedido
from app.extensions import mysql
from app.repositories import pedidos as pedidos_repo


def registrar_historico(pedido_id: int, status: StatusPedido, descricao: Optional[str], usuario_id: int):
    query = """
        INSERT INTO historico_pedidos (pedido_id, status, descricao, criado_por, criado_em)
        VALUES (%s, %s, %s, %s, NOW())
    """
    with mysql.get_cursor() as (_, cursor):
        cursor.execute(
            query,
            (pedido_id, status.value, descricao, usuario_id),  # ✅ REMOVIDO datetime.utcnow()
        )


def atualizar_status(
    pedido_id: int,
    status: StatusPedido,
    usuario_id: int,
    descricao: Optional[str] = None,
    extra_campos: Optional[dict] = None,
):
    campos = {
        "status": status.value,
        "usuario_atualizacao": usuario_id,
        "pendente_recepcao": 0,
    }
    if extra_campos:
        campos.update(extra_campos)
    pedidos_repo.atualizar_campos(pedido_id, campos)
    registrar_historico(pedido_id, status, descricao, usuario_id)

# ==========================================================
# 📥 Serviço que registra a retirada (antes da impressão)
# ==========================================================
def registrar_retirada_service(pedido_id: int, nome_retirante: str, cpf_retirante: str, usuario_id: int):
    print(">>> REPO LOADED FROM:", pedidos_repo.__file__)
    """
    Registra no pedido quem retirou (nome, cpf e timestamp).
    Não altera o status do pedido — apenas armazena os dados.
    """
    pedidos_repo.registrar_retirada(pedido_id, nome_retirante, cpf_retirante, usuario_id)


# ==========================================================
# ✅ Serviço para confirmar entrega (após impressão/confirm)
# ==========================================================
def confirmar_entrega_service(pedido_id: int, usuario_id: int, descricao: Optional[str] = None):
    """
    Marca o pedido como 'retirado', define data_entrega/entregue_por_usuario,
    e registra histórico.
    """
    from app.domain.status import StatusPedido

    query = """
        UPDATE pedidos
        SET 
            entrega_confirmada = 1,
            entregue_por_usuario = %s,
            data_entrega = NOW(),
            status = %s,
            data_atualizacao = NOW()
        WHERE id = %s
    """
    with mysql.get_cursor() as (_, cursor):
        cursor.execute(query, (usuario_id, StatusPedido.RETIRADO.value, pedido_id))

    # Registrar no histórico
    registrar_historico(
        pedido_id,
        StatusPedido.RETIRADO,
        descricao or "Pedido retirado e confirmado pela recepção.",
        usuario_id
    )
