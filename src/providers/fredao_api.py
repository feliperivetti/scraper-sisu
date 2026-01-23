def parse_fredao_response(self, response_json: dict):
    # O Dash retorna um dicionário com UUIDs como chaves
    # Precisamos encontrar qual chave contém o 'props' com o gráfico
    response_data = response_json.get("response", {})
    
    for component_id, component_body in response_data.items():
        # Procuramos o componente que tem a lista de dados
        props = component_body.get("props", {})
        data_list = props.get("data", [])
        
        if data_list:
            # Aqui você tem a lista com DIA 1, DIA 2, etc.
            # Você pode pegar apenas o último dia (o mais atual)
            latest_data = data_list[-1]
            cutoff_score = latest_data.get("A")
            print(f"Nota de corte encontrada: {cutoff_score}")
            return cutoff_score
            
    return None