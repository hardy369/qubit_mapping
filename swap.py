import networkx as nx
from qiskit import QuantumCircuit
from qiskit.converters import circuit_to_dag
from collections import defaultdict, deque
# define a gate
class Gate:
    def __init__(self, control, target):
        self.control = control
        self.target = target

class DependenceList:
    def __init__(self):
        self.gates = deque()
    
    def push_back(self, gate):
        self.gates.append(gate)
    
    def pop_front(self):
        return self.gates.popleft() if self.gates else None
    
    def head(self):
        return self.gates[0] if self.gates else None

def calculate_mcpe_cost(swap, active_gates, current_mapping, distances):
    p1, p2 = swap
    score = 0
    
    temp_mapping = current_mapping.copy()
    for q in temp_mapping:
        if temp_mapping[q] == p1:
            temp_mapping[q] = p2
        elif temp_mapping[q] == p2:
            temp_mapping[q] = p1
    
    for gate in active_gates:
        # old_dist: before swap the distance between physical qubits 
        old_dist = distances[current_mapping[gate.control]][current_mapping[gate.target]]
          # new_dist: after swap the distance between physical qubits 
        new_dist = distances[temp_mapping[gate.control]][temp_mapping[gate.target]]
        # score denotes the mcpe of swap
        score += old_dist - new_dist
    return score

def check_connectivity(gate, current_mapping, coupling_graph):
    pos1 = current_mapping[gate.control]
    pos2 = current_mapping[gate.target]
    node1 = f'Q{pos1}'
    node2 = f'Q{pos2}'
    # returns 1 if there is an edge between node 1 and node 2 in the coupling graph. else returns 0.  
    return node2 in coupling_graph[node1]

def get_reverse_mapping(mapping):
    return {v: k for k, v in mapping.items()}

def schedule_quantum_circuit(coupling_graph, initial_mapping, num_qubits=20):
    #initialised the final circuit
    final_cir = QuantumCircuit(6)
    current_mapping = initial_mapping.copy()
    #fron_list : tracks gates waiting to be scheduled
    #act_list : tracks gates currently being scheduled
    #frozen : tracks logical qubits which have been processed 0 means unfrozen 1 means frozen
    fron_list = []
    act_list = []
    frozen = {q: False for q in range(num_qubits)}
    executed_gates = []  # Track executed gates order
    
    #  dependence lists
    dlist = defaultdict(DependenceList)
    gates = [(0, 2), (5, 2), (0, 5), (4, 0), (0, 3), (5, 0), (3, 1)]
    for c, t in gates:
        gate = Gate(c, t)
        dlist[c].push_back(gate)
        dlist[t].push_back(gate)
    
    # Computes distances between nodes in coupling graph 
    distances = [[float('inf')] * num_qubits for _ in range(num_qubits)]
    for node, neighbors in coupling_graph.items():
        i = int(node[1:])
        distances[i][i] = 0
        for neighbor in neighbors:
            j = int(neighbor[1:])
            distances[i][j] = distances[j][i] = 1
    
    # Stores operations for later conversion
    operations = []
    
    while True:
        
        for q in range(6):
            if not frozen[q]:
                gate = dlist[q].head()
                if gate:
                    if gate in fron_list:
                        fron_list.remove(gate)
                        if gate not in act_list:
                            act_list.append(gate)
                    else:
                        if gate not in fron_list:
                            fron_list.append(gate)
                    frozen[q] = True
        
        # Execute gates that are satisfying connectivity constraint
        gates_to_remove = []
        for gate in act_list:
            if check_connectivity(gate, current_mapping, coupling_graph):
                gates_to_remove.append(gate)
                dlist[gate.control].pop_front()
                dlist[gate.target].pop_front()
                # Store gate operation with logical qubits
                operations.append(('cx', gate.control, gate.target))
                executed_gates.append(gate)
                frozen[gate.control] = False
                frozen[gate.target] = False
        
        for gate in gates_to_remove:
            act_list.remove(gate)
        # repeat till fron_list is empty
        
            
        # SWAP selection
        # Now act_list containes gates which donot satisfy the connectivity constraint.
        if act_list:
            candi_list = []
        #candi_list contains SWAPs having positive effect on at least one active gate;    
            for node, neighbors in coupling_graph.items():
                i = int(node[1:])
                for neighbor in neighbors:
                    j = int(neighbor[1:])
                    if i < j:
                        candi_list.append((i, j))
            # mcpe_costs contains mcpe of all the swaps in candi_list
            mcpe_costs = {}
            for swap in candi_list:
                cost = calculate_mcpe_cost(swap, act_list, current_mapping, distances)
                if cost > 0:
                    mcpe_costs[swap] = cost
            
            if mcpe_costs:
                best_swap = max(mcpe_costs.items(), key=lambda x: x[1])[0]
                p1, p2 = best_swap
                
                # Store SWAP operation with logical qubits
                rev_mapping = get_reverse_mapping(current_mapping)
                if p1 in rev_mapping and p2 in rev_mapping:
                    operations.append(('swap', rev_mapping[p1], rev_mapping[p2]))
                
                # Update mapping implementing that swap
                for q in current_mapping:
                    if current_mapping[q] == p1:
                        current_mapping[q] = p2
                    elif current_mapping[q] == p2:
                        current_mapping[q] = p1
      if  not fron_list:
            break
    # Create final circuit with logical qubits
    final_logical_cir = QuantumCircuit(6)
    for op_type, q1, q2 in operations:
        if op_type == 'cx':
            final_logical_cir.cx(q1, q2)
        else:  # swap
            final_logical_cir.swap(q1, q2)
    
    return final_logical_cir
#input coupling graph and initial mapping
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
    'Q9': ['Q3','Q4','Q8','Q14'],
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

initial_mapping = {0: 1, 2: 6, 5: 2, 4: 7, 3: 0, 1: 5}  

final_circuit = schedule_quantum_circuit(coupling_graph, initial_mapping)
print(final_circuit)
