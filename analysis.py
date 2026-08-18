import networkx as nx
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


def get_graph_from_csv_with_header(file_path):
    """
    Reads a CSV file and creates a directed graph using NetworkX.

    Args:
        file_path (str): The path to the CSV file.

    Returns:
        networkx.DiGraph: A directed graph created from the CSV file.
    """
    import csv

    G = nx.DiGraph()
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)  # Skip the header row
        for row in reader:
            if len(row) >= 7:
                source, target = row[0], row[6]
                G.add_edge(source, target)
    return G

def main(file_path):
    G = get_graph_from_csv_with_header(file_path)
    print(nx.strongly_connected_components(G))
    largest = nx.DiGraph(G.subgraph(max(nx.strongly_connected_components(G), key=len)))
    print(largest)
    smallWorld(largest)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analysis.py <file_path>")
        sys.exit(1)
    main(sys.argv[1])