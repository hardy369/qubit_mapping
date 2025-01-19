from qiskit import QuantumCircuit
import networkx as nx
from typing import List, Dict, Tuple, Optional

class MCPESWAPOptimizer:
    def __init__(self, coupling_graph: nx.Graph, look_ahead_window: int = 5):
        self.coupling_graph = coupling_graph
        self.dist_matrix = dict(nx.all_pairs_shortest_path_length(coupling_graph))
        self.look_ahead_window = look_ahead_window
        
    def calculate_dist(self, p1: int, p2: int) -> int:
        """Calculate the nearest neighbor distance between two physical qubits."""
        return self.dist_matrix[p1][p2]
    
    def get_shortest_path(self, q1: int, q2: int, physical_mapping: Dict[int, int]) -> List[Tuple[int, int]]:
        """Get a list of logical qubit pairs along the shortest path."""
        # Get physical locations
        p1, p2 = physical_mapping[q1], physical_mapping[q2]
        
        try:
            # Get physical path
            phys_path = nx.shortest_path(self.coupling_graph, p1, p2)
            
            # Convert to logical SWAP operations
            swaps = []
            for i in range(len(phys_path) - 1):
                # Find logical qubits at these physical locations
                reverse_map = {v: k for k, v in physical_mapping.items()}
                log_q1 = reverse_map[phys_path[i]]
                log_q2 = reverse_map[phys_path[i + 1]]
                swaps.append((log_q1, log_q2))
            return swaps
        except nx.NetworkXNoPath:
            return []
    
    def apply_swap(self, mapping: Dict[int, int], swap: Tuple[int, int]) -> Dict[int, int]:
        """Apply a SWAP operation between logical qubits."""
        new_mapping = mapping.copy()
        q1, q2 = swap
        new_mapping[q1], new_mapping[q2] = new_mapping[q2], new_mapping[q1]
        return new_mapping

    def optimize_circuit(self, circuit: QuantumCircuit, initial_mapping: Dict[int, int]) -> Tuple[QuantumCircuit, Dict[int, int]]:
        """Optimize the circuit using SWAP insertion."""
        current_mapping = initial_mapping.copy()
        n_qubits = len(initial_mapping)
        
        # Create new circuit with the same number of quantum and classical registers
        new_circuit = QuantumCircuit(n_qubits, n_qubits)
        
        print("\nStarting circuit optimization...")
        
        for idx, instruction in enumerate(circuit.data):
            operation = instruction.operation
            qubits = instruction.qubits
            clbits = instruction.clbits
            
            if operation.name == 'measure':
                # Handle measurement operations with proper mapping
                qubit = qubits[0]._index
                clbit = clbits[0]._index
                mapped_qubit = current_mapping[qubit]
                new_circuit.measure(mapped_qubit, clbit)
                print(f"Added measurement on mapped qubit {mapped_qubit} -> clbit {clbit}")
                
            elif len(qubits) == 2:  # Two-qubit gate
                control = qubits[0]._index
                target = qubits[1]._index
                
                print(f"\nProcessing gate {idx}: {operation.name} {control}-{target}")
                print(f"Current mapping: {current_mapping}")
                
                # Get physical locations
                control_phys = current_mapping[control]
                target_phys = current_mapping[target]
                
                # Check if qubits are connected in the coupling map
                if not self.coupling_graph.has_edge(control_phys, target_phys):
                    print(f"Need to insert SWAPs - qubits not adjacent")
                    print(f"Physical locations: {control_phys}-{target_phys}")
                    
                    # Get SWAP path
                    swap_path = self.get_shortest_path(control, target, current_mapping)
                    if not swap_path:
                        raise ValueError(f"No valid path found between qubits {control} and {target}")
                    
                    print(f"Proposed SWAP path: {swap_path}")
                    
                    # Apply necessary SWAPs
                    for swap in swap_path:
                        q1, q2 = swap
                        phys_q1 = current_mapping[q1]
                        phys_q2 = current_mapping[q2]
                        new_circuit.swap(phys_q1, phys_q2)
                        current_mapping = self.apply_swap(current_mapping, swap)
                        print(f"Applied SWAP {swap}, new mapping: {current_mapping}")
                
                # Add the two-qubit gate with updated mapping
                mapped_control = current_mapping[control]
                mapped_target = current_mapping[target]
                
                # Check if the gate needs to be reversed based on coupling map
                if self.coupling_graph.has_edge(mapped_control, mapped_target):
                    if operation.name == 'cx':
                        new_circuit.cx(mapped_control, mapped_target)
                    else:
                        new_circuit.append(operation, [mapped_control, mapped_target], clbits)
                elif self.coupling_graph.has_edge(mapped_target, mapped_control):
                    # If needed, add extra gates to implement the reversed operation
                    if operation.name == 'cx':
                        new_circuit.h(mapped_control)
                        new_circuit.h(mapped_target)
                        new_circuit.cx(mapped_target, mapped_control)
                        new_circuit.h(mapped_control)
                        new_circuit.h(mapped_target)
                    else:
                        raise ValueError(f"Unsupported gate {operation.name} for reverse implementation")
                else:
                    raise ValueError(f"Unable to implement gate between qubits {mapped_control} and {mapped_target}")
                
                print(f"Added {operation.name} gate {mapped_control}-{mapped_target}")
                
            else:  # Single-qubit gate
                qubit = qubits[0]._index
                mapped_qubit = current_mapping[qubit]
                if operation.name == 'h':
                    new_circuit.h(mapped_qubit)
                elif operation.name == 'x':
                    new_circuit.x(mapped_qubit)
                elif operation.name == 'measure':
                    new_circuit.measure(mapped_qubit, clbits[0]._index)
                else:
                    new_circuit.append(operation, [mapped_qubit], clbits)
                print(f"Added single-qubit gate on mapped qubit {mapped_qubit}")
        
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
    
    # Create the coupling graph
    coupling_graph = nx.Graph()
    for node, neighbors in coupling_dict.items():
        node_num = int(node[1:])
        for neighbor in neighbors:
            neighbor_num = int(neighbor[1:])
            coupling_graph.add_edge(node_num, neighbor_num)

    # Initial mapping
    initial_mapping = {i: i for i in range(6)}
    
    # Create example circuit
    circuit = QuantumCircuit(6, 6)  # Added classical bits
    circuit.cx(0, 2)
    circuit.cx(5, 2)
    circuit.cx(0, 5)
    circuit.cx(4, 0)
    circuit.cx(0, 3)
    circuit.cx(5, 0)
    circuit.cx(3, 1)
    
    # Add measurements one by one instead of measure_all()
    for i in range(6):
        circuit.measure(i, i)
    
    print("Coupling graph edges:", coupling_graph.edges())
    print("Initial mapping:", initial_mapping)
    
    # Optimize circuit
    optimizer = MCPESWAPOptimizer(coupling_graph)
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
