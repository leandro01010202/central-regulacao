from flask import render_template, request, redirect, url_for, flash, abort, session
from flask_login import login_required, current_user

from app.domain.status import StatusPedido
from app.repositories import pedidos as pedidos_repo
from app.services.pedidos_service import atualizar_status
from app.utils.decorators import roles_required
from . import regulator_bp


@regulator_bp.route("/definir-preferencia-tipo", methods=["POST"])
@login_required
@roles_required("medico_regulador", "malote", "admin")
def definir_preferencia_tipo():
    """Define a preferência do usuário para tipo de regulação"""
    tipo = request.form.get("tipo_preferido", "")
    
    if tipo in ["municipal", "estadual"]:
        session['tipo_regulacao_preferido'] = tipo
        flash(f"Preferência definida para {'municipal' if tipo == 'municipal' else 'cross/estadual'}.", "success")
    else:
        flash("Tipo de regulação inválido.", "error")
    
    # Redirecionar de volta para o painel
    return redirect(url_for("regulator.painel"))


@regulator_bp.route("/painel")
@login_required
@roles_required("medico_regulador", "malote", "admin")
def painel():
    # Obter tipo de regulação da query string ou da session
    tipo_param = request.args.get("tipo", None)
    
    # Se foi fornecido um tipo na URL, salvar na session e usar
    if tipo_param in ["municipal", "estadual"]:
        session['tipo_regulacao_preferido'] = tipo_param
        tipo = tipo_param
    else:
        # Se não foi fornecido, usar a preferência salva na session ou padrão
        tipo = session.get('tipo_regulacao_preferido', 'municipal')
    
    # Obter parâmetros de filtro da query string
    unidade = request.args.get('unidade', '').strip()
    categoria = request.args.get('categoria', '').strip()
    cpf = request.args.get('cpf', '').strip()
    nome = request.args.get('nome', '').strip()
    
    # Buscar pedidos do tipo especificado
    pedidos = pedidos_repo.listar_para_medico(tipo)
    
    # Filtrar pedidos se houver parâmetros
    if unidade or categoria or cpf or nome:
        pedidos_filtrados = []
        
        for pedido in pedidos:
            incluir = True
            
            # Filtro por unidade
            if unidade and unidade.lower() not in pedido.get('unidade_nome', '').lower():
                incluir = False
                
            # Filtro por categoria (tipo_solicitacao)
            if categoria and pedido.get('tipo_solicitacao') != categoria:
                incluir = False
                
            # Filtro por CPF
            if cpf:
                cpf_limpo = ''.join(filter(str.isdigit, cpf))
                pedido_cpf_limpo = ''.join(filter(str.isdigit, pedido.get('paciente_cpf', '')))
                if cpf_limpo not in pedido_cpf_limpo:
                    incluir = False
                    
            # Filtro por nome
            if nome and nome.lower() not in pedido.get('paciente_nome', '').lower():
                incluir = False
                
            if incluir:
                pedidos_filtrados.append(pedido)
                
        pedidos = pedidos_filtrados
    
    # Obter lista de unidades para o dropdown (apenas do tipo atual)
    todos_pedidos_tipo = pedidos_repo.listar_para_medico(tipo)
    unidades_disponiveis = sorted(list(set(p.get('unidade_nome', '') for p in todos_pedidos_tipo if p.get('unidade_nome'))))
    
    # Preparar dados para o template
    return render_template(
        "regulator/painel.html", 
        pedidos=pedidos, 
        tipo=tipo,
        preferencia_tipo=session.get('tipo_regulacao_preferido', 'municipal'),
        filtros={
            'unidade': unidade,
            'categoria': categoria,
            'cpf': cpf,
            'nome': nome
        },
        unidades_disponiveis=unidades_disponiveis
    )


@regulator_bp.route("/pedidos/<int:pedido_id>/aprovar", methods=["POST"])
@login_required
@roles_required("medico_regulador", "malote", "admin")
def aprovar(pedido_id: int):
    tipo_regulacao = request.form.get("tipo_regulacao")
    
    # Obter filtros ativos para manter na navegação após ação
    filtros_ativos = {
        'unidade': request.form.get('filtro_unidade', ''),
        'categoria': request.form.get('filtro_categoria', ''),
        'cpf': request.form.get('filtro_cpf', ''),
        'nome': request.form.get('filtro_nome', '')
    }
    
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
    
    # Redirecionar mantendo filtros e tipo
    params = [f"tipo={tipo_regulacao}"]
    for key, value in filtros_ativos.items():
        if value:
            params.append(f"{key}={value}")
    
    redirect_url = url_for("regulator.painel") + "?" + "&".join(params)
    return redirect(redirect_url)


@regulator_bp.route("/pedidos/<int:pedido_id>/cancelar", methods=["POST"])
@login_required
@roles_required("medico_regulador", "malote", "admin")
def cancelar(pedido_id: int):
    motivo = request.form.get("motivo", "").strip()
    tipo_regulacao = request.form.get("tipo_regulacao", "municipal")
    
    # Obter filtros ativos para manter na navegação após ação
    filtros_ativos = {
        'unidade': request.form.get('filtro_unidade', ''),
        'categoria': request.form.get('filtro_categoria', ''),
        'cpf': request.form.get('filtro_cpf', ''),
        'nome': request.form.get('filtro_nome', '')
    }
    
    if not motivo:
        flash("Informe o motivo do cancelamento.", "danger")
        # Redirecionar mantendo filtros
        params = [f"tipo={tipo_regulacao}"]
        for key, value in filtros_ativos.items():
            if value:
                params.append(f"{key}={value}")
        redirect_url = url_for("regulator.painel") + "?" + "&".join(params)
        return redirect(redirect_url)

    atualizar_status(
        pedido_id=pedido_id,
        status=StatusPedido.CANCELADO_MEDICO,
        usuario_id=current_user.id,
        descricao=f"Cancelado pelo médico regulador. Motivo: {motivo}",
        extra_campos={"motivo_cancelamento": motivo},
    )
    
    flash("Pedido cancelado.", "info")
    
    # Redirecionar mantendo filtros e tipo
    params = [f"tipo={tipo_regulacao}"]
    for key, value in filtros_ativos.items():
        if value:
            params.append(f"{key}={value}")
    
    redirect_url = url_for("regulator.painel") + "?" + "&".join(params)
    return redirect(redirect_url)


@regulator_bp.route("/pedidos/<int:pedido_id>/devolver", methods=["POST"])
@login_required
@roles_required("medico_regulador", "malote", "admin")
def devolver(pedido_id: int):
    motivo = request.form.get("motivo", "").strip()
    tipo_regulacao = request.form.get("tipo_regulacao", "municipal")
    
    # Obter filtros ativos para manter na navegação após ação
    filtros_ativos = {
        'unidade': request.form.get('filtro_unidade', ''),
        'categoria': request.form.get('filtro_categoria', ''),
        'cpf': request.form.get('filtro_cpf', ''),
        'nome': request.form.get('filtro_nome', '')
    }
    
    if not motivo:
        flash("Informe o motivo da devolução.", "danger")
        # Redirecionar mantendo filtros
        params = [f"tipo={tipo_regulacao}"]
        for key, value in filtros_ativos.items():
            if value:
                params.append(f"{key}={value}")
        redirect_url = url_for("regulator.painel") + "?" + "&".join(params)
        return redirect(redirect_url)

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
    
    # Redirecionar mantendo filtros e tipo
    params = [f"tipo={tipo_regulacao}"]
    for key, value in filtros_ativos.items():
        if value:
            params.append(f"{key}={value}")
    
    redirect_url = url_for("regulator.painel") + "?" + "&".join(params)
    return redirect(redirect_url)


@regulator_bp.route("/painel/limpar-filtros")
@login_required
@roles_required("medico_regulador", "malote", "admin")
def limpar_filtros():
    """Rota para limpar filtros e voltar à lista completa"""
    tipo = request.args.get("tipo", "municipal")
    return redirect(url_for("regulator.painel", tipo=tipo))