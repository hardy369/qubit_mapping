import networkx as nx
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit
from qiskit.converters import circuit_to_dag

# Step 1: Define the quantum circuit
qc = QuantumCircuit(4)
qc.cx(2, 0)
qc.cx(0, 1)
qc.cx(0, 2)
qc.cx(2, 1)
qc.cx(1, 2)
qc.cx(2, 3)
qc.cx(0, 3)
qc.measure_all()

# Convert the circuit to a DAG (directed acyclic graph)
dag = circuit_to_dag(qc)

# Extract the interaction graph with edge weights (gate numbers)
interaction_edges = []  # Store edges as pairs of qubits with gate numbers
first_interaction = {}  # Store the first gate number for each pair of qubits

# Iterate through the DAG and track the gate numbers
for gate_number, gate in enumerate(dag.two_qubit_ops()):  # Consider only two-qubit operations
    qubits = [q._index for q in gate.qargs]  # Use _index to access qubit index
    qubit_pair = tuple(sorted(qubits))  # Sort qubits to ensure (q1, q2) is the same as (q2, q1)

    # If the pair has not been seen before, record the first gate number
    if qubit_pair not in first_interaction:
        first_interaction[qubit_pair] = gate_number

    # Append the edge with the gate number (weight)
    interaction_edges.append((qubits[0], qubits[1], first_interaction[qubit_pair]))  # Use the first gate number

# Create an undirected graph for the interaction
Gd = nx.Graph()

# Add edges to the graph with weights (gate numbers)
for edge in interaction_edges:
    qubit1, qubit2, gate_number = edge
    Gd.add_edge(qubit1, qubit2, weight=gate_number)
# Draw the graph using Matplotlib
pos = nx.spring_layout(Gd)  # Positions for nodes using spring layout
plt.figure(figsize=(8, 6))  # Set the figure size

# Draw the graph with labels and edge weights
nx.draw(Gd, pos, with_labels=True, node_size=500, node_color='skyblue', font_size=15, font_weight='bold',
        edge_color='gray')
edge_labels = nx.get_edge_attributes(Gd, 'weight')  # Get the edge weights
# Edge labels are now just the gate numbers, no "g" prefix
nx.draw_networkx_edge_labels(Gd, pos, edge_labels=edge_labels, font_size=12, font_color='red')

# Show the plot
plt.title("Quantum Circuit Interaction Graph with Gate Numbers")
plt.show()
