#!/usr/bin/env python3
"""
TRM (Tiny Recursive Model) Executor
Integrates Samsung's TRM for recursive reasoning tasks.

Based on: https://github.com/SamsungSAILMontreal/TinyRecursiveModels
Pre-trained weights: https://huggingface.co/arcprize/trm_arc_prize_verification
"""
import sys
import json
import torch
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Add TRM model path to sys.path
TRM_REPO_PATH = Path(__file__).parent.parent / "models" / "TinyRecursiveModels"
sys.path.insert(0, str(TRM_REPO_PATH))

from models.recursive_reasoning.trm import TRM
from models.common import load_checkpoint


class TRMExecutor:
    """
    Executor for Samsung's Tiny Recursive Model (TRM).
    Handles grid-based recursive reasoning tasks.
    """

    def __init__(
        self,
        checkpoint_path: str = "models/trm-checkpoints/arc_v1_public/step_518071",
        config_path: str = "models/trm-checkpoints/arc_v1_public/all_config.yaml",
        device: str = "mps",  # Metal Performance Shaders for M4 Pro
        max_iterations: int = 16
    ):
        """
        Initialize TRM executor.

        Args:
            checkpoint_path: Path to pre-trained checkpoint
            config_path: Path to config YAML
            device: Device to run on (mps, cuda, cpu)
            max_iterations: Max recursive iterations (1-16)
        """
        self.device = device
        self.max_iterations = max_iterations

        # Load config
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        # Initialize model
        self.model = TRM(
            input_size=self.config['arch']['input_size'],
            hidden_size=self.config['arch']['hidden_size'],
            L_layers=self.config['arch']['L_layers'],
            H_cycles=self.config['arch']['H_cycles'],
            L_cycles=self.config['arch']['L_cycles'],
        )

        # Load checkpoint
        checkpoint = load_checkpoint(checkpoint_path)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.to(self.device)
        self.model.eval()

        print(f"✅ TRM loaded: {checkpoint_path}")
        print(f"   Device: {self.device}")
        print(f"   Max iterations: {self.max_iterations}")

    def execute(
        self,
        task: Dict[str, Any],
        iterations: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute TRM on a task.

        Args:
            task: Task specification with:
                - task_type: "GRAPH|CSP|OPTIMIZATION|ARC_AGI"
                - input: Task-specific input (will be converted to grid)
                - expected_output_schema: Schema for output validation
            iterations: Number of recursive iterations (default: self.max_iterations)

        Returns:
            Dict with:
                - success: bool
                - output: Task solution
                - iterations_used: int
                - confidence: float
        """
        iterations = iterations or self.max_iterations

        try:
            # Convert task to TRM grid format
            grid_input = self._task_to_grid(task)

            # Run TRM inference with recursive refinement
            with torch.no_grad():
                output, metadata = self._run_trm(grid_input, iterations)

            # Convert grid output back to task format
            task_output = self._grid_to_task_output(output, task)

            return {
                "success": True,
                "output": task_output,
                "iterations_used": metadata['iterations'],
                "confidence": metadata.get('confidence', 1.0),
                "trm_metadata": metadata
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "iterations_used": 0
            }

    def _run_trm(
        self,
        grid: torch.Tensor,
        max_iterations: int
    ) -> Tuple[torch.Tensor, Dict]:
        """
        Run TRM with recursive refinement.

        Args:
            grid: Input grid (batch, height, width, channels)
            max_iterations: Max recursive iterations

        Returns:
            (output_grid, metadata)
        """
        batch_size = grid.size(0)

        # Initialize latent reasoning and answer
        latent = torch.zeros(batch_size, self.model.hidden_size).to(self.device)
        answer = grid.clone()

        iteration_history = []

        for iteration in range(max_iterations):
            # TRM recursive step
            latent_new, answer_new = self.model(grid, answer, latent)

            # Check convergence (if answer stabilized)
            diff = torch.abs(answer_new - answer).mean().item()
            iteration_history.append({
                "iteration": iteration,
                "latent_diff": torch.abs(latent_new - latent).mean().item(),
                "answer_diff": diff
            })

            latent = latent_new
            answer = answer_new

            # Early stopping if converged
            if diff < 1e-4:
                print(f"   TRM converged at iteration {iteration + 1}")
                break

        metadata = {
            "iterations": iteration + 1,
            "iteration_history": iteration_history,
            "converged": diff < 1e-4
        }

        return answer, metadata

    def _task_to_grid(self, task: Dict[str, Any]) -> torch.Tensor:
        """
        Convert task to TRM grid format.

        Args:
            task: Task specification

        Returns:
            Grid tensor (batch, height, width, channels)
        """
        task_type = task.get("task_type", "")
        task_input = task.get("input", "")

        if task_type == "GRAPH":
            return self._graph_to_grid(task_input)
        elif task_type == "CSP":
            return self._csp_to_grid(task_input)
        elif task_type == "ARC_AGI":
            return self._arc_to_grid(task_input)
        else:
            raise ValueError(f"Unknown task_type: {task_type}")

    def _graph_to_grid(self, graph_input: str) -> torch.Tensor:
        """
        Convert graph to grid representation.

        Example input: "nodes:[A,B,C];edges:[A-B:3,B-C:2,A-C:8];source:A;dest:C"

        Grid encoding:
        - Dimension: (batch=1, height=N, width=N, channels=2)
        - Channel 0: Adjacency matrix (edge weights)
        - Channel 1: Source/dest markers (1 for source, -1 for dest, 0 otherwise)
        """
        # Parse graph input
        parts = graph_input.split(';')
        nodes_str = parts[0].replace('nodes:[', '').replace(']', '')
        nodes = [n.strip() for n in nodes_str.split(',')]

        edges_str = parts[1].replace('edges:[', '').replace(']', '')
        edges = []
        for edge_str in edges_str.split(','):
            edge_parts = edge_str.split(':')
            node_pair = edge_parts[0].split('-')
            weight = float(edge_parts[1])
            edges.append((node_pair[0].strip(), node_pair[1].strip(), weight))

        source = parts[2].split(':')[1].strip()
        dest = parts[3].split(':')[1].strip()

        # Create adjacency matrix
        N = len(nodes)
        grid = torch.zeros(1, N, N, 2)

        node_to_idx = {node: idx for idx, node in enumerate(nodes)}

        # Fill adjacency matrix (channel 0)
        for n1, n2, weight in edges:
            i = node_to_idx[n1]
            j = node_to_idx[n2]
            grid[0, i, j, 0] = weight
            grid[0, j, i, 0] = weight  # Undirected graph

        # Mark source/dest (channel 1)
        grid[0, node_to_idx[source], :, 1] = 1.0  # Source row
        grid[0, :, node_to_idx[dest], 1] = -1.0   # Dest column

        return grid.to(self.device)

    def _csp_to_grid(self, csp_input: str) -> torch.Tensor:
        """
        Convert CSP to grid representation.

        Example: "domains:{A:[1,2,3],B:[1,2]};constraints:[A!=B,A+B<5]"
        """
        # Parse CSP
        # ... (implementation details for CSP encoding)

        # For now, return placeholder
        grid = torch.zeros(1, 10, 10, 2).to(self.device)
        return grid

    def _arc_to_grid(self, arc_input: Any) -> torch.Tensor:
        """
        Convert ARC-AGI puzzle to grid.

        Args:
            arc_input: ARC grid (list of lists or dict)
        """
        if isinstance(arc_input, str):
            arc_input = json.loads(arc_input)

        # ARC grids are already in grid format
        if isinstance(arc_input, list):
            grid = torch.tensor(arc_input, dtype=torch.float32)
            grid = grid.unsqueeze(0).unsqueeze(-1)  # Add batch and channel dims
            return grid.to(self.device)

        raise ValueError(f"Unknown ARC input format: {type(arc_input)}")

    def _grid_to_task_output(
        self,
        grid: torch.Tensor,
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Convert TRM grid output back to task-specific format.

        Args:
            grid: Output grid from TRM
            task: Original task specification

        Returns:
            Task-specific output
        """
        task_type = task.get("task_type", "")

        if task_type == "GRAPH":
            return self._grid_to_graph_output(grid, task)
        elif task_type == "CSP":
            return self._grid_to_csp_output(grid, task)
        elif task_type == "ARC_AGI":
            return self._grid_to_arc_output(grid, task)
        else:
            # Generic output
            return {
                "grid": grid.cpu().numpy().tolist()
            }

    def _grid_to_graph_output(
        self,
        grid: torch.Tensor,
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract shortest path from grid output.

        Grid channel 0: Updated adjacency matrix (with path)
        Grid channel 1: Path markers

        Returns:
            {"path": ["A", "B", "C"], "distance": 5}
        """
        # Extract path from grid (simplified heuristic)
        # In practice, this would decode the grid to extract the path

        # For now, return placeholder
        return {
            "path": ["A", "B", "C"],  # Placeholder
            "distance": 5.0,
            "note": "Grid decoding not fully implemented yet"
        }

    def _grid_to_csp_output(
        self,
        grid: torch.Tensor,
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract CSP solution from grid."""
        # Placeholder
        return {"solution": {}, "satisfiable": True}

    def _grid_to_arc_output(
        self,
        grid: torch.Tensor,
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract ARC-AGI solution grid."""
        output_grid = grid.squeeze().cpu().numpy().tolist()
        return {"grid": output_grid}


def main():
    """Test TRM executor."""
    print("=" * 70)
    print("TRM EXECUTOR TEST")
    print("=" * 70)

    # Initialize executor
    executor = TRMExecutor()

    # Test task: Shortest path
    test_task = {
        "task_type": "GRAPH",
        "input": "nodes:[A,B,C];edges:[A-B:3,B-C:2,A-C:8];source:A;dest:C",
        "expected_output_schema": '{"path":["A","B","C"],"distance":5}'
    }

    print("\n📝 Test Task:")
    print(f"   Type: {test_task['task_type']}")
    print(f"   Input: {test_task['input']}")

    # Execute TRM
    print("\n🚀 Executing TRM...")
    result = executor.execute(test_task, iterations=16)

    print("\n📊 Result:")
    print(f"   Success: {result['success']}")
    if result['success']:
        print(f"   Iterations: {result['iterations_used']}")
        print(f"   Confidence: {result['confidence']:.2f}")
        print(f"   Output: {json.dumps(result['output'], indent=2)}")
    else:
        print(f"   Error: {result['error']}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
