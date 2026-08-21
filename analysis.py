import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import numpy as np
import powerlaw
import math
import sys

def smallWorld(graph):
    print(f"[*Metrica*], [*valor*], [*valor ER equivalente*],")
    k_avg = sum(dict(graph.degree()).values()) / graph.number_of_nodes()
    k = (2 * graph.number_of_edges()) / graph.number_of_nodes()

    L_ER = math.log(graph.number_of_nodes()) / math.log(k_avg)
    C_ER = k_avg / graph.number_of_nodes()

    L = nx.average_shortest_path_length(graph)
    C = nx.average_clustering(graph)

    print(f"[Grado promedio], [{k}], [{k_avg}],")
    print(f"[Largo caracteristico], [{L}], [{L_ER}],")
    print(f"[Coeficiente de clustering], [{C}], [{C_ER}],")

    return

def alpha_centrality(graph, alpha=0.1):
    eigenvalues = nx.adjacency_spectrum(graph)
    spectral_radius = max(abs(e) for e in eigenvalues)
    alpha = 0.7 / spectral_radius
    return nx.katz_centrality(graph, alpha=alpha, weight='weight')

def compute_centrality(graph, func, kind):
    try:
        return func(graph)
    except Exception as e:
        print(f"\t\tError computing {kind} centrality: {e}")
        return None

# Save centrality measures to CSV files
def save_centrality(dict, output_name):
        try:
            for kind in dict:
                with open(output_name, 'w', encoding='utf-8') as f:
                    print(f"\t\t{kind} centrality saved to: {output_name}")
                    for node, centrality in sorted(dict[kind].items(), key=lambda item: item[1], reverse=True):
                        f.write(f"{node}\t{centrality}\n")
        except Exception as e:
            print(f"\t\tError saving centrality: {kind}\n\t\t{e}")

def get_some_centrality(graph, lamdas=[nx.degree_centrality, alpha_centrality], kinds=['degree', 'alpha-centrality']):
    """Compute all centrality measures and return as dict of dicts."""
    
    for kind in kinds:
        save_centrality({kind: compute_centrality(graph, lamdas[kinds.index(kind)], kind)}, f"DATA/OUTPUT/centrality_{kind}.csv")

def get_graph_from_csv_with_header(file_path):
    import csv

    G = nx.DiGraph()
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)  # Skip the header row
        for row in reader:
            if len(row) >= 7:
                source, target, weight = row[0], row[6], row[13]
                G.add_edge(source, target, weight=float(weight))
    return G


def plot(metric_path, title, outdir):
    print(f"Constructing dot diagram for {metric_path}...")
    df = pd.read_csv(metric_path, sep='\t', names=['node', 'value'])
    values = df['value']
    counts = values.value_counts().sort_index()
    total = counts.sum()

    plt.figure()
    plt.scatter(counts.index, counts.values / total, s=3, color='black')
    plt.xscale('log')
    plt.yscale('log')
    plt.title(title)
    plt.xlabel("Valor")
    plt.ylabel("Frecuencia")

    if 'degree' in metric_path:
        values_array = np.array(values)
        fit = powerlaw.Fit(values_array, verbose=False)
        gamma = fit.alpha
        xmin = fit.xmin

        if np.isfinite(gamma) and np.isfinite(xmin):
            x_fit = counts.index[counts.index >= xmin].to_numpy(dtype=float)
            if x_fit.size:
                observed_tail = (counts.loc[x_fit] / total).to_numpy(dtype=float)
                y_fit = observed_tail[0] * np.power(x_fit / x_fit[0], -gamma)
                valid = y_fit >= observed_tail.min()

                if np.count_nonzero(valid) >= 2:
                    plt.plot(x_fit[valid], y_fit[valid], 'r--', linewidth=2, label=f'Power law (γ={gamma:.2f})')
                    plt.legend()

    plt.savefig(f"{outdir}.png")
    plt.close()


def main(file_path):
    G = get_graph_from_csv_with_header(file_path)
    largest = nx.DiGraph(G.subgraph(max(nx.strongly_connected_components(G), key=len)))
    print(largest)
    smallWorld(largest)
    get_some_centrality(G,[nx.degree_centrality, alpha_centrality, nx.in_degree_centrality, nx.out_degree_centrality], ['degree', 'alpha-centrality', 'indegree', 'outdegree'])
    for kind in ['degree','alpha-centrality','indegree','outdegree']:
        metric_path = f"DATA/OUTPUT/centrality_{kind}.csv"
        plot(metric_path, title=f"Histogram for {kind}", outdir=f"DATA/OUTPUT/Hist_{kind}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analysis.py <file_path>")
        sys.exit(1)
    main(sys.argv[1])