"""
POPIN v4 — Step 6: Robustness Checks

Este script executa os testes de robustez estatística para o paper:
1. Length Bias Check: Regressão do POPIN Final Score contra o Log(Word Count).
2. Peak Populism Check: Correlação da Média Anual contra o P95 e P99.
"""

import duckdb
import pandas as pd
import numpy as np
from scipy import stats
import os

def run_robustness_checks(db_path="./popin.duckdb"):
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    con = duckdb.connect(db_path, read_only=True)

    print("--- Length Bias Check (Text Length Independence) ---")
    df_len = con.execute('''
        SELECT s.final_score, d.word_count
        FROM scores s
        JOIN discourses d ON s.discourse_id = d.id
        WHERE s.final_score IS NOT NULL AND d.word_count > 0
    ''').fetchdf()

    corr = df_len['final_score'].corr(df_len['word_count'])
    print(f"Pearson Correlation (r) between Final Score and Word Count: {corr:.4f}")

    log_words = np.log(df_len['word_count'])
    res = stats.linregress(log_words, df_len['final_score'])
    print(f"R-squared (OLS with Log Word Count): {res.rvalue**2:.4f}")
    print(f"P-value: {res.pvalue:.4e}")

    print("\n--- Aggregation Sensitivity (Mean vs Peak Populism) ---")
    df_agg = con.execute('''
        SELECT 
            d.leader_name, 
            d.discourse_year,
            AVG(s.final_score) as mean_score,
            QUANTILE_CONT(s.final_score, 0.95) as p95_score,
            QUANTILE_CONT(s.final_score, 0.99) as p99_score
        FROM scores s
        JOIN discourses d ON s.discourse_id = d.id
        WHERE s.final_score IS NOT NULL
        GROUP BY d.leader_name, d.discourse_year
        HAVING COUNT(*) > 10
    ''').fetchdf()

    corr_p95 = df_agg['mean_score'].corr(df_agg['p95_score'])
    corr_p99 = df_agg['mean_score'].corr(df_agg['p99_score'])
    
    print(f"Correlation between Annual Mean and 95th Percentile: {corr_p95:.4f}")
    print(f"Correlation between Annual Mean and 99th Percentile: {corr_p99:.4f}")

if __name__ == "__main__":
    # Aponta para o banco de dados relativo caso seja executado dentro da pasta
    db_location = "popin.duckdb"
    
    # Se o banco não for encontrado no diretório atual, usa o caminho absoluto
    if not os.path.exists(db_location):
        db_location = r"C:\Users\Andre\Downloads\popin v4\arquivos popin v4\popin.duckdb"
        
    run_robustness_checks(db_path=db_location)
