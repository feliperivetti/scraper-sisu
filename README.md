# 🎓 SISU Daily Sync - Monitoramento de Notas de Corte

Este projeto evoluiu de um script simples para auxiliar no monitoramento de cursos específicos, como Psicologia, para uma plataforma de engenharia de dados robusta. Ele utiliza uma arquitetura moderna para coletar, tratar e visualizar o histórico das notas de corte do SISU 2026, garantindo integridade mesmo diante de instabilidades nos dados oficiais.

## 🏗️ Arquitetura e Padrões de Projeto

O sistema segue o padrão MVC (Model-View-Controller) e foi refatorado para suportar persistência relacional e consumo híbrido de dados:

- **Model**: Gerenciamento de dados com SQLite, garantindo consultas muito mais rápidas que a abordagem anterior baseada em CSV.
- **View**: Dashboard analítico desenvolvido em Streamlit com visualizações dinâmicas via Plotly.
- **Controller**: Orquestração de busca híbrida (Local DB + Live API) e lógica de paralelismo.
- **Camada DAL (Data Access Layer)**: Isolamento total da lógica de persistência no SisuRepository.

## 🚀 Diferenciais Técnicos e Evolução

- **Estratégia Híbrida (Lazy Loading)**: O sistema prioriza a consulta ao banco local para os 17 cursos prioritários. Caso o usuário selecione um curso fora do cache, o app realiza uma busca On-Demand via API Especialista (Professor Fredão).
- **Normalização de Dados**: Tratamento rigoroso de strings (Uppercase/Strip) e uso de Composite Keys (Universidade + Cidade + Curso) para evitar colisões e erros em gráficos de séries temporais.
- **Automação com GitHub Actions**: Workflow configurado para realizar o sync diário, processar os dados e persistir as atualizações no repositório automaticamente.

## 📂 Estrutura do Projeto
```
.
├── data/
│   ├── sisu_data.db     # Banco de dados SQLite (Histórico consolidado)
│   ├── mappings/        # JSONs de mapeamento de IDs (MEC vs Especialista)
│   └── reports/         # Relatórios legados em TXT para consulta rápida
└── src/
    ├── providers/       # Abstração de APIs (MEC e Provedores Externos)
    ├── repository.py    # DAL - Operações de banco e carregamento de JSON
    ├── controller.py    # Lógica de negócio e coordenação de threads
    └── app.py           # Interface Streamlit (Filtros dinâmicos e Gráficos)
```

## 📊 Visualização Avançada

O dashboard foi projetado para oferecer clareza máxima na tomada de decisão:

- **Filtros Cascata**: Seleção de UF que filtra automaticamente as instituições disponíveis.
- **Gráficos de Tendência**: Visualização das 5 opções mais acessíveis, com eixos categóricos travados no cronograma oficial (20/01 a 23/01).
- **Tabela Pivotada**: Visão multidimensional incluindo Curso, Universidade, Cidade e UF.

## 📝 Notas de Desenvolvimento

Originalmente concebido para gerar relatórios simples em .txt, o projeto foi expandido para praticar conceitos avançados de Python, SQL e Engenharia de Software.