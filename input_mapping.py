import networkx as nx
from qiskit import QuantumCircuit
from qiskit.converters import circuit_to_dag
import json

def read_circuit_from_file(filename):
    """
    Read quantum circuit description from a JSON file.
    """
    with open(filename, 'r') as f:
        circuit_data = json.load(f)
    
    qc = QuantumCircuit(circuit_data['n_qubits'])
    
    for gate in circuit_data['gates']:
        if gate['type'] == 'cx':
            qc.cx(gate['control'], gate['target'])
    
    qc.measure_all()
    return qc

def read_coupling_from_file(filename):
    """
    Read coupling graph description from a JSON file.
    """
    with open(filename, 'r') as f:
        coupling_data = json.load(f)
    return coupling_data

def get_qubit_index(node):
    """
    Extract numeric index from qubit label (e.g., 'Q7' -> 7)
    """
    return int(node.replace('Q', ''))

def find_center_with_max_degree(G):
    """
    Find center nodes and return the one with maximum degree.
    If there's a tie in degree, return the one with minimum qubit index.
    Handles both string labels ('Q0', 'Q1', etc.) and integer nodes.
    """
    centers = nx.center(G)
    # Get degrees of center nodes
    center_degrees = {node: G.degree(node) for node in centers}
    # Find maximum degree among centers
    max_degree = max(center_degrees.values())
    # Get all centers with maximum degree
    max_degree_centers = [node for node, degree in center_degrees.items() 
                         if degree == max_degree]
    
    # Check if nodes are strings (coupling graph) or integers (interaction graph)
    if isinstance(max_degree_centers[0], str):
        # For coupling graph (nodes are strings like 'Q0', 'Q1')
        return min(max_degree_centers, key=lambda x: int(x.replace('Q', '')))
    else:
        # For interaction graph (nodes are integers)
        return min(max_degree_centers)

def get_qubit_mapping(qc, coupling_graph):
    """
    Generate qubit mapping for the given quantum circuit and coupling graph.
    """
    dag = circuit_to_dag(qc)
    interaction_edges = []
    first_interaction = {}

    for gate_number, gate in enumerate(dag.two_qubit_ops()):
        qubits = [q._index for q in gate.qargs]
        qubit_pair = tuple(sorted(qubits))
        
        if qubit_pair not in first_interaction:
            first_interaction[qubit_pair] = gate_number
        
        interaction_edges.append((qubits[0], qubits[1], first_interaction[qubit_pair]))

    # Create interaction graph (Gd)
    Gd = nx.Graph()
    for edge in interaction_edges:
        qubit1, qubit2, gate_number = edge
        Gd.add_edge(qubit1, qubit2, weight=gate_number)

    # Create coupling graph (Gc)
    Gc = nx.Graph(coupling_graph)

    if len(Gc) < qc.num_qubits:
        raise ValueError(f"Coupling graph has fewer qubits ({len(Gc)}) than required by the circuit ({qc.num_qubits})")

    # Find centers with maximum degree
    interaction_center = find_center_with_max_degree(Gd)
    coupling_center = find_center_with_max_degree(Gc)

    # Print detailed center analysis
    print(f"\nCoupling Graph Centers Analysis:")
    centers = nx.center(Gc)
    print("All centers and their degrees:")
    for center in centers:
        print(f"Center: {center}, Degree: {Gc.degree(center)}")
    print(f"Selected center: {coupling_center} (Degree: {Gc.degree(coupling_center)})")

    print(f"\nInteraction Graph Center Analysis:")
    print(f"Selected center: {interaction_center}")
    print(f"Degree: {Gd.degree(interaction_center)}")

    # BFS traversal of interaction graph
    bfs_edges = list(nx.bfs_edges(Gd, interaction_center))
    bfs_traversal = [interaction_center] + [v for u, v in bfs_edges]

    # Initialize mapping
    mapping = {}
    mapped_qubits = set()

    mapping[interaction_center] = coupling_center
    mapped_qubits.add(coupling_center)

    queue = bfs_traversal.copy()
    queue.pop(0)

    while queue:
        p = queue.pop(0)
        ref_locs = [neighbor for neighbor in Gd.neighbors(p) if neighbor in mapping]
        candi_locs = [neighbor for neighbor in Gc.neighbors(mapping[ref_locs[0]]) 
                     if neighbor not in mapped_qubits]

        for ref in ref_locs[1:]:
            candi_locs.sort(key=lambda x: nx.shortest_path_length(Gc, source=mapping[ref], target=x))
            candi_locs = candi_locs[:1]

        if len(candi_locs) == 1:
            mapping[p] = candi_locs[0]
            mapped_qubits.add(candi_locs[0])
        else:
            selected = max(candi_locs, key=lambda x: Gc.degree[x])
            mapping[p] = selected
            mapped_qubits.add(selected)

    return mapping

def main():
    try:
        circuit = read_circuit_from_file('circuit.json')
        coupling_graph = read_coupling_from_file('coupling.json')
        
        mapping = get_qubit_mapping(circuit, coupling_graph)
        
        print("\nQubit Mapping Results:")
        for logical_qubit, physical_qubit in sorted(mapping.items()):
            print(f"q{logical_qubit} -> {physical_qubit}")
            
    except FileNotFoundError as e:
        print(f"Error: File not found - {e.filename}")
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in input file")
    except ValueError as e:
        print(f"Error: {str(e)}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
