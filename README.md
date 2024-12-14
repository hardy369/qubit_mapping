# Qubit Mapping Algorithms

This repository contains the implementation of algorithms for the qubit mapping problem, inspired by the research paper **"A Dynamic Look-Ahead Heuristic for the Qubit Mapping Problem of NISQ Computers."**

---

## **Installation and Setup**

To run the code:
1. **Install Qiskit**: Follow the official IBM Qiskit installation guide available at [Qiskit Installation Documentation](https://docs.quantum.ibm.com/guides/install-qiskit).
2. **Install Python**: Ensure that Python is installed on your computer.
3. **Run the Code**: Execute the provided Python files to run the algorithms.

---

## **File Descriptions**

### **gd.py**
This file contains code to:
- Extract the interaction graph from a quantum circuit.
- Identify centers of interaction within the interaction graph.
- Handle the coupling graph representation and also the center of the coupling graph.

  
### **ig.py**
This file prints the interaction graph from the quantum circuit.

### **im.py**
This file implements the initial qubit mapping algorithm, which includes the expansion from the center of the interaction graph.

### **dl_dm.py**
This file prints the Dependence list and Distance matrix 

---

## **How the Code Works**

### **1. Interaction Graph (Gd):**
The interaction graph represents the logical connections between qubits in the quantum circuit.
- The quantum circuit is first converted into a Directed Acyclic Graph (DAG).
- From the DAG, an interaction graph is constructed where:
  - **Nodes** represent logical qubits.
  - **Edges** represent interactions between qubits, weighted by the gate order in the circuit.
 
  
![image](https://github.com/user-attachments/assets/349e75bb-ca78-4b34-a3cf-d825a35c5cb5)


### **2. Coupling Graph (Gc):**
The coupling graph represents the physical constraints of a quantum computer's qubits.
- **Nodes** represent physical qubits.
- **Edges** represent possible connections between physical qubits.

### **3. Mapping Algorithm:**
The mapping algorithm ensures an optimal assignment of logical qubits to physical qubits, considering the constraints of the coupling graph.

#### Steps:
1. Identify the **center** of the interaction graph (interaction_center) and map it to the **center** of the coupling graph (coupling_center).
2. Perform a Breadth-First Search (BFS) traversal of the interaction graph to determine the order of mapping.
3. Select candidate physical qubits for mapping based on:
   - **Proximity** to already mapped qubits.
   - **Degree** (number of neighbors) of the candidate physical qubit, used as a tie-breaker.

### **4. Output:**
The output of the algorithm is a mapping (π) that assigns logical qubits to physical qubits efficiently.

---
