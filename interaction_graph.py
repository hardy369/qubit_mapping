import networkx as nx
from qiskit import QuantumCircuit
from qiskit.converters import circuit_to_dag
import json
import matplotlib.pyplot as plt

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
    
    return qc

def generate_interaction_graph(qc):
    """
    Generate interaction graph from quantum circuit.
    Returns the graph and detailed interaction information.
    """
    # Convert circuit to DAG
    dag = circuit_to_dag(qc)

    # Track interactions and their first occurrence
    interaction_edges = []
    first_interaction = {}
    edge_counts = {}  # Track number of interactions between each pair

    # Process all two-qubit gates
    for gate_number, gate in enumerate(dag.two_qubit_ops()):
        qubits = [q._index for q in gate.qargs]
        qubit_pair = tuple(sorted(qubits))
        
        # Track first interaction
        if qubit_pair not in first_interaction:
            first_interaction[qubit_pair] = gate_number
        
        # Count interactions
        if qubit_pair not in edge_counts:
            edge_counts[qubit_pair] = 0
        edge_counts[qubit_pair] += 1
        
        interaction_edges.append((qubits[0], qubits[1], first_interaction[qubit_pair]))

    # Create interaction graph
    G = nx.Graph()
    
    # Add edges with weights being the first interaction number
    for edge in interaction_edges:
        qubit1, qubit2, gate_number = edge
        if not G.has_edge(qubit1, qubit2):
            G.add_edge(qubit1, qubit2, weight=gate_number, count=edge_counts[tuple(sorted([qubit1, qubit2]))])

    return G, first_interaction, edge_counts

def analyze_interaction_graph(G):
    """
    Analyze properties of the interaction graph.
    """
    # Find centers
    centers = nx.center(G)
    
    # Get center with maximum degree
    center_degrees = {node: G.degree(node) for node in centers}
    max_degree = max(center_degrees.values())
    max_degree_centers = [node for node, degree in center_degrees.items() 
                         if degree == max_degree]
    selected_center = min(max_degree_centers)

    return {
        'centers': centers,
        'selected_center': selected_center,
        'center_degrees': center_degrees,
        'diameter': nx.diameter(G),
        'average_shortest_path': nx.average_shortest_path_length(G),
        'density': nx.density(G)
    }

def visualize_interaction_graph(G, analysis):
    """
    Create visualization of the interaction graph.
    """
    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(G, k=1)
    
    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_color='lightblue', 
                          node_size=500)
    
    # Highlight center nodes
    nx.draw_networkx_nodes(G, pos, 
                          nodelist=analysis['centers'],
                          node_color='lightgreen',
                          node_size=500)
    
    # Highlight selected center
    nx.draw_networkx_nodes(G, pos,
                          nodelist=[analysis['selected_center']],
                          node_color='red',
                          node_size=500)
    
    # Draw edges with weights
    nx.draw_networkx_edges(G, pos)
    
    # Add labels
    nx.draw_networkx_labels(G, pos)
    edge_labels = nx.get_edge_attributes(G, 'count')
    nx.draw_networkx_edge_labels(G, pos, edge_labels)
    
    plt.title("Quantum Circuit Interaction Graph")
    plt.axis('off')
    plt.savefig('interaction_graph.png')
    plt.close()

def main():
    try:
        # Read circuit from file
        circuit = read_circuit_from_file('circuit.json')
        
        # Generate interaction graph
        G, first_interactions, edge_counts = generate_interaction_graph(circuit)
        
        # Analyze the graph
        analysis = analyze_interaction_graph(G)
        
        # Print analysis results
        print("\nInteraction Graph Analysis:")
        print(f"Number of qubits: {G.number_of_nodes()}")
        print(f"Number of interactions: {G.number_of_edges()}")
        print("\nCenter Analysis:")
        print(f"All centers: {analysis['centers']}")
        print("Center degrees:")
        for node, degree in analysis['center_degrees'].items():
            print(f"  Node {node}: degree {degree}")
        print(f"Selected center (max degree, min index): {analysis['selected_center']}")
        
        print("\nInteraction Details:")
        for (q1, q2), count in edge_counts.items():
            print(f"Qubits {q1}-{q2}: {count} interactions (first at gate {first_interactions[(q1, q2)]})")
        
        print("\nGraph Metrics:")
        print(f"Diameter: {analysis['diameter']}")
        print(f"Average shortest path length: {analysis['average_shortest_path']:.2f}")
        print(f"Graph density: {analysis['density']:.2f}")
        
        # Visualize the graph
        visualize_interaction_graph(G, analysis)
        print("\nInteraction graph visualization saved as 'interaction_graph.png'")
        
    except FileNotFoundError:
        print("Error: circuit.json file not found")
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in circuit file")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
