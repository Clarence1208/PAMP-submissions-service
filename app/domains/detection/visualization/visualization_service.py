"""
Visualization Service
Handles React Flow AST generation and code similarity visualization.
"""

import logging
from typing import Any, Dict, List

from app.domains.detection.similarity_detection_service import SimilarityDetectionService

logger = logging.getLogger(__name__)


class VisualizationService:
    def __init__(self):
        """Initialize the visualization service."""
        self.similarity_service = SimilarityDetectionService()

    def generate_react_flow_ast(
        self,
        tokens1: List[Dict[str, Any]],
        tokens2: List[Dict[str, Any]],
        source1: str = "",
        source2: str = "",
        file1_name: str = "",
        file2_name: str = "",
        layout_type: str = "elk",
    ) -> Dict[str, Any]:
        """
        Generate optimized React Flow JSON representation with minimal payload.
        Focused on essential data for visualization without excessive styling or layout configs.

        Args:
            tokens1: First set of tokens
            tokens2: Second set of tokens
            source1: Original source code of first file
            source2: Original source code of second file
            file1_name: Name of the first file
            file2_name: Name of the second file
            layout_type: Layout algorithm to use (elk, dagre, etc.)
        """
        # First detect shared code blocks to see if we should include these files
        shared_blocks_result = self.similarity_service.detect_shared_code_blocks(
            tokens1, tokens2, source1, source2, file1_name, file2_name
        )

        # If no similarities detected, return empty structure
        if shared_blocks_result["total_shared_blocks"] == 0:
            return {
                "nodes": [],
                "edges": [],
                "has_similarity": False,
                "message": "No similarities detected between files",
            }

        # Generate flow representation for both files
        nodes = []
        edges = []
        node_id_counter = 0

        # File 1 flow - minimal layout config
        file1_nodes, file1_edges, node_id_counter = self._generate_optimized_file_nodes(
            tokens1, source1, file1_name, "file1", node_id_counter, shared_blocks_result["shared_blocks"]
        )

        # File 2 flow - minimal layout config
        file2_nodes, file2_edges, node_id_counter = self._generate_optimized_file_nodes(
            tokens2, source2, file2_name, "file2", node_id_counter, shared_blocks_result["shared_blocks"]
        )

        # Combine nodes and edges
        nodes.extend(file1_nodes)
        nodes.extend(file2_nodes)
        edges.extend(file1_edges)
        edges.extend(file2_edges)

        # Add similarity connection edges between similar functions
        similarity_edges = self._generate_similarity_edges(shared_blocks_result["shared_blocks"], nodes)
        edges.extend(similarity_edges)

        # Return optimized structure - removed excessive styling and layout configs
        return {
            "nodes": nodes,
            "edges": edges,
            "has_similarity": True,
            "analysis_metadata": {
                "total_similarities": shared_blocks_result["total_shared_blocks"],
                "average_similarity": shared_blocks_result["average_similarity"],
                "algorithm": "elk_layered",
                "analysis_version": "2.1.0",
            },
            "file_metadata": {
                "file1": {"name": file1_name, "functions": shared_blocks_result["functions_file1"]},
                "file2": {"name": file2_name, "functions": shared_blocks_result["functions_file2"]},
            },
        }

    def _generate_optimized_file_nodes(
        self,
        tokens: List[Dict[str, Any]],
        source_code: str,
        filename: str,
        file_prefix: str,
        node_id_counter: int,
        shared_blocks: List[Dict],
    ) -> tuple:
        """Generate ultra-lightweight React Flow nodes - no positions (ELK overwrites), no styling (frontend handles)."""
        nodes = []
        edges = []

        # Extract functions and imports using similarity service
        functions = self.similarity_service._extract_functions_with_positions(tokens, source_code)
        imports = self._extract_imports(tokens, source_code)

        # Create file subflow container - absolutely minimal data
        file_node_id = f"{file_prefix}_root"
        file_subflow = {
            "id": file_node_id,
            "type": "group",
            "data": {
                "label": f"📁 {filename}",
                "type": "file_subflow",
                "filename": filename,
                "functions_count": len(functions),
                "imports_count": len(imports),
            },
        }
        nodes.append(file_subflow)

        # Add imports group - no position (ELK will calculate)
        if imports:
            import_group_id = f"{file_prefix}_imports_group"
            import_node = {
                "id": import_group_id,
                "type": "default",
                "data": {
                    "label": f"📦 Imports ({len(imports)})",
                    "type": "import_group",
                    "imports": [imp["module"] for imp in imports],
                },
                "parentNode": file_node_id,
            }
            nodes.append(import_node)

        # Group functions by similarity
        similar_functions = []
        regular_functions = []

        for func_name, func_data in functions.items():
            similar_block = self._find_similarity_for_function(func_name, shared_blocks, file_prefix)
            if similar_block:
                similar_functions.append((func_name, func_data, similar_block))
            else:
                regular_functions.append((func_name, func_data, None))

        # Add similar functions with complete source code content - no position data
        for i, (func_name, func_data, similar_block) in enumerate(similar_functions):
            func_node_id = f"{file_prefix}_{func_name}"

            # CRITICAL: Include complete source code content for comparison dialog
            function_node = {
                "id": func_node_id,
                "type": "default",
                "data": {
                    "label": f"⚡ {func_data.get('function_name', 'unknown')} ({similar_block['similarity_score']:.1%})",
                    "type": "function",
                    "function_name": func_data.get("function_name", "unknown"),
                    "start_line": func_data.get("start_line", 0),
                    "end_line": func_data.get("end_line", 0),
                    "has_similarity": True,
                    "similarity_score": similar_block["similarity_score"],
                    "similarity_target": similar_block.get(
                        "file2_function" if file_prefix == "file1" else "file1_function"
                    ),
                    # CRITICAL: Full source code content for comparison dialog
                    "source_code": {
                        "file1_code": similar_block.get("file1_code_block", ""),
                        "file2_code": similar_block.get("file2_code_block", ""),
                    },
                    "line_numbers": {
                        "file1": {
                            "start": similar_block.get("file1_start_line", 0),
                            "end": similar_block.get("file1_end_line", 0),
                        },
                        "file2": {
                            "start": similar_block.get("file2_start_line", 0),
                            "end": similar_block.get("file2_end_line", 0),
                        },
                    },
                    "similarity_details": {
                        "algorithm_used": "ast_similarity_v2",
                        "similarity_type": "structural",
                        "confidence_level": similar_block["similarity_score"],
                        "common_patterns": similar_block.get("common_patterns", []),
                    },
                },
                "parentNode": file_node_id,
            }
            nodes.append(function_node)

        # Add regular functions - minimal data, no position
        for i, (func_name, func_data, _) in enumerate(regular_functions):
            func_node_id = f"{file_prefix}_{func_name}"

            function_node = {
                "id": func_node_id,
                "type": "default",
                "data": {
                    "label": f"⚙️ {func_data.get('function_name', 'unknown')}",
                    "type": "function",
                    "function_name": func_data.get("function_name", "unknown"),
                    "start_line": func_data.get("start_line", 0),
                    "end_line": func_data.get("end_line", 0),
                    "has_similarity": False,
                    "similarity_score": 0,
                },
                "parentNode": file_node_id,
            }
            nodes.append(function_node)

        # Generate function call edges - clean without styling
        call_edges = self._analyze_function_calls(tokens, source_code, functions, file_prefix)
        edges.extend(call_edges)

        return nodes, edges, node_id_counter

    def _analyze_function_calls(
        self, tokens: List[Dict[str, Any]], source_code: str, functions: Dict, file_prefix: str
    ) -> List[Dict]:
        """Analyze function calls and create clean call edges - no styling (frontend handles with CSS)."""
        call_edges = []

        # Extract function names for reference
        function_names = [func_data.get("function_name", "unknown") for func_data in functions.values()]
        function_node_map = {
            func_data.get("function_name", "unknown"): f"{file_prefix}_{func_name}"
            for func_name, func_data in functions.items()
        }

        # Look for function calls in source code
        source_lines = source_code.split("\n") if source_code else []

        for i, line in enumerate(source_lines):
            for func_name in function_names:
                if f"{func_name}(" in line and not line.strip().startswith("def "):
                    # Found a function call
                    calling_function = self._find_containing_function(i + 1, source_lines, function_names)

                    if calling_function and calling_function != func_name:
                        caller_id = function_node_map.get(calling_function)
                        callee_id = function_node_map.get(func_name)

                        if caller_id and callee_id:
                            call_edges.append(
                                {
                                    "id": f"call_edge_{caller_id}_to_{callee_id}",
                                    "source": caller_id,
                                    "target": callee_id,
                                    "type": "smoothstep",
                                    "label": "calls",
                                    "animated": True,
                                    "data": {"type": "function_call", "line": i + 1},
                                }
                            )

        return call_edges

    def _extract_imports(self, tokens: List[Dict[str, Any]], source_code: str) -> List[Dict]:
        """Extract import statements and their details."""
        imports = []
        source_lines = source_code.split("\n") if source_code else []

        for i, line in enumerate(source_lines):
            line = line.strip()
            if line.startswith("import "):
                # Handle 'import module'
                module = line[7:].split()[0].split(".")[0]  # Get first part
                imports.append({"module": module, "type": "import", "line": i + 1})
            elif line.startswith("from "):
                # Handle 'from module import ...'
                parts = line.split()
                if len(parts) >= 4 and parts[2] == "import":
                    module = parts[1]
                    imports.append({"module": module, "type": "from_import", "line": i + 1})

        return imports

    def _find_similarity_for_function(self, func_name: str, shared_blocks: List[Dict], file_prefix: str) -> Dict:
        """Find similarity block for a given function."""
        for block in shared_blocks:
            if file_prefix == "file1" and block.get("file1_function") == func_name:
                return block
            elif file_prefix == "file2" and block.get("file2_function") == func_name:
                return block
        return None

    def _generate_similarity_edges(self, shared_blocks: List[Dict], all_nodes: List[Dict]) -> List[Dict]:
        """Generate clean edges connecting similar functions - no styling (frontend handles with CSS)."""
        similarity_edges = []

        for i, block in enumerate(shared_blocks):
            file1_func = block.get("file1_function", "")
            file2_func = block.get("file2_function", "")

            # Find corresponding nodes
            file1_node_id = f"file1_{file1_func}"
            file2_node_id = f"file2_{file2_func}"

            # Check if both nodes exist
            file1_node_exists = any(node["id"] == file1_node_id for node in all_nodes)
            file2_node_exists = any(node["id"] == file2_node_id for node in all_nodes)

            if file1_node_exists and file2_node_exists:
                similarity_edges.append(
                    {
                        "id": f"similarity_edge_{i}",
                        "source": file1_node_id,
                        "target": file2_node_id,
                        "animated": True,
                        "type": "bezier",
                        "data": {"type": "similarity", "similarity_score": block.get("similarity_score", 0)},
                    }
                )

        return similarity_edges

    def _find_containing_function(self, line_num: int, source_lines: List[str], function_names: List[str]) -> str:
        """Find which function contains a given line number."""
        # Check if line number is valid
        if line_num <= 0 or line_num > len(source_lines):
            return None

        # Look backwards from the line to find the containing function
        for i in range(line_num - 1, -1, -1):
            line = source_lines[i].strip()
            if line.startswith("def "):
                # Extract function name
                func_part = line[4:].split("(")[0].strip()
                if func_part in function_names:
                    return func_part
        return None

    # Delegate methods to SimilarityDetectionService
    def _extract_functions_with_positions(self, tokens: List[Dict[str, Any]], source_code: str = "") -> Dict[str, Dict]:
        """Delegate to SimilarityDetectionService for function extraction."""
        return self.similarity_service._extract_functions_with_positions(tokens, source_code)

    def _extract_function_name(self, function_token: Dict[str, Any], all_tokens: List[Dict[str, Any]]) -> str:
        """Delegate to SimilarityDetectionService for function name extraction."""
        return self.similarity_service._extract_function_name(function_token, all_tokens)

    def _extract_code_block(self, source_lines: List[str], start_line: int, end_line: int) -> str:
        """Delegate to SimilarityDetectionService for code block extraction."""
        return self.similarity_service._extract_code_block(source_lines, start_line, end_line)
