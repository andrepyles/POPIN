"""
POPIN v4 — Step 7: Dimensionality Validation (PCA)

Este script calcula a Análise de Componentes Principais usando numpy
para justificar empiricamente a agregação dos 6 eixos ideacionais.
"""

import duckdb
import numpy as np
import os

def run_pca_validation(db_path="./popin.duckdb"):
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    con = duckdb.connect(db_path, read_only=True)
    
    print("--- Extraindo dados do DuckDB ---")
    df = con.execute('''
        SELECT people_centrism, anti_elitism, moral_dichotomy, 
               popular_sovereignty, exclusionary_rhetoric, crisis_rhetoric 
        FROM scores 
        WHERE final_score IS NOT NULL
    ''').fetchdf()

    print(f"Total de registros válidos para PCA: {len(df):,}")

    # Converte para array numpy
    X = df.to_numpy()

    # Padroniza os dados (Média 0, Variância 1) - Passo essencial do PCA
    X_std = (X - np.mean(X, axis=0)) / np.std(X, axis=0)

    # Calcula a Matriz de Covariância
    cov_mat = np.cov(X_std, rowvar=False)

    # Calcula os Autovalores (Eigenvalues) e Autovetores (Eigenvectors)
    eigen_vals, eigen_vecs = np.linalg.eigh(cov_mat)

    # Ordena em ordem decrescente (do componente mais forte para o mais fraco)
    sorted_idx = np.argsort(eigen_vals)[::-1]
    eigen_vals = eigen_vals[sorted_idx]
    eigen_vecs = eigen_vecs[:, sorted_idx]

    # Calcula a Variância Explicada por cada Componente Principal
    tot = sum(eigen_vals)
    var_exp = [(i / tot) for i in eigen_vals]

    print("\n--- PCA Explained Variance (Construct Cohesion) ---")
    print("Principal Component\tExplained Variance\tCumulative Variance")
    cum_var = 0
    for i, var in enumerate(var_exp):
        cum_var += var
        print(f"PC{i+1}\t\t\t{var*100:.1f}%\t\t\t{cum_var*100:.1f}%")

    print("\n--- PC1 Loadings (Dimensional Weights on the Latent Construct) ---")
    print("Ideational Dimension\t\tLoading on PC1")
    # Pega os autovetores do PC1. Usamos valor absoluto pois a direção do vetor (sinal) é arbitrária no PCA
    for col, load in zip(df.columns, np.abs(eigen_vecs[:, 0])):
        print(f"{col:<30}\t{load:.4f}")

if __name__ == "__main__":
    # Aponta para o banco de dados relativo caso seja executado dentro da pasta
    db_location = "popin.duckdb"
    
    # Se o banco não for encontrado no diretório atual, usa o caminho absoluto
    if not os.path.exists(db_location):
        db_location = r"C:\Users\Andre\Downloads\popin v4\arquivos popin v4\popin.duckdb"
        
    run_pca_validation(db_path=db_location)
