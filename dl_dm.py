import networkx as nx
from qiskit import QuantumCircuit
from qiskit.converters import circuit_to_dag

# Step 1: Define the quantum circuit
qc = QuantumCircuit(6)
qc.cx(0, 2)
qc.cx(5, 2)
qc.cx(0, 5)
qc.cx(4, 0)
qc.cx(0, 3)
qc.cx(5, 0)
qc.cx(3, 1)
qc.measure_all()

# Convert the circuit to a DAG (directed acyclic graph)
dag = circuit_to_dag(qc)

# Extract the interaction graph with edge weights (gate numbers)
interaction_edges = []  # Store edges as pairs of qubits with gate numbers
first_interaction = {}  # Store the first gate number for each pair of qubits

# Dependency list
dependency_list = {}

# Iterate through the DAG and track the gate numbers
for gate_number, gate in enumerate(dag.two_qubit_ops()):  # Consider only two-qubit operations
    qubits = [q._index for q in gate.qargs]  # Use _index to access qubit index
    qubit_pair = tuple(sorted(qubits))  # Sort qubits to ensure (q1, q2) is the same as (q2, q1)

    # If the pair has not been seen before, record the first gate number
    if qubit_pair not in first_interaction:
        first_interaction[qubit_pair] = gate_number

    # Append the edge with the gate number (weight)
    interaction_edges.append((qubits[0], qubits[1], first_interaction[qubit_pair]))

    # Update dependency list
    for q in qubits:
        if q not in dependency_list:
            dependency_list[q] = []
        dependency_list[q].append(gate_number)

# Create the interaction graph (Gd)
Gd = nx.Graph()
for edge in interaction_edges:
    qubit1, qubit2, gate_number = edge
    Gd.add_edge(qubit1, qubit2, weight=gate_number)

# Define the coupling graph (Gc)
coupling_graph = {
    'Q0': ['Q1','Q5'],
    'Q1': ['Q0','Q2','Q6','Q7'],
    'Q2': ['Q1','Q3','Q6','Q7'],
    'Q3': ['Q2','Q4','Q8','Q9'],
    'Q4': ['Q3','Q8','Q9'],
    'Q5': ['Q0','Q6','Q10','Q11'],
    'Q6': ['Q1','Q2','Q5','Q7','Q10','Q11'],
    'Q7': ['Q1','Q2','Q6','Q8','Q12','Q13'],
    'Q8': ['Q3','Q4','Q7','Q9','Q12','Q13'],
    'Q9': ['Q3','Q4','Q8','Q14'] ,
    'Q10': ['Q5','Q6','Q11','Q15'],
    'Q11': ['Q5','Q6','Q10','Q12','Q16','Q17'],
    'Q12': ['Q7','Q8','Q11','Q13','Q16','Q17'],
    'Q13': ['Q7','Q8','Q12','Q14','Q18','Q19'],
    'Q14': ['Q9','Q13','Q18','Q19'],
    'Q15': ['Q10','Q16'],
    'Q16': ['Q11','Q12','Q15','Q17'],
    'Q17': ['Q11','Q12','Q16','Q18'],
    'Q18': ['Q13','Q14','Q17','Q19'],
    'Q19': ['Q13','Q14','Q18']
}
Gc = nx.Graph(coupling_graph)

# Compute the shortest path distances for the distance matrix
distance_matrix = {}
for node1 in Gc.nodes:
    distance_matrix[node1] = {}
    for node2 in Gc.nodes:
        if node1 != node2:
            distance_matrix[node1][node2] = nx.shortest_path_length(Gc, source=node1, target=node2)
        else:
            distance_matrix[node1][node2] = 0

# Print the results
print("Dependency List:")
for qubit, dependencies in dependency_list.items():
    print(f"q{qubit}: {dependencies}")

print("\nDistance Matrix:")
for node, distances in distance_matrix.items():
    print(f"{node}:{distances}")
