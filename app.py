import os
import re
import pandas as pd
import numpy as np
from flask import Flask, render_template, request, send_file
from io import BytesIO

app = Flask(__name__)

# Variável global para armazenar o resultado temporariamente para o download
df_resultado_final = None

def limpar_telefone(tel):
    """Limpa o telefone para o formato 5581900000000."""
    num = re.sub(r'\D', '', str(tel))
    if not num: return ""
    return f"55{num}" if not num.startswith('55') else num

def ler_planilha(file):
    """Lê CSV ou Excel de forma flexível."""
    if file.filename.endswith(('.xlsx', '.xls')):
        return pd.read_excel(file)
    return pd.read_csv(file)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    global df_resultado_final
    
    if 'file1' not in request.files or 'file2' not in request.files:
        return "Selecione os dois arquivos!"

    try:
        # 1. Carregar Dados
        df_a = ler_planilha(request.files['file1']) # Inscritos
        df_b = ler_planilha(request.files['file2']) # Resultados

        # --- PROCESSAMENTO PLANILHA A (LIMPEZA) ---
        
        # Filtro de Categoria (Remove 'saude', 'cortesia', etc)
        termos_remover = ["cortesia", "company", "grupos", "saude", "saúde"]
        regex_limpeza = '|'.join(termos_remover)
        df_a = df_a[~df_a['Categoria'].astype(str).str.contains(regex_limpeza, case=False, na=False)].copy()

        # Normalização do Telefone
        df_a['celular'] = df_a['Telefone'].apply(limpar_telefone)

        # Padronização do CPF para o Merge
        df_a['cpf'] = df_a['Documento'].astype(str).str.strip()

        # IMPORTANTE: Remover CPFs duplicados na Planilha A para evitar o erro de multiplicação de linhas
        df_a = df_a.drop_duplicates(subset=['cpf'], keep='first')

        # --- PROCESSAMENTO PLANILHA B (CRUZAMENTO E CÁLCULOS) ---

        # Padroniza CPF na B também
        df_b['cpf'] = df_b['cpf'].astype(str).str.strip()

        # Colunas que queremos extrair da Planilha A
        colunas_procv = ['cpf', 'Pelotão', 'celular', 'Evento', 'Cidade', 'Estado']
        colunas_existentes_a = [c for c in colunas_procv if c in df_a.columns]

        # MERGE (O nosso PROCV): Base na B (Resultados), traz informações da A
        df_final = pd.merge(df_b, df_a[colunas_existentes_a], on='cpf', how='left')

        # Selecionar apenas as colunas solicitadas para o painel final
        colunas_finais_req = [
            'nome_atleta', 'cpf', 'nr_peito', 'sexo', 'tempo_total', 
            'modalidade', 'pace', 'Pelotão', 'classificacao_total',
            'celular', 'Evento', 'Cidade', 'Estado'
        ]
        df_final = df_final[[c for c in colunas_finais_req if c in df_final.columns]].copy()

        # Cálculo: total_participantes por cada modalidade
        df_final['total_participantes'] = df_final.groupby('modalidade')['nome_atleta'].transform('count')

        # Cálculo: porcentagem de classificação
        df_final['porcentagem'] = (df_final['classificacao_total'] / df_final['total_participantes']) * 100
        
        # Cálculo: porcentagem_baixa (SIM se < 30%)
        # np.where funciona como o SE do Excel: SE(condicao; verdadeiro; falso)
        df_final['porcentagem_baixa'] = np.where(df_final['porcentagem'] < 30, 'SIM', 'NÃO')

        # Formatação para exibição amigável
        df_final['porcentagem'] = df_final['porcentagem'].round(2).astype(str) + '%'

        # ✅ NOVO: Remove linhas onde classificacao_total é 99999999
        df_final = df_final[df_final['classificacao_total'] != 99999999]

        # ✅ NOVO: Remove linhas onde 'celular' está vazio ou nulo
        df_final = df_final[df_final['celular'].notna() & (df_final['celular'].str.strip() != '')]

        # ✅ NOVO: Ordena por porcentagem do maior para o menor
        # Precisamos de uma coluna numérica temporária para ordenar (a formatada já tem '%')
        df_final['_pct_num'] = df_final['porcentagem'].str.replace('%', '', regex=False).astype(float)
        df_final = df_final.sort_values('_pct_num', ascending=False).drop(columns=['_pct_num'])

        # Salva na variável global para o download
        df_resultado_final = df_final.copy()

        # Renderizar pré-visualização
        tabela_preview = df_final.head(50).to_html(classes='table table-sm table-striped', index=False)
        
        return f"""
        <html>
            <head>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                <style>body{{padding: 40px; background: #f8f9fa;}} .container{{background:white; padding:30px; border-radius:15px;}}</style>
            </head>
            <body>
                <div class="container shadow">
                    <h2 class="mb-4">Painel de Resultados Gerado</h2>
                    <div class="alert alert-info">
                        <strong>Sucesso!</strong> Foram processados {len(df_final)} atletas.
                    </div>
                    <div class="mb-4">
                        <a href="/download" class="btn btn-success btn-lg">Baixar Planilha Completa (.xlsx)</a>
                        <a href="/" class="btn btn-outline-secondary btn-lg">Novo Upload</a>
                    </div>
                    <h5>Pré-visualização (Primeiros 50):</h5>
                    <div class="table-responsive" style="max-height: 500px; overflow-y: auto;">
                        {tabela_preview}
                    </div>
                </div>
            </body>
        </html>
        """

    except Exception as e:
        return f"<h3>Erro no Processamento:</h3><p>{str(e)}</p><br><a href='/'>Voltar</a>"

@app.route('/download')
def download():
    global df_resultado_final
    if df_resultado_final is None:
        return "Nenhum dado disponível para download."
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_resultado_final.to_excel(writer, index=False, sheet_name='Resultado')
    output.seek(0)
    
    return send_file(output, download_name="resultado_processado.xlsx", as_attachment=True)

if __name__ == '__main__':
    # Roda o servidor. '0.0.0.0' permite acesso por outras máquinas na rede
    app.run(host='0.0.0.0', port=5000, debug=True)