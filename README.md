This repository contains implementation of algorithms of qubit mapping.


We are implementing the algorithms based on the research paper **A dynamic look-ahead heuristic for the qubit mapping problem of NISQ computers**.

**To run the code :**
Install qiskit and its environment using the IBM documentation :https://docs.quantum.ibm.com/guides/install-qiskit
also make sure you have python installed on your computer.
run the  python files.

**gd:** This file contains the code for interaction graph from the quantum circuit and obtaining centers of interaction and coupling graphs.


**im:** This file implements the initial mapping algorithm (expansion from center).

**How the Code Works**

**Interaction Graph (Gd):**
i)The circuit is converted into a Directed Acyclic Graph (DAG).
ii)From the DAG, an interaction graph is constructed where:
  Nodes represent qubits.
  Edges represent interactions between qubits, weighted by the gate order.

**Coupling Graph (Gc):**
i)A predefined graph models the physical constraints of a quantum computer's qubits.
ii)Nodes represent physical qubits, and edges represent possible connections.

**Mapping Algorithm:**
i)The center of the interaction graph (interaction_center) is mapped to the center of the coupling graph (coupling_center).
ii)A Breadth-First Search (BFS) traversal of the interaction graph determines the mapping order.
iii)Candidate physical qubits are selected for mapping based on:
  Proximity to already mapped qubits.
  Degree (number of neighbors) as a tie-breaker.

**Output:**
A mapping (π) that assigns logical qubits to physical qubits.
