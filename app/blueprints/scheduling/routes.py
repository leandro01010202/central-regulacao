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

    if tipo not in ("municipal", "estadual"):
        abort(404)

    papel_necessario = "agendador_municipal" if tipo == "municipal" else "agendador_estadual"
    if current_user.role not in (papel_necessario, "admin"):
        abort(403)

    # Filtros
    ano = request.args.get("ano", type=int)
    mes = request.args.get("mes", type=int)
    prioridade = request.args.get("prioridade", type=str)
    nome = request.args.get("nome", type=str)
    exame_q = request.args.get("exame", type=str)
    cpf = request.args.get("cpf", type=str)

    # Buscar todos os pedidos do tipo
    pedidos = pedidos_repo.listar_para_agendador(
        tipo,
        ano=ano,
        mes=mes,
        prioridade=prioridade
    )

    # Filtrar por nome/cpf se fornecidos
    if nome or cpf:
        pedidos_filtrados = []
        nome_lower = nome.lower() if nome else None
        cpf_digits = ''.join(filter(str.isdigit, cpf)) if cpf else None
        for p in pedidos:
            incluir = True
            if nome_lower:
                paciente_nome = (p.get('paciente_nome') or '').lower()
                if nome_lower not in paciente_nome:
                    incluir = False
            if cpf_digits and incluir:
                pedido_cpf = ''.join(filter(str.isdigit, (p.get('paciente_cpf') or '')))
                if cpf_digits not in pedido_cpf:
                    incluir = False
            if incluir:
                pedidos_filtrados.append(p)
        pedidos = pedidos_filtrados

    # Filtrar por nome do exame se fornecido (filtro adicional)
    if exame_q:
        exame_lower = exame_q.lower()
        pedidos = [p for p in pedidos if exame_lower in ((p.get('exame_nome') or p.get('nome_solicitacao') or '').lower())]

    # 🔥 SEPARAÇÃO FINAL
    exames = [p for p in pedidos if p.get("exame_id")]
    consultas = [p for p in pedidos if p.get("consulta_id")]

    # Agrupar exames por nome e por mês/ano, contando prioridades (P1/P2)
    dados = {}
    for p in exames:
        exame_nome = p.get('exame_nome') or p.get('nome_solicitacao') or 'Sem Exame'
        data_solicitacao = p.get('data_solicitacao')

        # normalizar label mês/ano (MM/YYYY)
        mes_label = 'Sem data'
        if data_solicitacao:
            try:
                # pode ser date/datetime ou string 'YYYY-MM-DD'
                if hasattr(data_solicitacao, 'month') and hasattr(data_solicitacao, 'year'):
                    mes_label = f"{data_solicitacao.month:02d}/{data_solicitacao.year}"
                else:
                    parts = str(data_solicitacao).split('-')
                    if len(parts) >= 2:
                        mes_label = f"{int(parts[1]):02d}/{parts[0]}"
                    else:
                        mes_label = str(data_solicitacao)
            except Exception:
                mes_label = str(data_solicitacao)

        dados.setdefault(exame_nome, {})
        dados[exame_nome].setdefault(mes_label, {'P1': 0, 'P2': 0})
        prioridade_pedido = (p.get('prioridade') or '').upper()
        if prioridade_pedido == 'P1':
            dados[exame_nome][mes_label]['P1'] += 1
        elif prioridade_pedido == 'P2':
            dados[exame_nome][mes_label]['P2'] += 1

    # Gerar lista ordenada de meses (MM/YYYY) do menor ano/mês para o maior
    meses_set = set()
    for exame_nome, meses_map in dados.items():
        for mes_label in meses_map.keys():
            meses_set.add(mes_label)

    def _parse_label(label: str):
        try:
            if '/' in label:
                m, y = label.split('/')
                return int(y), int(m)
        except Exception:
            pass
        return (9999, 99)

    meses_ordenados = sorted(list(meses_set), key=lambda l: _parse_label(l))

    # Anos / meses
    ano_atual = datetime.now().year
    anos_disponiveis = [ano_atual - 2, ano_atual - 1, ano_atual, ano_atual + 1]

    meses = [
        (1, "Janeiro"), (2, "Fevereiro"), (3, "Março"), (4, "Abril"),
        (5, "Maio"), (6, "Junho"), (7, "Julho"), (8, "Agosto"),
        (9, "Setembro"), (10, "Outubro"), (11, "Novembro"), (12, "Dezembro"),
    ]

    # ==========================================================
    # PAGINAÇÃO
    # ==========================================================
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    # importantíssimo: manter filtros nos links
    def url_with_params(page_number):
        return url_for(
            "scheduling.lista",
            tipo=tipo,
            page=page_number,
            per_page=per_page,
            ano=ano,
            mes=mes,
            prioridade=prioridade,
            nome=nome,
            cpf=cpf,
            exame=exame_q,
        )

    # aplicar paginação separada para exames e consultas
    total_exames = len(exames)
    total_consultas = len(consultas)

    start = (page - 1) * per_page
    end = start + per_page

    exames_page = exames[start:end]
    consultas_page = consultas[start:end]

    total_paginas = max(
        (total_exames + per_page - 1) // per_page,
        (total_consultas + per_page - 1) // per_page,
    )


    template = f"scheduling/{tipo}.html"
    return render_template(
        template,

        # Listas paginadas
        exames=exames_page,
        consultas=consultas_page,

        # Dados originais
        pedidos=pedidos,
        dados=dados,
        exame_selecionado=exame_q,
        meses_ordenados=meses_ordenados,
        tipo=tipo,
        anos_disponiveis=anos_disponiveis,
        meses=meses,
        ano_selecionado=ano,
        mes_selecionado=mes,
        prioridade_selecionada=prioridade,
        nome_selecionado=nome,
        cpf_selecionado=cpf,
        tipo_agendador=current_user.tipo_agendador,

        # 🔹 Variáveis da paginação
        page=page,
        per_page=per_page,
        total_paginas=total_paginas,
        make_page_url=url_with_params,
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
