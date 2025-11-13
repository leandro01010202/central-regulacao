from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.repositories import pedidos as pedidos_repo
from app.services.agendamento_service import registrar_tentativa
from app.utils.decorators import roles_required
from . import scheduling_bp


# ==========================================================
# 📋 Página principal de agendamento (com filtros)
# ==========================================================
@scheduling_bp.route("/<tipo>")
@login_required
def lista(tipo: str):
    """Página principal de agendamento (municipal/estadual) com filtros."""
    if tipo not in ("municipal", "estadual"):
        abort(404)

    # Verificação de permissão
    papel_necessario = "agendador_municipal" if tipo == "municipal" else "agendador_estadual"
    if current_user.role not in (papel_necessario, "admin"):
        abort(403)

    # --------------------------
    # 🔹 Captura dos filtros GET
    # --------------------------
    ano = request.args.get("ano", type=int)
    mes = request.args.get("mes", type=int)
    prioridade = request.args.get("prioridade", type=str)


    # --------------------------
    # 🔹 Obtenção de dados filtrados
    # --------------------------
    pedidos = pedidos_repo.listar_para_agendador(tipo, ano=ano, mes=mes, prioridade=prioridade)

    # --------------------------
    # 🔹 Dados auxiliares para os selects
    # --------------------------
    ano_atual = datetime.now().year
    anos_disponiveis = [ano_atual - 2, ano_atual - 1, ano_atual, ano_atual + 1]

    meses = [
        (1, "Janeiro"), (2, "Fevereiro"), (3, "Março"), (4, "Abril"),
        (5, "Maio"), (6, "Junho"), (7, "Julho"), (8, "Agosto"),
        (9, "Setembro"), (10, "Outubro"), (11, "Novembro"), (12, "Dezembro"),
    ]

    # --------------------------
    # 🔹 Renderização
    # --------------------------
    template = f"scheduling/{tipo}.html"
    return render_template(
        template,
        pedidos=pedidos,
        tipo=tipo,
        anos_disponiveis=anos_disponiveis,
        meses=meses,
        ano_selecionado=ano,
        mes_selecionado=mes,
        prioridade_selecionada=prioridade
    )


# ==========================================================
# 🧾 Registrar tentativa de agendamento
# ==========================================================
@scheduling_bp.route("/<tipo>/pedidos/<int:pedido_id>/tentativa", methods=["POST"])
@login_required
def registrar(tipo: str, pedido_id: int):
    """Registra uma tentativa de contato/agendamento."""
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

    # --------------------------
    # 🔹 Validação de dados
    # --------------------------
    if resultado not in ("contato_sucesso", "sem_contato", "recado", "outra"):
        flash("Selecione um resultado válido para a tentativa.", "danger")
        return redirect(url_for("scheduling.lista", tipo=tipo))

    if resultado == "contato_sucesso":
        if not data_exame_final or not horario_final or not local_exame:
            flash("Informe data, horário e local do exame para contato com sucesso.", "danger")
            return redirect(url_for("scheduling.lista", tipo=tipo))

    # --------------------------
    # 🔹 Registro no serviço
    # --------------------------
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
        flash("Tentativa registrada com sucesso.", "success")
    except ValueError as exc:
        flash(str(exc), "danger")

    return redirect(url_for("scheduling.lista", tipo=tipo))
