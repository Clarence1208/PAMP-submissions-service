"""
Visualization Service for generating React Flow compatible AST visualizations.
Handles conversion of code tokens into interactive graph structures.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class VisualizationService:
    """Service for generating React Flow compatible visualizations from code similarity analysis."""

    def __init__(self, tokenization_service=None):
        """Initialize the visualization service."""
        if tokenization_service is None:
            # Use singleton service to avoid multiple initializations
            from app.shared.services import get_tokenization_service
            self.tokenization_service = get_tokenization_service()
        else:
            self.tokenization_service = tokenization_service

    def generate_react_flow_ast(
        self,
        source1: str = "",
        source2: str = "",
        file1_name: str = "file1",
        file2_name: str = "file2",
        layout_engine: str = "elk",
    ) -> Dict[str, Any]:
        """
        Generate a React Flow compatible visualization from two sets of tokens.

        Returns:
            Dictionary containing React Flow nodes and edges for visualization
        """
        try:
            # Import here to avoid circular imports
            from app.domains.detection.similarity_detection_service import SimilarityDetectionService

            similarity_service = SimilarityDetectionService()

            # First detect shared code blocks to determine if we should include these files
            from pathlib import Path

            file1_path = Path(file1_name) if file1_name else None
            file2_path = Path(file2_name) if file2_name else None

            shared_blocks_result = similarity_service.detect_shared_code_blocks(
                source1=source1,
                source2=source2,
                file1_name=file1_name,
                file2_name=file2_name,
                file1_path=file1_path,
                file2_path=file2_path,
                tokenization_service=self.tokenization_service,
            )

            nodes = []
            edges = []
            shared_blocks = shared_blocks_result["shared_blocks"]

            # Generate nodes and edges for both files
            file1_functions = self._extract_functions_with_imports(source1, file1_name)
            file2_functions = self._extract_functions_with_imports(source2, file2_name)

            # Generate file1 nodes (calculator project)
            file1_nodes = self._generate_file_group_nodes(
                file1_functions, file1_name, "file1", shared_blocks, source1, source2
            )

            # Generate file2 nodes (game project)
            file2_nodes = self._generate_file_group_nodes(
                file2_functions, file2_name, "file2", shared_blocks, source2, source1
            )

            nodes.extend(file1_nodes)
            nodes.extend(file2_nodes)

            # Generate function call edges within each file
            file1_call_edges = self._generate_function_call_edges(file1_functions, "file1", source1)
            file2_call_edges = self._generate_function_call_edges(file2_functions, "file2", source2)
            edges.extend(file1_call_edges)
            edges.extend(file2_call_edges)

            # Generate similarity edges between files
            similarity_edges = self._generate_similarity_edges_advanced(file1_functions, file2_functions, shared_blocks)
            edges.extend(similarity_edges)

            # Calculate analysis metadata
            total_similarities = len(
                [edge for edge in similarity_edges if edge.get("data", {}).get("type") == "similarity"]
            )
            average_similarity = sum(
                edge.get("data", {}).get("similarity_score", 0)
                for edge in similarity_edges
                if edge.get("data", {}).get("type") == "similarity"
            ) / max(total_similarities, 1)

            has_similarity = total_similarities > 0

            return {
                "nodes": nodes,
                "edges": edges,
                "has_similarity": has_similarity,
                "analysis_metadata": {
                    "total_similarities": total_similarities,
                    "average_similarity": average_similarity,
                    "algorithm": layout_engine + "_layered",
                    "analysis_version": "2.1.0",
                },
                "file_metadata": {
                    "file1": {"name": file1_name, "functions": len(file1_functions.get("functions", []))},
                    "file2": {"name": file2_name, "functions": len(file2_functions.get("functions", []))},
                },
            }

        except Exception as e:
            # Fallback for any errors
            return {
                "nodes": [],
                "edges": [],
                "has_similarity": False,
                "error": f"Visualization generation failed: {str(e)}",
                "layout": {"engine": layout_engine},
            }

    def generate_react_flow_ast_with_cache(
        self,
        source1: str = "",
        source2: str = "",
        file1_name: str = "file1",
        file2_name: str = "file2",
        layout_engine: str = "elk",
        submission1_id: Optional[str] = None,
        submission2_id: Optional[str] = None,
        file1_path: Optional[Path] = None,
        file2_path: Optional[Path] = None,
        project1_root: Optional[Path] = None,
        project2_root: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Generate a React Flow compatible visualization from two sets of tokens with caching support.
        This method leverages the tokenization cache when submission context is available.

        Returns:
            Dictionary containing React Flow nodes and edges for visualization
        """
        try:
            # Import here to avoid circular imports
            from app.domains.detection.similarity_detection_service import SimilarityDetectionService

            similarity_service = SimilarityDetectionService()

            # Use cached shared block detection when possible
            shared_blocks_result = similarity_service.detect_shared_code_blocks_with_cache(
                source1=source1,
                source2=source2,
                file1_name=file1_name,
                file2_name=file2_name,
                file1_path=file1_path,
                file2_path=file2_path,
                tokenization_service=self.tokenization_service,
                submission1_id=submission1_id,
                submission2_id=submission2_id,
                project1_root=project1_root,
                project2_root=project2_root,
            )

            nodes = []
            edges = []
            shared_blocks = shared_blocks_result["shared_blocks"]

            # Generate nodes and edges for both files with caching
            file1_functions = self._extract_functions_with_imports_cached(
                source1, file1_name, submission1_id, file1_path, project1_root
            )
            file2_functions = self._extract_functions_with_imports_cached(
                source2, file2_name, submission2_id, file2_path, project2_root
            )

            # Generate file1 nodes (calculator project)
            file1_nodes = self._generate_file_group_nodes(
                file1_functions, file1_name, "file1", shared_blocks, source1, source2
            )

            # Generate file2 nodes (game project)
            file2_nodes = self._generate_file_group_nodes(
                file2_functions, file2_name, "file2", shared_blocks, source2, source1
            )

            nodes.extend(file1_nodes)
            nodes.extend(file2_nodes)

            # Generate function call edges within each file
            file1_call_edges = self._generate_function_call_edges(file1_functions, "file1", source1)
            file2_call_edges = self._generate_function_call_edges(file2_functions, "file2", source2)
            edges.extend(file1_call_edges)
            edges.extend(file2_call_edges)

            # Generate similarity edges between files
            similarity_edges = self._generate_similarity_edges_advanced(file1_functions, file2_functions, shared_blocks)
            edges.extend(similarity_edges)

            # Calculate analysis metadata
            total_similarities = len(
                [edge for edge in similarity_edges if edge.get("data", {}).get("type") == "similarity"]
            )
            average_similarity = sum(
                edge.get("data", {}).get("similarity_score", 0)
                for edge in similarity_edges
                if edge.get("data", {}).get("type") == "similarity"
            ) / max(total_similarities, 1)

            has_similarity = total_similarities > 0

            return {
                "nodes": nodes,
                "edges": edges,
                "has_similarity": has_similarity,
                "analysis_metadata": {
                    "total_similarities": total_similarities,
                    "average_similarity": average_similarity,
                    "algorithm": layout_engine + "_layered",
                    "analysis_version": "2.1.0",
                },
                "file_metadata": {
                    "file1": {"name": file1_name, "functions": len(file1_functions.get("functions", []))},
                    "file2": {"name": file2_name, "functions": len(file2_functions.get("functions", []))},
                },
            }

        except Exception as e:
            # Fallback to non-cached version
            logger.warning(f"Cache-aware visualization failed, falling back to standard method: {e}")
            return self.generate_react_flow_ast(source1, source2, file1_name, file2_name, layout_engine)

    def _extract_functions_with_imports(self, source_code: str, filename: str) -> Dict[str, Any]:
        """Extract functions and imports from source code."""
        if not source_code:
            return {"functions": [], "imports": []}

        # Extract functions
        file_path = Path(filename)
        functions_dict = self.tokenization_service.extract_functions_with_positions(source_code, file_path)
        functions_list = list(functions_dict.values()) if functions_dict else []

        # Extract imports (simple regex-based extraction)
        imports = []
        import_lines = re.findall(r"^(?:from\s+\S+\s+)?import\s+([^#\n]+)", source_code, re.MULTILINE)
        for import_line in import_lines:
            # Clean up and split imports
            clean_imports = [imp.strip().split(" as ")[0] for imp in import_line.split(",")]
            imports.extend([imp.strip() for imp in clean_imports if imp.strip()])

        # Remove duplicates while preserving order
        unique_imports = []
        seen = set()
        for imp in imports:
            if imp not in seen:
                unique_imports.append(imp)
                seen.add(imp)

        return {"functions": functions_list, "imports": unique_imports[:10]}  # Limit to first 10 imports

    def _extract_functions_with_imports_cached(
        self,
        source_code: str,
        filename: str,
        submission_id: Optional[str] = None,
        file_path: Optional[Path] = None,
        project_root: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Extract functions and imports from source code with caching support."""
        if not source_code:
            return {"functions": [], "imports": []}

        # Extract functions with caching when submission context is available
        if submission_id and file_path and project_root:
            try:
                functions_dict = self.tokenization_service.extract_functions_with_positions(source_code, file_path)
                functions_list = list(functions_dict.values()) if functions_dict else []
            except Exception as e:
                logger.warning(f"Cached function extraction failed, falling back: {e}")
                # Fallback to non-cached
                file_path_obj = Path(filename)
                functions_dict = self.tokenization_service.extract_functions_with_positions(source_code, file_path_obj)
                functions_list = list(functions_dict.values()) if functions_dict else []
        else:
            # Use original method when no caching context
            file_path_obj = Path(filename)
            functions_dict = self.tokenization_service.extract_functions_with_positions(source_code, file_path_obj)
            functions_list = list(functions_dict.values()) if functions_dict else []

        # Extract imports (simple regex-based extraction)
        imports = []
        import_lines = re.findall(r"^(?:from\s+\S+\s+)?import\s+([^#\n]+)", source_code, re.MULTILINE)
        for import_line in import_lines:
            # Clean up and split imports
            clean_imports = [imp.strip().split(" as ")[0] for imp in import_line.split(",")]
            imports.extend([imp.strip() for imp in clean_imports if imp.strip()])

        # Remove duplicates while preserving order
        unique_imports = []
        seen = set()
        for imp in imports:
            if imp not in seen:
                unique_imports.append(imp)
                seen.add(imp)

        return {"functions": functions_list, "imports": unique_imports[:10]}  # Limit to first 10 imports

    def _generate_file_group_nodes(
        self,
        file_data: Dict[str, Any],
        filename: str,
        file_prefix: str,
        shared_blocks: List[Dict],
        own_source: str,
        other_source: str,
    ) -> List[Dict[str, Any]]:
        """Generate React Flow nodes for a file in the expected group format."""
        nodes = []
        functions = file_data.get("functions", [])
        imports = file_data.get("imports", [])

        # File root group node
        file_root_id = f"{file_prefix}_root"
        nodes.append(
            {
                "id": file_root_id,
                "type": "group",
                "data": {
                    "label": f"📁 {filename}",
                    "type": "file_subflow",
                    "filename": filename,
                    "functions_count": len(functions),
                    "imports_count": len(imports),
                },
            }
        )

        # Imports group node
        if imports:
            imports_id = f"{file_prefix}_imports_group"
            nodes.append(
                {
                    "id": imports_id,
                    "type": "default",
                    "data": {"label": f"📦 Imports ({len(imports)})", "type": "import_group", "imports": imports},
                    "parentNode": file_root_id,
                }
            )

        # Function nodes
        for i, func in enumerate(functions):
            func_id = f"{file_prefix}_function_{i}_{func['function_name']}"

            # Check for similarity with other file's functions
            similarity_data = self._find_function_similarity(func, shared_blocks, file_prefix, own_source, other_source)

            # Generate function label with similarity indicator
            if similarity_data["has_similarity"]:
                similarity_percent = similarity_data["similarity_score"] * 100
                label = f"⚡ {func['function_name']} ({similarity_percent:.1f}%)"
            else:
                label = f"⚙️ {func['function_name']}"

            func_node = {
                "id": func_id,
                "type": "default",
                "data": {
                    "label": label,
                    "type": "function",
                    "function_name": func["function_name"],
                    "start_line": func.get("start_line", 0),
                    "end_line": func.get("end_line", 0),
                    "has_similarity": similarity_data["has_similarity"],
                    "similarity_score": similarity_data["similarity_score"],
                },
                "parentNode": file_root_id,
            }

            # Add rich similarity data if found
            if similarity_data["has_similarity"]:
                func_node["data"].update(
                    {
                        "similarity_target": similarity_data["similarity_target"],
                        "source_code": similarity_data["source_code"],
                        "line_numbers": similarity_data["line_numbers"],
                        "similarity_details": similarity_data["similarity_details"],
                    }
                )

            nodes.append(func_node)

        return nodes

    def _find_function_similarity(
        self, func: Dict[str, Any], shared_blocks: List[Dict], file_prefix: str, own_source: str, other_source: str
    ) -> Dict[str, Any]:
        """Find similarity data for a function based on shared blocks - returns the HIGHEST similarity match."""
        best_match = None
        highest_similarity = 0.0

        for block in shared_blocks:
            # Check if this function matches a shared block
            func_matches = False
            if file_prefix == "file1":
                func_matches = block.get("file1_function") == func["function_name"] or (
                    block.get("file1_start_line", 0) <= func.get("start_line", 0) <= block.get("file1_end_line", 0)
                )
            else:
                func_matches = block.get("file2_function") == func["function_name"] or (
                    block.get("file2_start_line", 0) <= func.get("start_line", 0) <= block.get("file2_end_line", 0)
                )

            if func_matches:
                current_similarity = block.get("similarity_score", 0.0)

                # Only update if this similarity is higher than the current best
                if current_similarity > highest_similarity:
                    highest_similarity = current_similarity
                    file1_code = block.get("file1_code_block", "")
                    file2_code = block.get("file2_code_block", "")

                    best_match = {
                        "has_similarity": True,
                        "similarity_score": current_similarity,
                        "similarity_target": f"function_{block.get('file2_function' if file_prefix == 'file1' else 'file1_function', 'unknown')}",
                        "source_code": {"file1_code": file1_code, "file2_code": file2_code},
                        "line_numbers": {
                            "file1": {"start": block.get("file1_start_line", 0), "end": block.get("file1_end_line", 0)},
                            "file2": {"start": block.get("file2_start_line", 0), "end": block.get("file2_end_line", 0)},
                        },
                        "similarity_details": {
                            "algorithm_used": "ast_similarity_v2",
                            "similarity_type": "structural",
                            "confidence_level": current_similarity,
                            "common_patterns": block.get("common_elements", []),
                        },
                    }

        # Return the best match found, or no similarity if none found
        return best_match if best_match else {"has_similarity": False, "similarity_score": 0}

    def _generate_function_call_edges(
        self, file_data: Dict[str, Any], file_prefix: str, source_code: str
    ) -> List[Dict[str, Any]]:
        """Generate edges representing function calls within a file."""
        edges = []
        functions = file_data.get("functions", [])

        # Simple regex-based function call detection
        for i, func in enumerate(functions):
            func_id = f"{file_prefix}_function_{i}_{func['function_name']}"

            # Look for calls to other functions in this file
            for j, other_func in enumerate(functions):
                if i != j:
                    other_func_id = f"{file_prefix}_function_{j}_{other_func['function_name']}"

                    # Check if this function calls the other function
                    func_code = func.get("code_block", "")
                    call_pattern = rf'\b{re.escape(other_func["function_name"])}\s*\('

                    if re.search(call_pattern, func_code):
                        # Find approximate line number of the call
                        call_line = func.get("start_line", 0)
                        for line_num, line in enumerate(func_code.split("\n")):
                            if re.search(call_pattern, line):
                                call_line = func.get("start_line", 0) + line_num
                                break

                        edges.append(
                            {
                                "id": f"call_edge_{func_id}_to_{other_func_id}",
                                "source": func_id,
                                "target": other_func_id,
                                "type": "smoothstep",
                                "label": "calls",
                                "animated": True,
                                "data": {"type": "function_call", "line": call_line},
                            }
                        )

        return edges

    def _generate_similarity_edges_advanced(
        self, file1_data: Dict[str, Any], file2_data: Dict[str, Any], shared_blocks: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Generate similarity edges between functions from different files."""
        edges = []
        edge_counter = 0

        file1_functions = file1_data.get("functions", [])
        file2_functions = file2_data.get("functions", [])

        for block in shared_blocks:
            # Find matching functions
            file1_func_id = None
            file2_func_id = None

            # Find file1 function
            for i, func in enumerate(file1_functions):
                if func["function_name"] == block.get("file1_function") or (
                    block.get("file1_start_line", 0) <= func.get("start_line", 0) <= block.get("file1_end_line", 0)
                ):
                    file1_func_id = f"file1_function_{i}_{func['function_name']}"
                    break

            # Find file2 function
            for i, func in enumerate(file2_functions):
                if func["function_name"] == block.get("file2_function") or (
                    block.get("file2_start_line", 0) <= func.get("start_line", 0) <= block.get("file2_end_line", 0)
                ):
                    file2_func_id = f"file2_function_{i}_{func['function_name']}"
                    break

            # Create similarity edge if both functions found
            if file1_func_id and file2_func_id:
                edges.append(
                    {
                        "id": f"similarity_edge_{edge_counter}",
                        "source": file1_func_id,
                        "target": file2_func_id,
                        "animated": True,
                        "type": "default",
                        "data": {"type": "similarity", "similarity_score": block.get("similarity_score", 0.8)},
                    }
                )
                edge_counter += 1

        return edges
