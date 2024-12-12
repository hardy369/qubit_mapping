README: Dynamic Look-Ahead Heuristic for Initial Qubit Mapping

Introduction
This script implements a dynamic look-ahead heuristic for initial qubit mapping in quantum circuits. It uses an interaction graph derived from the quantum circuit and maps it to a coupling graph (representing hardware constraints) to minimize the number of SWAP gates needed during execution.

How the Code Works

##Interaction Graph (Gd):
i)The circuit is converted into a Directed Acyclic Graph (DAG).
ii)From the DAG, an interaction graph is constructed where:
  Nodes represent qubits.
  Edges represent interactions between qubits, weighted by the gate order.

##Coupling Graph (Gc):
i)A predefined graph models the physical constraints of a quantum computer's qubits.
ii)Nodes represent physical qubits, and edges represent possible connections.

##Mapping Algorithm:
i)The center of the interaction graph (interaction_center) is mapped to the center of the coupling graph (coupling_center).
ii)A Breadth-First Search (BFS) traversal of the interaction graph determines the mapping order.
iii)Candidate physical qubits are selected for mapping based on:
  Proximity to already mapped qubits.
  Degree (number of neighbors) as a tie-breaker.

##Output:
A mapping (π) that assigns logical qubits to physical qubits.
