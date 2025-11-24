from flask import redirect, url_for, render_template
from flask_login import current_user, login_required
from app.extensions import mysql
from datetime import datetime, timedelta

# Importa as utilidades de data em português
from app.utils.data_portugues import data_utils

from . import dashboards_bp


def _get_dashboard_stats():
    """Busca estatísticas gerais do sistema"""
    with mysql.get_cursor(dictionary=True) as (_, cursor):
        stats = {}
        
        # Estatísticas básicas de pedidos
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN tipo_solicitacao = 'exame' THEN 1 END) as total_exames,
                COUNT(CASE WHEN tipo_solicitacao = 'consulta' THEN 1 END) as total_consultas,
                COUNT(CASE WHEN status LIKE '%AGUARDANDO%' THEN 1 END) as aguardando,
                COUNT(CASE WHEN status LIKE '%AGENDADO%' THEN 1 END) as agendados,
                COUNT(CASE WHEN status LIKE '%CANCELADO%' THEN 1 END) as cancelados,
                COUNT(CASE WHEN prioridade = 'P1' THEN 1 END) as prioridade_alta,
                COUNT(CASE WHEN DATE(data_solicitacao) = CURDATE() THEN 1 END) as hoje,
                AVG(TIMESTAMPDIFF(HOUR, data_solicitacao, data_atualizacao)) as tempo_medio_horas
            FROM pedidos
        """)
        stats['pedidos'] = cursor.fetchone()
        
        # Taxa de resolução
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN status LIKE '%AGENDADO%' THEN 1 END) as finalizados,
                COUNT(*) as total,
                ROUND((COUNT(CASE WHEN status LIKE '%AGENDADO%' THEN 1 END) / COUNT(*)) * 100, 1) as taxa_resolucao
            FROM pedidos
            WHERE data_solicitacao >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """)
        stats['performance'] = cursor.fetchone()
        
        # Pedidos críticos (>7 dias parados)
        cursor.execute("""
            SELECT COUNT(*) as pedidos_criticos
            FROM pedidos
            WHERE TIMESTAMPDIFF(DAY, data_atualizacao, NOW()) > 7
            AND status NOT LIKE '%AGENDADO%'
            AND status NOT LIKE '%CANCELADO%'
        """)
        stats['criticos'] = cursor.fetchone()
        
        # Usuários e atividade online
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN is_online = 1 THEN 1 END) as online,
                COUNT(CASE WHEN ativo = 1 THEN 1 END) as ativos,
                AVG(TIMESTAMPDIFF(HOUR, last_seen, NOW())) as tempo_medio_offline
            FROM usuarios
        """)
        stats['usuarios'] = cursor.fetchone()
        
        # Unidades por atividade
        cursor.execute("""
            SELECT 
                u.nome as unidade,
                COUNT(p.id) as total_pedidos,
                COUNT(CASE WHEN p.status LIKE '%AGUARDANDO%' THEN 1 END) as pendentes,
                ROUND((COUNT(CASE WHEN p.status LIKE '%AGENDADO%' THEN 1 END) / COUNT(p.id)) * 100, 1) as taxa_sucesso
            FROM unidades_saude u
            LEFT JOIN pedidos p ON u.id = p.unidade_id AND p.data_solicitacao >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            WHERE u.ativo = 1
            GROUP BY u.id, u.nome
            ORDER BY total_pedidos DESC
            LIMIT 10
        """)
        stats['unidades'] = cursor.fetchall()
        
        # Atividade por dia
        cursor.execute("""
            SELECT 
                DATE(data_solicitacao) as data,
                COUNT(*) as total,
                COUNT(CASE WHEN tipo_solicitacao = 'exame' THEN 1 END) as exames,
                COUNT(CASE WHEN tipo_solicitacao = 'consulta' THEN 1 END) as consultas,
                COUNT(CASE WHEN prioridade = 'P1' THEN 1 END) as urgentes
            FROM pedidos
            WHERE data_solicitacao >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            GROUP BY DATE(data_solicitacao)
            ORDER BY data DESC
        """)
        stats['atividade'] = cursor.fetchall()
        
        # Chat avançado
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT c.id) as total_conversas,
                COUNT(m.id) as total_mensagens,
                COUNT(CASE WHEN DATE(m.created_at) = CURDATE() THEN 1 END) as mensagens_hoje,
                COUNT(DISTINCT a.id) as total_anexos,
                ROUND(SUM(a.size) / 1024 / 1024, 2) as mb_anexos
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
            LEFT JOIN attachments a ON a.message_id = m.id
        """)
        stats['chat'] = cursor.fetchone()
        
        return stats


def _get_advanced_analytics():
    """Análises avançadas do sistema"""
    with mysql.get_cursor(dictionary=True) as (_, cursor):
        analytics = {}
        
        # Picos de atividade por hora
        cursor.execute("""
            SELECT 
                HOUR(data_solicitacao) as hora,
                COUNT(*) as total
            FROM pedidos
            WHERE data_solicitacao >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY HOUR(data_solicitacao)
            ORDER BY total DESC
            LIMIT 1
        """)
        pico = cursor.fetchone()
        analytics['pico_atividade'] = f"{pico['hora']}:00" if pico else "N/A"
        
        # Especialidade mais solicitada
        cursor.execute("""
            SELECT c.especialidade, COUNT(*) as total
            FROM pedidos p
            JOIN consultas c ON c.id = p.consulta_id
            WHERE p.data_solicitacao >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY c.especialidade
            ORDER BY total DESC
            LIMIT 1
        """)
        especialidade = cursor.fetchone()
        analytics['top_especialidade'] = especialidade['especialidade'] if especialidade else "N/A"
        
        # Exame mais solicitado
        cursor.execute("""
            SELECT e.nome, COUNT(*) as total
            FROM pedidos p
            JOIN exames e ON e.id = p.exame_id
            WHERE p.data_solicitacao >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY e.nome
            ORDER BY total DESC
            LIMIT 1
        """)
        exame = cursor.fetchone()
        analytics['top_exame'] = exame['nome'] if exame else "N/A"
        
        # Eficiência de contato
        cursor.execute("""
            SELECT 
                ROUND((COUNT(CASE WHEN resultado = 'contato_sucesso' THEN 1 END) / COUNT(*)) * 100, 1) as taxa_sucesso_contato
            FROM tentativas_contato
            WHERE data_tentativa >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """)
        contato = cursor.fetchone()
        analytics['eficiencia_contato'] = contato['taxa_sucesso_contato'] if contato else 0
        
        # Tendência semanal
        cursor.execute("""
            SELECT 
                DAYNAME(data_solicitacao) as dia,
                COUNT(*) as total
            FROM pedidos
            WHERE data_solicitacao >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY DAYNAME(data_solicitacao), DAYOFWEEK(data_solicitacao)
            ORDER BY total DESC
            LIMIT 1
        """)
        dia_pico = cursor.fetchone()
        analytics['dia_mais_ativo'] = dia_pico['dia'] if dia_pico else "N/A"
        
        return analytics


def _get_system_health():
    """Métricas de saúde do sistema"""
    with mysql.get_cursor(dictionary=True) as (_, cursor):
        health = {}
        
        # Pedidos travados
        cursor.execute("""
            SELECT COUNT(*) as travados
            FROM pedidos
            WHERE TIMESTAMPDIFF(DAY, data_atualizacao, NOW()) > 7
            AND status NOT LIKE '%AGENDADO%'
            AND status NOT LIKE '%CANCELADO%'
        """)
        health['pedidos_travados'] = cursor.fetchone()['travados']
        
        # Usuários inativos
        cursor.execute("""
            SELECT COUNT(*) as inativos
            FROM usuarios
            WHERE TIMESTAMPDIFF(DAY, last_seen, NOW()) > 30
            AND ativo = 1
        """)
        health['usuarios_inativos'] = cursor.fetchone()['inativos']
        
        # Unidades sem atividade
        cursor.execute("""
            SELECT COUNT(*) as silenciosas
            FROM unidades_saude u
            LEFT JOIN pedidos p ON u.id = p.unidade_id 
                AND p.data_solicitacao >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            WHERE u.ativo = 1 AND p.id IS NULL
        """)
        health['unidades_silenciosas'] = cursor.fetchone()['silenciosas']
        
        # Qualidade dos dados
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN observacoes IS NOT NULL AND observacoes != '' THEN 1 END) as com_observacoes,
                COUNT(CASE WHEN local_exame IS NOT NULL AND local_exame != '' THEN 1 END) as com_local
            FROM pedidos
            WHERE data_solicitacao >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """)
        qualidade = cursor.fetchone()
        health['qualidade_dados'] = round((qualidade['com_observacoes'] / qualidade['total']) * 100, 1) if qualidade['total'] else 0
        
        return health


@dashboards_bp.route("/")
@login_required
def home():
    role = current_user.role
    
    # Redirecionamentos
    if role == "recepcao":
        return redirect(url_for("reception.listar_pedidos"))
    if role == "recepcao_regulacao":
        return redirect(url_for("reception.regulacao"))
    if role == "agendador_municipal":
        return redirect(url_for("scheduling.lista", tipo="municipal"))
    if role == "agendador_estadual":
        return redirect(url_for("scheduling.lista", tipo="estadual"))
    
    # Dashboard completo
    stats_gerais = _get_dashboard_stats()
    stats_especificos = _get_role_specific_stats(role)
    analytics = _get_advanced_analytics()
    system_health = _get_system_health()
    
    return render_template(
        "dashboards/home.html", 
        stats=stats_gerais,
        role_stats=stats_especificos,
        analytics=analytics,
        health=system_health,
        user_role=role,
        datetime=data_utils  # 🔄 SUBSTITUI datetime por data_utils para datas em português
    )


def _get_role_specific_stats(role):
    """Estatísticas específicas por perfil"""
    with mysql.get_cursor(dictionary=True) as (_, cursor):
        stats = {}
        
        if role == "admin":
            cursor.execute("""
                SELECT 
                    role,
                    COUNT(*) as total,
                    COUNT(CASE WHEN is_online = 1 THEN 1 END) as online,
                    AVG(TIMESTAMPDIFF(DAY, criado_em, NOW())) as dias_medio_conta
                FROM usuarios
                WHERE ativo = 1
                GROUP BY role
                ORDER BY total DESC
            """)
            stats['usuarios_por_role'] = cursor.fetchall()
            
            # Análise de segurança
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN TIMESTAMPDIFF(DAY, last_seen, NOW()) > 30 THEN 1 END) as contas_abandonadas,
                    COUNT(CASE WHEN unidade_id IS NULL AND role != 'admin' THEN 1 END) as usuarios_sem_unidade
                FROM usuarios
                WHERE ativo = 1
            """)
            stats['seguranca'] = cursor.fetchone()
            
        elif role == "medico_regulador":
            cursor.execute("""
                SELECT 
                    tipo_regulacao,
                    COUNT(*) as total,
                    COUNT(CASE WHEN prioridade = 'P1' THEN 1 END) as urgentes,
                    AVG(TIMESTAMPDIFF(HOUR, data_solicitacao, data_atualizacao)) as tempo_medio_horas
                FROM pedidos
                WHERE status IN ('AGUARDANDO_ANALISE_MEDICO_MUNICIPAL', 'AGUARDANDO_ANALISE_MEDICO_ESTADUAL')
                GROUP BY tipo_regulacao
            """)
            stats['pedidos_regulacao'] = cursor.fetchall()
            
        elif role == "malote":
            cursor.execute("""
                SELECT 
                    u.nome as unidade,
                    COUNT(p.id) as total,
                    COUNT(CASE WHEN p.status = 'DEVOLVIDO_SEM_CONTATO' THEN 1 END) as devolvidos,
                    AVG(TIMESTAMPDIFF(HOUR, p.data_solicitacao, NOW())) as horas_aguardando
                FROM unidades_saude u
                LEFT JOIN pedidos p ON u.id = p.unidade_id 
                    AND p.status IN ('AGUARDANDO_TRIAGEM', 'DEVOLVIDO_SEM_CONTATO')
                WHERE u.ativo = 1
                GROUP BY u.id, u.nome
                HAVING total > 0
                ORDER BY total DESC
            """)
            stats['pedidos_por_unidade'] = cursor.fetchall()
        
        return stats


def _get_advanced_analytics():
    """Análises avançadas e preditivas"""
    with mysql.get_cursor(dictionary=True) as (_, cursor):
        analytics = {}
        
        # Pico de atividade
        cursor.execute("""
            SELECT 
                HOUR(data_solicitacao) as hora,
                COUNT(*) as total
            FROM pedidos
            WHERE data_solicitacao >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY HOUR(data_solicitacao)
            ORDER BY total DESC
            LIMIT 1
        """)
        pico = cursor.fetchone()
        analytics['pico_atividade'] = f"{pico['hora']}:00" if pico and pico['hora'] is not None else "N/A"
        analytics['volume_pico'] = pico['total'] if pico else 0
        
        # Top especialidade/exame
        cursor.execute("""
            SELECT c.especialidade, COUNT(*) as total
            FROM pedidos p
            JOIN consultas c ON c.id = p.consulta_id
            WHERE p.data_solicitacao >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY c.especialidade
            ORDER BY total DESC
            LIMIT 1
        """)
        especialidade = cursor.fetchone()
        analytics['top_especialidade'] = especialidade['especialidade'] if especialidade else "N/A"
        analytics['volume_especialidade'] = especialidade['total'] if especialidade else 0
        
        cursor.execute("""
            SELECT e.nome, COUNT(*) as total
            FROM pedidos p
            JOIN exames e ON e.id = p.exame_id
            WHERE p.data_solicitacao >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY e.nome
            ORDER BY total DESC
            LIMIT 1
        """)
        exame = cursor.fetchone()
        analytics['top_exame'] = exame['nome'] if exame else "N/A"
        analytics['volume_exame'] = exame['total'] if exame else 0
        
        # Eficiência de contato
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN resultado = 'contato_sucesso' THEN 1 END) as sucessos,
                COUNT(*) as total,
                ROUND((COUNT(CASE WHEN resultado = 'contato_sucesso' THEN 1 END) / COUNT(*)) * 100, 1) as taxa_sucesso,
                AVG(tentativa_numero) as tentativas_media
            FROM tentativas_contato
            WHERE data_tentativa >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """)
        contato = cursor.fetchone()
        analytics['eficiencia_contato'] = contato['taxa_sucesso'] if contato else 0
        analytics['tentativas_media'] = round(contato['tentativas_media'], 1) if contato and contato['tentativas_media'] else 0
        
        # Dia mais ativo
        cursor.execute("""
            SELECT 
                DAYNAME(data_solicitacao) as dia,
                COUNT(*) as total
            FROM pedidos
            WHERE data_solicitacao >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY DAYNAME(data_solicitacao), DAYOFWEEK(data_solicitacao)
            ORDER BY total DESC
            LIMIT 1
        """)
        dia_pico = cursor.fetchone()
        analytics['dia_mais_ativo'] = dia_pico['dia'] if dia_pico else "N/A"
        analytics['volume_dia'] = dia_pico['total'] if dia_pico else 0
        
        # Análise temporal
        cursor.execute("""
            SELECT 
                AVG(TIMESTAMPDIFF(HOUR, data_solicitacao, 
                    CASE 
                        WHEN status LIKE '%AGENDADO%' THEN data_atualizacao
                        ELSE NOW()
                    END)) as tempo_medio_resolucao
            FROM pedidos
            WHERE data_solicitacao >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """)
        tempo = cursor.fetchone()
        analytics['tempo_medio_resolucao'] = round(tempo['tempo_medio_resolucao'], 1) if tempo and tempo['tempo_medio_resolucao'] else 0
        
        # Sazonalidade
        cursor.execute("""
            SELECT 
                COUNT(*) as total_mes_atual,
                (SELECT COUNT(*) FROM pedidos 
                 WHERE MONTH(data_solicitacao) = MONTH(DATE_SUB(NOW(), INTERVAL 1 MONTH))
                 AND YEAR(data_solicitacao) = YEAR(DATE_SUB(NOW(), INTERVAL 1 MONTH))) as total_mes_anterior
            FROM pedidos
            WHERE MONTH(data_solicitacao) = MONTH(NOW())
            AND YEAR(data_solicitacao) = YEAR(NOW())
        """)
        sazonalidade = cursor.fetchone()
        if sazonalidade and sazonalidade['total_mes_anterior'] > 0:
            analytics['crescimento_mensal'] = round(((sazonalidade['total_mes_atual'] - sazonalidade['total_mes_anterior']) / sazonalidade['total_mes_anterior']) * 100, 1)
        else:
            analytics['crescimento_mensal'] = 0
            
        return analytics


def _get_system_health():
    """Métricas de saúde do sistema"""
    with mysql.get_cursor(dictionary=True) as (_, cursor):
        health = {}
        
        # Pedidos críticos
        cursor.execute("""
            SELECT 
                COUNT(*) as travados,
                GROUP_CONCAT(CONCAT(p.id, ' (', u.nome, ')') SEPARATOR ', ') as exemplos
            FROM pedidos p
            JOIN unidades_saude u ON u.id = p.unidade_id
            WHERE TIMESTAMPDIFF(DAY, p.data_atualizacao, NOW()) > 7
            AND p.status NOT LIKE '%AGENDADO%'
            AND p.status NOT LIKE '%CANCELADO%'
            LIMIT 5
        """)
        travados = cursor.fetchone()
        health['pedidos_travados'] = travados['travados'] if travados else 0
        health['exemplos_travados'] = travados['exemplos'] if travados else ""
        
        # Usuários inativos
        cursor.execute("""
            SELECT 
                COUNT(*) as inativos,
                GROUP_CONCAT(nome SEPARATOR ', ') as nomes
            FROM usuarios
            WHERE TIMESTAMPDIFF(DAY, last_seen, NOW()) > 30
            AND ativo = 1
            LIMIT 5
        """)
        inativos = cursor.fetchone()
        health['usuarios_inativos'] = inativos['inativos'] if inativos else 0
        health['usuarios_inativos_nomes'] = inativos['nomes'] if inativos else ""
        
        # Unidades silenciosas
        cursor.execute("""
            SELECT COUNT(*) as silenciosas
            FROM unidades_saude u
            LEFT JOIN pedidos p ON u.id = p.unidade_id 
                AND p.data_solicitacao >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            WHERE u.ativo = 1 AND p.id IS NULL
        """)
        health['unidades_silenciosas'] = cursor.fetchone()['silenciosas']
        
        # Integridade dos dados
        cursor.execute("""
            SELECT 
                COUNT(*) as total_pedidos,
                COUNT(CASE WHEN observacoes IS NOT NULL AND observacoes != '' THEN 1 END) as com_observacoes,
                COUNT(CASE WHEN motivo_devolucao IS NOT NULL AND status LIKE '%DEVOLVIDO%' THEN 1 END) as devolucoes_justificadas
            FROM pedidos
            WHERE data_solicitacao >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """)
        qualidade = cursor.fetchone()
        health['qualidade_dados'] = round((qualidade['com_observacoes'] / qualidade['total_pedidos']) * 100, 1) if qualidade['total_pedidos'] else 0
        health['devolucoes_justificadas'] = round((qualidade['devolucoes_justificadas'] / qualidade['total_pedidos']) * 100, 1) if qualidade['total_pedidos'] else 0
        
        # Capacidade do sistema
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN DATE(data_solicitacao) = CURDATE() THEN 1 END) as hoje,
                COUNT(CASE WHEN DATE(data_solicitacao) = DATE_SUB(CURDATE(), INTERVAL 1 DAY) THEN 1 END) as ontem,
                MAX(DATE(data_solicitacao)) as ultima_atividade
            FROM pedidos
        """)
        capacidade = cursor.fetchone()
        health['volume_hoje'] = capacidade['hoje'] if capacidade else 0
        health['volume_ontem'] = capacidade['ontem'] if capacidade else 0
        health['ultima_atividade'] = capacidade['ultima_atividade'] if capacidade else None
        
        return health


@dashboards_bp.route("/relatorios")
@login_required
def relatorios():
    """Página de relatórios detalhados"""
    role = current_user.role
    
    if role not in ["admin", "medico_regulador", "malote"]:
        return redirect(url_for("dashboards.home"))
    
    with mysql.get_cursor(dictionary=True) as (_, cursor):
        relatorios = {}
        
        # Relatórios existentes + novos
        cursor.execute("""
            SELECT 
                DATE_FORMAT(data_solicitacao, '%Y-%m') as mes,
                tipo_solicitacao,
                status,
                COUNT(*) as total,
                AVG(TIMESTAMPDIFF(DAY, data_solicitacao, data_atualizacao)) as tempo_medio_dias
            FROM pedidos
            WHERE data_solicitacao >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
            GROUP BY DATE_FORMAT(data_solicitacao, '%Y-%m'), tipo_solicitacao, status
            ORDER BY mes DESC
        """)
        relatorios['pedidos_periodo'] = cursor.fetchall()
        
        cursor.execute("""
            SELECT 
                u.nome as unidade,
                COUNT(p.id) as total_pedidos,
                AVG(DATEDIFF(p.data_atualizacao, p.data_solicitacao)) as tempo_medio_dias,
                COUNT(CASE WHEN p.status LIKE '%AGENDADO%' THEN 1 END) as agendados,
                COUNT(CASE WHEN p.status LIKE '%CANCELADO%' THEN 1 END) as cancelados,
                ROUND((COUNT(CASE WHEN p.status LIKE '%AGENDADO%' THEN 1 END) / COUNT(p.id)) * 100, 1) as taxa_sucesso
            FROM unidades_saude u
            LEFT JOIN pedidos p ON u.id = p.unidade_id 
                AND p.data_solicitacao >= DATE_SUB(NOW(), INTERVAL 3 MONTH)
            WHERE u.ativo = 1
            GROUP BY u.id, u.nome
            ORDER BY total_pedidos DESC
        """)
        relatorios['performance_unidades'] = cursor.fetchall()
        
        cursor.execute("""
            SELECT 
                u.nome,
                u.role,
                COUNT(h.id) as acoes_realizadas,
                MAX(u.last_seen) as ultimo_acesso,
                COUNT(DISTINCT p.id) as pedidos_criados
            FROM usuarios u
            LEFT JOIN historico_pedidos h ON u.id = h.criado_por 
                AND h.criado_em >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            LEFT JOIN pedidos p ON u.id = p.usuario_criacao
                AND p.data_solicitacao >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            WHERE u.ativo = 1
            GROUP BY u.id
            ORDER BY acoes_realizadas DESC
            LIMIT 20
        """)
        relatorios['usuarios_ativos'] = cursor.fetchall()
    
    return render_template("dashboards/relatorios.html", relatorios=relatorios, user_role=role)