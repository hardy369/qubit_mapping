import networkx as nx
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
    interaction_edges.append((qubits[0], qubits[1], first_interaction[qubit_pair]))

# Create the interaction graph (Gd)
Gd = nx.Graph()
for edge in interaction_edges:
    qubit1, qubit2, gate_number = edge
    Gd.add_edge(qubit1, qubit2, weight=gate_number)

# Find the center of the interaction graph
interaction_centers = nx.center(Gd)
interaction_center = min(interaction_centers)

# BFS traversal of the interaction graph
bfs_edges = list(nx.bfs_edges(Gd, interaction_center))
bfs_traversal = [interaction_center] + [v for u, v in bfs_edges]

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

# Find the center of the coupling graph
coupling_centers = nx.center(Gc)
coupling_center = min(coupling_centers)

# Initialize the mapping
mapping = {}
mapped_qubits = set()  # Track already mapped physical qubits

mapping[interaction_center] = coupling_center
mapped_qubits.add(coupling_center)

# BFS traversal for mapping
queue = bfs_traversal
queue.pop(0)  # Remove the interaction center

while queue:
    p = queue.pop(0)  # Get the next interaction node
    
    # Reference locations and candidate locations
    #ref_locs neighbors of current node in interaction graph which are already mapped
    #candi_locs neighbours of the mapped physical qubit(of ref locs) which are not mapped yet
    ref_locs = [neighbor for neighbor in Gd.neighbors(p) if neighbor in mapping]
    candi_locs = [neighbor for neighbor in Gc.neighbors(mapping[ref_locs[0]]) if neighbor not in mapped_qubits]

    for ref in ref_locs[1:]:
        candi_locs.sort(key=lambda x: nx.shortest_path_length(Gc, source=mapping[ref], target=x))
        candi_locs = candi_locs[:1]  # Keep only the minimal distance candidate

    if len(candi_locs) == 1:
        mapping[p] = candi_locs[0]
        mapped_qubits.add(candi_locs[0])
    else:
        # the node with the highest degree is choosen in case of a tie
        selected = max(candi_locs, key=lambda x: Gc.degree[x])
        mapping[p] = selected
        mapped_qubits.add(selected)

# Print the resulting mapping
print("Initial Mapping (π):")
for k, v in mapping.items():
    print(f"q{k} -> {v}")
