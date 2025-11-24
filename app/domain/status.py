from enum import Enum


class StatusPedido(str, Enum):
    RECEBIDO = "recebido_recepcao"
    AGUARDANDO_TRIAGEM = "aguardando_triagem"
    CANCELADO_RECEPCAO = "cancelado_recepcao"
    TRIAGEM_CONCLUIDA_MUNICIPAL = "triagem_concluida_municipal"
    TRIAGEM_CONCLUIDA_ESTADUAL = "triagem_concluida_estadual"
    AGUARDANDO_ANALISE_MEDICO_MUNICIPAL = "aguardando_medico_municipal"
    AGUARDANDO_ANALISE_MEDICO_ESTADUAL = "aguardando_medico_estadual"
    DEVOLVIDO_PELO_MEDICO = "devolvido_medico_para_recepcao"
    CANCELADO_MEDICO = "cancelado_medico"
    APROVADO_MUNICIPAL = "aprovado_para_agendamento_municipal"
    APROVADO_ESTADUAL = "aprovado_para_agendamento_estadual"
    AGENDAMENTO_EM_ANDAMENTO = "agendamento_em_andamento"
    AGENDAMENTO_CONFIRMADO = "agendamento_confirmado"
    DEVOLVIDO_SEM_CONTATO = "devolvido_sem_contato_recepcao"
    RETIRADO = "retirado"

    @classmethod
    def choices(cls):
        return [status.value for status in cls]