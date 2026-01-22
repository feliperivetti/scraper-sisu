# 🎓 SISU Daily Sync - Monitoramento de Notas de Corte

Este projeto é uma ferramenta de automação e engenharia de dados projetada para monitorar, coletar e armazenar o histórico das notas de corte do SISU. Ele foca nos cursos mais concorridos, construindo uma base de dados histórica robusta para análise de tendências.

## 🌐 Dashboard Online
Acesse a visualização dos dados em tempo real:  
🚀 **[https://scraper-sisu.streamlit.app](https://scraper-sisu.streamlit.app)**

## 🏗️ Arquitetura e Padrões de Projeto
O sistema foi desenvolvido seguindo padrões de engenharia de software para garantir escalabilidade e manutenção:

* **Padrão MVC (Model-View-Controller):**
    * **Model:** Representação dos dados (vagas e modalidades).
    * **View:** Interface interativa desenvolvida em Streamlit.
    * **Controller:** Orquestração da lógica de negócio e paralelismo.
* **Camada DAL (Data Access Layer):** Implementada via `SisuRepository`, isolando completamente a lógica de persistência de arquivos (CSV/JSON/TXT) das regras de negócio.
* **Injeção de Dependência:** Facilitando a troca de provedores de dados (APIs) sem afetar o fluxo principal.

## 🚀 Diferenciais Técnicos

* **Alta Performance (Parallel Threading):** Implementação de `ThreadPoolExecutor` no Controller para realizar a coleta de múltiplas faculdades simultaneamente, reduzindo o tempo de execução em mais de 90%.
* **Sessões Persistentes:** Uso de `requests.Session` com **Connection Pooling**, permitindo o reuso de conexões TCP (Keep-Alive) e reduzindo a latência nas requisições ao servidor do MEC.
* **Resiliência a Fuso Horário:** Configurado com `zoneinfo` para operar rigorosamente no fuso de **Brasília (UTC-3)**, garantindo a integridade do histórico mesmo quando executado em servidores internacionais (GitHub/Streamlit).
* **Histórico Incremental Inteligente:** O sistema identifica se os dados do dia já foram coletados e utiliza uma lógica de *Skip* para evitar redundância e desperdício de recursos.

## 📂 Estrutura do Projeto

```text
.
├── data/
│   ├── history/     # CSVs com histórico incremental (uma coluna por dia)
│   ├── mappings/    # JSONs de mapeamento de IDs de cursos
│   └── reports/     # Relatórios TXT formatados do último ciclo de sync
└── src/
    ├── providers/    # Provedores de dados (Consumo de APIs externas)
    ├── controller.py # Cérebro do projeto (MVC - Controller)
    ├── repository.py # Camada de persistência (DAL)
    └── cron_sync.py  # Script de automação e rotinas em lote
    └── app.py        # Dashboard Streamlit (MVC - View)
```

## 🤖 Automação e Hospedagem

* **Execução:** O projeto utiliza **GitHub Actions** para rodar o processo de coleta automaticamente todos os dias. O workflow realiza o setup, executa a sincronização e faz o commit automático dos novos dados para o repositório.
* **Hospedagem:** O dashboard de visualização está hospedado no **Streamlit Cloud**, integrado diretamente ao repositório para atualizações contínuas.

---

### 📝 Notas de Desenvolvimento
O projeto foi otimizado para respeitar limites de taxa (Rate Limiting) da API oficial, utilizando um pool de no máximo 10 conexões simultâneas, garantindo a coleta sem risco de bloqueio de IP.