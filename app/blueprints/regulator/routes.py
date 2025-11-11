from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.domain.status import StatusPedido
from app.repositories import pedidos as pedidos_repo
from app.services.pedidos_service import atualizar_status
from app.utils.decorators import roles_required
from . import regulator_bp


@regulator_bp.route("/painel")
@login_required
@roles_required("medico_regulador", "malote", "admin")
def painel():
    tipo = request.args.get("tipo", "municipal")
    pedidos = pedidos_repo.listar_para_medico(tipo)
    return render_template("regulator/painel.html", pedidos=pedidos, tipo=tipo)


@regulator_bp.route("/pedidos/<int:pedido_id>/aprovar", methods=["POST"])
@login_required
@roles_required("medico_regulador", "malote", "admin")
def aprovar(pedido_id: int):
    tipo_regulacao = request.form.get("tipo_regulacao")
    if tipo_regulacao not in ("municipal", "estadual"):
        abort(400)

    status_destino = (
        StatusPedido.APROVADO_MUNICIPAL if tipo_regulacao == "municipal" else StatusPedido.APROVADO_ESTADUAL
    )
    atualizar_status(
        pedido_id=pedido_id,
        status=status_destino,
        usuario_id=current_user.id,
        descricao="Pedido aprovado pelo médico regulador.",
        extra_campos={"pendente_recepcao": 0},
    )
    flash("Pedido aprovado e encaminhado aos agendadores.", "success")
    return redirect(url_for("regulator.painel", tipo=tipo_regulacao))


@regulator_bp.route("/pedidos/<int:pedido_id>/cancelar", methods=["POST"])
@login_required
@roles_required("medico_regulador", "malote", "admin")
def cancelar(pedido_id: int):
    motivo = request.form.get("motivo", "").strip()
    if not motivo:
        flash("Informe o motivo do cancelamento.", "danger")
        return redirect(request.referrer or url_for("regulator.painel"))

    atualizar_status(
        pedido_id=pedido_id,
        status=StatusPedido.CANCELADO_MEDICO,
        usuario_id=current_user.id,
        descricao=f"Cancelado pelo médico regulador. Motivo: {motivo}",
        extra_campos={"motivo_cancelamento": motivo},
    )
    flash("Pedido cancelado.", "info")
    return redirect(request.referrer or url_for("regulator.painel"))


@regulator_bp.route("/pedidos/<int:pedido_id>/devolver", methods=["POST"])
@login_required
@roles_required("medico_regulador", "malote", "admin")
def devolver(pedido_id: int):
    motivo = request.form.get("motivo", "").strip()
    if not motivo:
        flash("Informe o motivo da devolução.", "danger")
        return redirect(request.referrer or url_for("regulator.painel"))

    atualizar_status(
        pedido_id=pedido_id,
        status=StatusPedido.DEVOLVIDO_PELO_MEDICO,
        usuario_id=current_user.id,
        descricao=f"Pedido devolvido para a recepção. Motivo: {motivo}",
        extra_campos={
            "pendente_recepcao": 1,
            "motivo_devolucao": motivo,
            "tipo_regulacao": None,
            "prioridade": None,
        },
    )
    flash("Pedido devolvido à recepção da unidade.", "warning")
    return redirect(request.referrer or url_for("regulator.painel"))