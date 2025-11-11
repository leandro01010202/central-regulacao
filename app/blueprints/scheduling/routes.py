from datetime import datetime

from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.repositories import pedidos as pedidos_repo
from app.services.agendamento_service import registrar_tentativa
from app.utils.decorators import roles_required
from . import scheduling_bp


@scheduling_bp.route("/<tipo>")
@login_required
def lista(tipo: str):
    if tipo not in ("municipal", "estadual"):
        abort(404)

    papel_necessario = "agendador_municipal" if tipo == "municipal" else "agendador_estadual"
    if current_user.role not in (papel_necessario, "admin"):
        abort(403)

    pedidos = pedidos_repo.listar_para_agendador(tipo)
    template = f"scheduling/{tipo}.html"
    return render_template(template, pedidos=pedidos, tipo=tipo)


@scheduling_bp.route("/<tipo>/pedidos/<int:pedido_id>/tentativa", methods=["POST"])
@login_required
def registrar(tipo: str, pedido_id: int):
    if tipo not in ("municipal", "estadual"):
        abort(404)
    papel_necessario = "agendador_municipal" if tipo == "municipal" else "agendador_estadual"
    if current_user.role not in (papel_necessario, "admin"):
        abort(403)

    resultado = request.form.get("resultado")
    resumo = request.form.get("resumo", "").strip()

    data_exame = request.form.get("data_exame")
    horario_exame = request.form.get("horario_exame")
    local_exame = request.form.get("local_exame")

    data_exame_final = datetime.strptime(data_exame, "%Y-%m-%d").date() if data_exame else None
    horario_final = datetime.strptime(horario_exame, "%H:%M").time() if horario_exame else None

    if resultado not in ("contato_sucesso", "sem_contato", "recado", "outra"):
        flash("Selecione um resultado válido para a tentativa.", "danger")
        return redirect(url_for("scheduling.lista", tipo=tipo))

    if resultado == "contato_sucesso":
        if not data_exame_final or not horario_final or not local_exame:
            flash("Informe data, horário e local do exame para contato com sucesso.", "danger")
            return redirect(url_for("scheduling.lista", tipo=tipo))

    try:
        registrar_tentativa(
            pedido_id=pedido_id,
            usuario_id=current_user.id,
            resultado=resultado,
            resumo=resumo,
            data_exame=data_exame_final,
            horario_exame=horario_final,
            local_exame=local_exame,
        )
        flash("Tentativa registrada.", "success")
    except ValueError as exc:
        flash(str(exc), "danger")

    return redirect(url_for("scheduling.lista", tipo=tipo))