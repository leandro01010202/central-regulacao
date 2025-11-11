from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.domain.status import StatusPedido
from app.repositories import pedidos as pedidos_repo
from app.services.pedidos_service import atualizar_status
from app.utils.decorators import roles_required
from . import malote_bp


@malote_bp.route("/pedidos")
@login_required
@roles_required("malote", "admin")
def listar():
    pedidos = pedidos_repo.listar_para_malote()
    return render_template("malote/list.html", pedidos=pedidos)


@malote_bp.route("/pedidos/<int:pedido_id>/classificar", methods=["POST"])
@login_required
@roles_required("malote", "admin")
def classificar(pedido_id: int):
    tipo_regulacao = request.form.get("tipo_regulacao")
    prioridade = request.form.get("prioridade")
    if tipo_regulacao not in ("municipal", "estadual") or prioridade not in ("P1", "P2"):
        flash("Selecione tipo de regulação e prioridade válidos.", "danger")
        return redirect(url_for("malote.listar"))

    status_destino = (
        StatusPedido.AGUARDANDO_ANALISE_MEDICO_MUNICIPAL
        if tipo_regulacao == "municipal"
        else StatusPedido.AGUARDANDO_ANALISE_MEDICO_ESTADUAL
    )

    atualizar_status(
        pedido_id=pedido_id,
        status=status_destino,
        usuario_id=current_user.id,
        descricao=f"Pedido encaminhado ao médico regulador ({tipo_regulacao.upper()}) com prioridade {prioridade}.",
        extra_campos={
            "tipo_regulacao": tipo_regulacao,
            "prioridade": prioridade,
            "pendente_recepcao": 0,
        },
    )
    flash("Pedido encaminhado ao médico regulador.", "success")
    return redirect(url_for("malote.listar"))