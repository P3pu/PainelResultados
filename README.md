# 🏃‍♂️ Painel de Processamento de Resultados de Corrida

Este é um projeto **Flask** robusto para automação de cronometragem e análise de dados de eventos esportivos. O sistema recebe duas planilhas (Inscritos e Resultados), realiza uma limpeza profunda, cruza os dados via CPF (similar a um PROCV) e gera métricas de performance automática por modalidade.

## ✨ Funcionalidades Principais

### 1. Tratamento da Planilha de Inscritos (Planilha A)
* **Limpeza Inteligente de Categorias:** Remove automaticamente linhas que contenham termos como "cortesia", "company", "grupos" ou "saúde" (filtros imunes a acentos e variações de maiúsculas/minúsculas).
* **Padronização de Telefone:** Formata todos os números de celular para o padrão internacional `5581900000000`, removendo parênteses, traços e espaços.
* **Deduplicação de CPFs:** Garante que cada atleta seja único na base de busca, evitando erros de multiplicação de linhas no resultado final.

### 2. Processamento de Resultados (Planilha B)
* **Merge de Dados (PROCV):** Cruza a planilha de resultados com a de inscritos para buscar informações como `Pelotão`, `Celular`, `Evento`, `Cidade` e `Estado`.
* **Cálculo de Participantes por Modalidade:** Identifica o volume total de atletas em cada categoria (ex: 5km, 10km) dinamicamente.
* **Métrica de Performance:** Calcula o percentual de classificação do atleta em relação ao total da sua modalidade específica.
* **Flag de Destaque:** Gera uma coluna "Porcentagem Baixa" (SIM/NÃO) para identificar atletas que ficaram entre os 30% melhores da prova.

---

## 🛠️ Estrutura do Projeto

```text
meu_projeto_painel/
├── app.py              # Lógica principal, rotas Flask e processamento Pandas
├── requirements.txt    # Lista de dependências do Python
├── .gitignore          # Arquivos e pastas ignorados pelo Git
├── README.md           # Documentação do projeto
├── templates/          # Interface do usuário (HTML)
│   └── index.html      # Página de upload e resultados
└── uploads/            # Pasta temporária para geração dos arquivos de download