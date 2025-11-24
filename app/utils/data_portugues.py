from datetime import datetime

# Nomes em português
MESES = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}

DIAS = {
    0: 'Segunda-feira', 1: 'Terça-feira', 2: 'Quarta-feira',
    3: 'Quinta-feira', 4: 'Sexta-feira', 5: 'Sábado', 6: 'Domingo'
}

def data_pt(data=None):
    """Formata data em português brasileiro"""
    if data is None:
        data = datetime.now()
    
    if data is None:
        return "Data não disponível"
    
    dia_semana = DIAS.get(data.weekday(), 'N/A')
    mes = MESES.get(data.month, 'N/A')
    
    return f"{dia_semana}, {data.day} de {mes} de {data.year}"

def data_pt_hora(data=None):
    """Formata data com hora em português brasileiro"""
    if data is None:
        data = datetime.now()
    
    if data is None:
        return "Data não disponível"
    
    dia_semana = DIAS.get(data.weekday(), 'N/A')
    mes = MESES.get(data.month, 'N/A')
    
    return f"{dia_semana}, {data.day} de {mes} de {data.year} às {data.strftime('%H:%M')}"

def data_simples(data=None):
    """Formata data simples (dd/mm/aaaa)"""
    if data is None:
        data = datetime.now()
    
    if data is None:
        return "Data não disponível"
    
    return data.strftime('%d/%m/%Y')

def data_simples_hora(data=None):
    """Formata data com hora (dd/mm/aaaa às HH:MM)"""
    if data is None:
        data = datetime.now()
    
    if data is None:
        return "Data não disponível"
    
    return data.strftime('%d/%m/%Y às %H:%M')

# Instância global para facilitar o uso
data_utils = type('DataUtilsPT', (), {
    'agora': lambda: datetime.now(),
    'formatar': data_pt,
    'formatar_completa': data_pt,
    'formatar_hora': data_pt_hora,
    'simples': data_simples,
    'simples_hora': data_simples_hora,
    'mes': lambda data: MESES.get(data.month if data else datetime.now().month, 'N/A'),
    'dia_semana': lambda data: DIAS.get(data.weekday() if data else datetime.now().weekday(), 'N/A')
})()

if __name__ == "__main__":
    print("=== TESTE RÁPIDO ===")
    agora = datetime.now()
    print(f"Agora: {data_pt_hora(agora)}")
    print(f"Data: {data_pt(agora)}")
    print(f"Simples: {data_simples(agora)}")