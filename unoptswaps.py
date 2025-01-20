from qiskit import QuantumCircuit
import networkx as nx
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
import itertools

class MCPEOptimizer:
    def __init__(self, coupling_graph: nx.Graph):
        self.coupling_graph = coupling_graph
        self.dist_matrix = dict(nx.all_pairs_shortest_path_length(coupling_graph))
        
    def calculate_dist(self, p1: int, p2: int) -> int:
        """Calculate the nearest neighbor distance between two physical qubits."""
        return self.dist_matrix[p1][p2]
    
    def calculate_mcpe(self, circuit_slice: List[Tuple[int, int]], swap_qubits: Tuple[int, int], 
                      current_mapping: Dict[int, int]) -> float:
        """Calculate MCPE value for a potential SWAP."""
        q1, q2 = swap_qubits
        mcpe_value = 0
        
        # Create new mapping after potential swap
        new_mapping = current_mapping.copy()
        new_mapping[q1], new_mapping[q2] = new_mapping[q2], new_mapping[q1]
        
        # Calculate effect on each gate in look-ahead window
        for idx, (control, target) in enumerate(circuit_slice):
            # Calculate distances before and after SWAP
            old_dist = self.calculate_dist(current_mapping[control], current_mapping[target])
            new_dist = self.calculate_dist(new_mapping[control], new_mapping[target])
            effect = (old_dist - new_dist) 
            if effect>0:
                effect=1
            # Add to MCPE value
            mcpe_value += effect
            
            # Stop if we find a gate with no positive effect
            if mcpe_value <= 0:
                break
                
        return mcpe_value
    
    def get_affected_gates(self, circuit_data: List, start_idx: int, swap_qubits: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get list of 2-qubit gates affected by the SWAP."""
        affected_gates = []
        q1, q2 = swap_qubits
        
        for inst in circuit_data[start_idx:]:
            if len(inst.qubits) == 2:
                control = inst.qubits[0]._index
                target = inst.qubits[1]._index
                if control in (q1, q2) or target in (q1, q2):
                    affected_gates.append((control, target))
                    
                # Stop when we find a gate that's not affected
                if control not in (q1, q2) and target not in (q1, q2):
                    break
                    
        return affected_gates
    
    def find_best_swap(self, circuit_data: List, current_idx: int, 
                      current_mapping: Dict[int, int]) -> Optional[Tuple[int, int]]:
        """Find the best SWAP operation using MCPE heuristic."""
        best_swap = None
        best_mcpe = float('-inf')
        
        # Get all possible SWAP candidates from coupling graph
        swap_candidates = list(self.coupling_graph.edges())
        
        for edge in swap_candidates:
            # Get logical qubits for this edge
            reverse_map = {v: k for k, v in current_mapping.items()}
            q1 = reverse_map[edge[0]]
            q2 = reverse_map[edge[1]]
            
            # Get affected gates for this SWAP
            affected_gates = self.get_affected_gates(circuit_data, current_idx, (q1, q2))
            
            if affected_gates:
                # Calculate MCPE value
                mcpe = self.calculate_mcpe(affected_gates, (q1, q2), current_mapping)
                
                # Update best SWAP if this one is better
                if mcpe > best_mcpe:
                    best_mcpe = mcpe
                    best_swap = (q1, q2)
        
        return best_swap

    def optimize_circuit(self, circuit: QuantumCircuit, initial_mapping: Dict[int, int]) -> Tuple[QuantumCircuit, Dict[int, int]]:
        """Optimize circuit using MCPE-based SWAP insertion."""
        current_mapping = initial_mapping.copy()
        n_qubits = len(initial_mapping)
        new_circuit = QuantumCircuit(n_qubits)
        
        print("\nStarting MCPE-based circuit optimization...")
        
        idx = 0
        while idx < len(circuit.data):
            instruction = circuit.data[idx]
            operation = instruction.operation
            qubits = instruction.qubits
            
            if len(qubits) == 2:
                control = qubits[0]._index
                target = qubits[1]._index
                mapped_control = current_mapping[control]
                mapped_target = current_mapping[target]
                
                # Check if qubits are adjacent
                if not self.coupling_graph.has_edge(mapped_control, mapped_target):
                    # Find best SWAP
                    best_swap = self.find_best_swap(circuit.data, idx, current_mapping)
                    
                    if best_swap:
                        q1, q2 = best_swap
                        phys_q1 = current_mapping[q1]
                        phys_q2 = current_mapping[q2]
                        new_circuit.swap(phys_q1, phys_q2)
                        current_mapping[q1], current_mapping[q2] = current_mapping[q2], current_mapping[q1]
                        print(f"Applied MCPE-selected SWAP {best_swap}, new mapping: {current_mapping}")
                        continue
                
                # Apply the gate if possible
                if self.coupling_graph.has_edge(mapped_control, mapped_target):
                    new_circuit.append(operation, [mapped_control, mapped_target])
                elif self.coupling_graph.has_edge(mapped_target, mapped_control):
                    if operation.name == 'cx':
                        new_circuit.h(mapped_control)
                        new_circuit.h(mapped_target)
                        new_circuit.cx(mapped_target, mapped_control)
                        new_circuit.h(mapped_control)
                        new_circuit.h(mapped_target)
                    else:
                        raise ValueError(f"Unsupported gate {operation.name} for reverse implementation")
            else:
                # Single-qubit gate
                qubit = qubits[0]._index
                mapped_qubit = current_mapping[qubit]
                new_circuit.append(operation, [mapped_qubit])
            
            idx += 1
        
        return new_circuit, current_mapping

def main():
    # Create the coupling graph
    coupling_dict = {
        'Q0': ['Q1','Q5'],
        'Q1': ['Q0','Q2'],
        'Q2': ['Q1','Q3'],
        'Q3': ['Q2','Q4'],
        'Q4': ['Q3'],
        'Q5': ['Q0']
    }
    
    coupling_graph = nx.Graph()
    for node, neighbors in coupling_dict.items():
        node_num = int(node[1:])
        for neighbor in neighbors:
            neighbor_num = int(neighbor[1:])
            coupling_graph.add_edge(node_num, neighbor_num)

    # Initial mapping
    initial_mapping = {i: i for i in range(6)}
    
    # Create example circuit
    circuit = QuantumCircuit(6)
    circuit.cx(0, 2)
    circuit.cx(5, 2)
    circuit.cx(0, 5)
    circuit.cx(4, 0)
    circuit.cx(0, 3)
    circuit.cx(5, 0)
    circuit.cx(3, 1)
    
    print("Coupling graph edges:", coupling_graph.edges())
    print("Initial mapping:", initial_mapping)
    
    # Optimize circuit using MCPE
    optimizer = MCPEOptimizer(coupling_graph)
    optimized_circuit, final_mapping = optimizer.optimize_circuit(circuit, initial_mapping)
    
    print("\nFinal Results:")
    print("Initial Mapping:", initial_mapping)
    print("Final Mapping:", final_mapping)
    print("\nOriginal Circuit:")
    print(circuit)
    print("\nOptimized Circuit (with SWAP gates):")
    print(optimized_circuit)
    print("\nNumber of additional SWAP gates:", 
          sum(1 for inst in optimized_circuit.data if inst.operation.name == 'swap'))

if __name__ == "__main__":
    main()
