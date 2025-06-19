"""
Similarity Detection Service
Handles code similarity analysis, comparison, and shared code block detection.
"""

import logging
import math
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class SimilarityDetectionService:
    def __init__(self):
        """Initialize the similarity detection service."""
        pass

    def prepare_for_similarity(self, tokens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prepare tokens for similarity comparison by filtering and normalizing elements.
        
        Keeps elements relevant to code structure and logic:
        - Control flow (if, for, while, etc.)
        - Function/method definitions and calls
        - Class definitions
        - Operators
        - Import statements
        - Data structures (lists, dicts, etc.)
        
        Filters out elements that don't affect logic:
        - Comments
        - String literals (normalize to generic placeholder)
        - Numeric literals (normalize to generic placeholder)
        - Variable names (normalize to generic placeholder)
        """
        similarity_tokens = []

        # Types to keep as-is (structural/logical elements)
        keep_types = {
            'if_statement', 'else_clause', 'elif_clause',
            'for_statement', 'while_statement', 'break_statement', 'continue_statement',
            'function_definition', 'class_definition', 'method_definition',
            'call', 'attribute', 'subscript',
            'import_statement', 'import_from_statement',
            'return_statement', 'yield_statement',
            'try_statement', 'except_clause', 'finally_clause',
            'with_statement', 'assert_statement',
            'list', 'dictionary', 'set', 'tuple',
            'list_comprehension', 'dictionary_comprehension', 'set_comprehension',
            'lambda', 'generator_expression',
            'binary_operator', 'unary_operator', 'comparison_operator',
            'boolean_operator', 'assignment',
            'augmented_assignment', 'decorated_definition'
        }

        # Types to normalize (replace content with generic placeholder)
        normalize_types = {
            'string': '<STRING>',
            'integer': '<NUMBER>',
            'float': '<NUMBER>',
            'identifier': '<VAR>',
            'comment': '<COMMENT>'
        }

        # Types to completely filter out
        skip_types = {
            'comment',  # Comments don't affect logic
            'ERROR'  # Parsing errors
        }

        for token in tokens:
            token_type = token.get('type', '')

            # Skip irrelevant types
            if token_type in skip_types:
                continue

            # Keep structural types as-is
            if token_type in keep_types:
                similarity_tokens.append({
                    'type': token_type,
                    'text': token.get('text', ''),
                    'normalized': False
                })
                continue

            # Normalize certain types
            if token_type in normalize_types:
                similarity_tokens.append({
                    'type': token_type,
                    'text': normalize_types[token_type],
                    'normalized': True
                })
                continue

            # For other types, include them but mark for potential normalization
            similarity_tokens.append({
                'type': token_type,
                'text': token.get('text', ''),
                'normalized': False
            })

        return similarity_tokens

    def get_similarity_signature(self, tokens: List[Dict[str, Any]]) -> str:
        """
        Generate a compact signature for similarity comparison.
        This creates a normalized string representation focusing on structure.
        """
        similarity_tokens = self.prepare_for_similarity(tokens)

        # Create a compact signature by joining token types and normalized text
        signature_parts = []
        for token in similarity_tokens:
            if token['normalized']:
                # For normalized tokens, just use the placeholder
                signature_parts.append(token['text'])
            else:
                # For structural tokens, use type + simplified text
                token_text = token['text'].strip()
                if len(token_text) > 20:  # Truncate very long text
                    token_text = token_text[:20] + "..."
                signature_parts.append(f"{token['type']}:{token_text}")

        return " | ".join(signature_parts)

    def compare_similarity(self, tokens1: List[Dict[str, Any]], tokens2: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compare similarity between two sets of tokens.
        Returns similarity metrics and analysis.
        """
        # Prepare both token sets for similarity comparison
        sim_tokens1 = self.prepare_for_similarity(tokens1)
        sim_tokens2 = self.prepare_for_similarity(tokens2)

        # Generate signatures
        signature1 = self.get_similarity_signature(tokens1)
        signature2 = self.get_similarity_signature(tokens2)

        # Simple similarity metrics
        sig1_parts = signature1.split(' | ')
        sig2_parts = signature2.split(' | ')

        # Calculate overlap
        common_parts = set(sig1_parts) & set(sig2_parts)
        total_unique_parts = set(sig1_parts) | set(sig2_parts)

        jaccard_similarity = len(common_parts) / len(total_unique_parts) if total_unique_parts else 0

        # Structure similarity (focusing on types only)
        types1 = [token['type'] for token in sim_tokens1]
        types2 = [token['type'] for token in sim_tokens2]

        common_types = set(types1) & set(types2)
        total_types = set(types1) | set(types2)

        type_similarity = len(common_types) / len(total_types) if total_types else 0

        return {
            'jaccard_similarity': jaccard_similarity,
            'type_similarity': type_similarity,
            'common_elements': len(common_parts),
            'total_unique_elements': len(total_unique_parts),
            'signature1_length': len(sig1_parts),
            'signature2_length': len(sig2_parts),
            'common_types': list(common_types),
            'signatures': {
                'file1': signature1[:100] + "..." if len(signature1) > 100 else signature1,
                'file2': signature2[:100] + "..." if len(signature2) > 100 else signature2
            }
        }

    def detect_shared_code_blocks(self, tokens1: List[Dict[str, Any]], tokens2: List[Dict[str, Any]],
                                  source1: str = "", source2: str = "",
                                  file1_name: str = "", file2_name: str = "") -> Dict[str, Any]:
        """
        Detect shared code blocks between two sets of tokens.
        
        Args:
            tokens1: First set of tokens
            tokens2: Second set of tokens  
            source1: Original source code of first file (optional, for extracting code blocks)
            source2: Original source code of second file (optional, for extracting code blocks)
            file1_name: Name of the first file (optional, for better reporting)
            file2_name: Name of the second file (optional, for better reporting)
        """
        # Extract function definitions from both files
        functions1 = self._extract_functions_with_positions(tokens1, source1)
        functions2 = self._extract_functions_with_positions(tokens2, source2)

        shared_blocks = []
        similarity_scores = []

        for func1_name, func1_data in functions1.items():
            for func2_name, func2_data in functions2.items():
                # Compare function signatures and body
                func_similarity = self._compare_function_similarity(func1_data['tokens'], func2_data['tokens'])

                if func_similarity['similarity_score'] > 0.7:  # Threshold for considering functions similar
                    shared_block = {
                        'file1_function': func1_name,
                        'file2_function': func2_name,
                        'file1_filename': file1_name,
                        'file2_filename': file2_name,
                        'similarity_score': func_similarity['similarity_score'],
                        'common_patterns': func_similarity['common_patterns'],
                        'file1_code_block': func1_data.get('code_block', ''),
                        'file2_code_block': func2_data.get('code_block', ''),
                        'file1_start_line': func1_data.get('start_line', 0),
                        'file1_end_line': func1_data.get('end_line', 0),
                        'file2_start_line': func2_data.get('start_line', 0),
                        'file2_end_line': func2_data.get('end_line', 0)
                    }
                    shared_blocks.append(shared_block)
                    similarity_scores.append(func_similarity['similarity_score'])

        return {
            'shared_blocks': shared_blocks,
            'total_shared_blocks': len(shared_blocks),
            'average_similarity': sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0,
            'functions_file1': len(functions1),
            'functions_file2': len(functions2),
            'shared_percentage': len(shared_blocks) / max(len(functions1),
                                                          len(functions2)) * 100 if functions1 or functions2 else 0
        }

    def _extract_functions_with_positions(self, tokens: List[Dict[str, Any]], source_code: str = "") -> Dict[str, Dict]:
        """Extract function definitions with their tokens, positions, and actual code blocks."""
        functions = {}
        current_function = None
        current_function_tokens = []
        current_function_name = None
        function_start_line = 0
        function_end_line = 0
        function_depth = 0

        source_lines = source_code.split('\n') if source_code else []

        for token in tokens:
            token_type = token.get('type', '')

            # Start of a new function
            if token_type == 'function_definition':
                # Save previous function if exists
                if current_function and current_function_tokens:
                    end_line = function_end_line if function_end_line > 0 else function_start_line + 10
                    code_block = self._extract_code_block(source_lines, function_start_line, end_line)

                    functions[current_function] = {
                        'tokens': current_function_tokens,
                        'code_block': code_block,
                        'start_line': function_start_line,
                        'end_line': end_line,
                        'function_name': current_function_name
                    }

                # Start new function
                current_function_tokens = [token]
                function_depth = 1
                # Ensure line numbers are integers
                function_start_line = int(token.get('start', 0)) if token.get('start') is not None else 0
                function_end_line = int(token.get('end', 0)) if token.get('end') is not None else 0

                # Try to extract function name from the token text or find it in next tokens
                current_function_name = self._extract_function_name(token, tokens)
                current_function = f"function_{len(functions)}_{current_function_name}" if current_function_name else f"function_{len(functions)}"

            # Inside a function
            elif current_function and function_depth > 0:
                current_function_tokens.append(token)
                # Ensure end position is an integer before comparison
                token_end = int(token.get('end', function_end_line)) if token.get(
                    'end') is not None else function_end_line
                function_end_line = max(function_end_line, token_end)

                # Track nesting depth (simplified)
                if token_type in ['function_definition', 'class_definition']:
                    function_depth += 1
                elif token_type in ['return_statement'] and function_depth == 1:
                    # End of current function (simplified detection)
                    token_end = int(token.get('end', function_end_line)) if token.get(
                        'end') is not None else function_end_line
                    end_line = max(function_end_line, token_end)
                    code_block = self._extract_code_block(source_lines, function_start_line, end_line + 1)

                    functions[current_function] = {
                        'tokens': current_function_tokens,
                        'code_block': code_block,
                        'start_line': function_start_line,
                        'end_line': end_line,
                        'function_name': current_function_name
                    }
                    current_function = None
                    current_function_tokens = []
                    function_depth = 0

        # Handle last function
        if current_function and current_function_tokens:
            end_line = function_end_line if function_end_line > 0 else function_start_line + 10
            code_block = self._extract_code_block(source_lines, function_start_line, end_line + 1)

            functions[current_function] = {
                'tokens': current_function_tokens,
                'code_block': code_block,
                'start_line': function_start_line,
                'end_line': end_line,
                'function_name': current_function_name
            }

        return functions

    def _extract_function_name(self, function_token: Dict[str, Any], all_tokens: List[Dict[str, Any]]) -> str:
        """Extract function name from function definition token or surrounding tokens."""
        # Try to extract from the function token text first
        func_text = function_token.get('text', '')
        if 'def ' in func_text:
            # Simple regex-like extraction
            try:
                lines = func_text.split('\n')
                for line in lines:
                    if 'def ' in line:
                        # Extract function name between 'def ' and '('
                        def_start = line.find('def ') + 4
                        paren_pos = line.find('(', def_start)
                        if paren_pos > def_start:
                            func_name = line[def_start:paren_pos].strip()
                            if func_name and func_name.isidentifier():
                                return func_name
            except:
                pass

        return "unknown_function"

    def _extract_code_block(self, source_lines: List[str], start_line: int, end_line: int) -> str:
        """Extract code block from source lines between start and end line numbers."""
        if not source_lines:
            return ""

        # Ensure line numbers are integers and handle None values
        try:
            start_line = int(start_line) if start_line is not None else 0
            end_line = int(end_line) if end_line is not None else 0
        except (ValueError, TypeError):
            return ""

        if start_line < 0:
            return ""

        # Adjust for 0-based indexing and bounds
        start_idx = max(0, start_line)
        end_idx = min(len(source_lines), end_line)

        if start_idx >= end_idx:
            return ""

        code_lines = source_lines[start_idx:end_idx]
        return '\n'.join(code_lines)

    def _compare_function_similarity(self, func1_tokens: List[Dict[str, Any]], func2_tokens: List[Dict[str, Any]]) -> \
            Dict[str, Any]:
        """Compare similarity between two function token sequences."""
        # Prepare tokens for similarity comparison
        sim_tokens1 = self.prepare_for_similarity(func1_tokens)
        sim_tokens2 = self.prepare_for_similarity(func2_tokens)

        # Extract token types for pattern matching
        types1 = [token['type'] for token in sim_tokens1]
        types2 = [token['type'] for token in sim_tokens2]

        # Find common patterns (simple approach using sets)
        common_types = set(types1) & set(types2)
        total_types = set(types1) | set(types2)

        type_similarity = len(common_types) / len(total_types) if total_types else 0

        # Text similarity for non-normalized tokens
        text1 = ' '.join([token['text'] for token in sim_tokens1 if not token.get('normalized', False)])
        text2 = ' '.join([token['text'] for token in sim_tokens2 if not token.get('normalized', False)])

        # Simple text similarity
        text_similarity = self._simple_text_similarity(text1, text2)

        # Combined similarity score
        similarity_score = (type_similarity * 0.7) + (text_similarity * 0.3)

        return {
            'similarity_score': similarity_score,
            'type_similarity': type_similarity,
            'text_similarity': text_similarity,
            'common_patterns': list(common_types)
        }

    def _simple_text_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity using word overlap."""
        if not text1 or not text2:
            return 0.0

        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        common_words = words1 & words2
        total_words = words1 | words2

        return len(common_words) / len(total_words) if total_words else 0.0

    def generate_react_flow_ast(self, tokens1: List[Dict[str, Any]], tokens2: List[Dict[str, Any]],
                                source1: str = "", source2: str = "",
                                file1_name: str = "", file2_name: str = "",
                                layout_type: str = "elk") -> Dict[str, Any]:
        """
        Generate React Flow JSON representation showing actual code flow and relationships.
        Only includes files where similarity is detected and adds comments with similar code.
        Shows function calls, imports, and control flow relationships with ELK layout optimization.
        
        Args:
            layout_type: "elk", "dagre", "hierarchical", "force", "circular", or "manual" (default: "elk")
        """
        # First detect shared code blocks to see if we should include these files
        shared_blocks_result = self.detect_shared_code_blocks(
            tokens1, tokens2, source1, source2, file1_name, file2_name
        )

        # If no similarities detected, return empty structure
        if shared_blocks_result['total_shared_blocks'] == 0:
            return {
                "nodes": [],
                "edges": [],
                "has_similarity": False,
                "message": "No similarities detected between files"
            }

        # Generate flow representation for both files
        nodes = []
        edges = []
        node_id_counter = 0

        # Calculate layout dimensions
        layout_config = self._get_layout_config(layout_type)

        # File 1 flow with layout
        file1_nodes, file1_edges, node_id_counter = self._generate_file_flow_nodes_with_layout(
            tokens1, source1, file1_name, "file1", layout_config["file1_offset"],
            node_id_counter, shared_blocks_result['shared_blocks'], layout_type
        )

        # File 2 flow with layout (positioned based on layout type)
        file2_nodes, file2_edges, node_id_counter = self._generate_file_flow_nodes_with_layout(
            tokens2, source2, file2_name, "file2", layout_config["file2_offset"],
            node_id_counter, shared_blocks_result['shared_blocks'], layout_type
        )

        # Combine nodes and edges
        nodes.extend(file1_nodes)
        nodes.extend(file2_nodes)
        edges.extend(file1_edges)
        edges.extend(file2_edges)

        # Apply layout algorithm for better spacing
        if layout_type in ["dagre", "elk"]:
            # For auto-layout libraries, provide minimal positioning and let library handle it
            nodes = self._prepare_nodes_for_auto_layout(nodes, layout_type)
        elif layout_type != "manual":
            nodes = self._apply_layout_algorithm(nodes, edges, layout_type)

        # Add similarity connection edges between similar functions
        similarity_edges = self._generate_similarity_edges(shared_blocks_result['shared_blocks'], nodes)
        edges.extend(similarity_edges)

        return {
            "nodes": nodes,
            "edges": edges,
            "has_similarity": True,
            "shared_blocks_count": shared_blocks_result['total_shared_blocks'],
            "average_similarity": shared_blocks_result['average_similarity'],
            "flow_type": "execution_flow",
            "layout_type": layout_type,
            "layout_config": layout_config,
            "files": {
                "file1": file1_name,
                "file2": file2_name
            },
            "layout_libraries": {
                "elk_integration": {
                    "library": "elkjs",
                    "install": "npm install elkjs",
                    "usage": "import ELK from 'elkjs/lib/elk.bundled.js'",
                    "recommended_for": "Complex subflow hierarchies (RECOMMENDED)",
                    "recommended_settings": {
                        "algorithm": "layered",
                        "elk.direction": layout_config.get("elk_direction", "DOWN"),
                        "elk.spacing.nodeNode": layout_config.get("node_spacing_elk", "120"),
                        "elk.layered.spacing.nodeNodeBetweenLayers": layout_config.get("layer_spacing_elk", "200"),
                        "elk.spacing.componentComponent": layout_config.get("component_spacing_elk", "100"),
                        "elk.hierarchyHandling": "INCLUDE_CHILDREN",
                        "elk.layered.thoroughness": "7",
                        "elk.layered.priority.straightness": "7",
                        "elk.padding": "[top=40,left=30,bottom=30,right=30]"
                    }
                },
                "dagre_integration": {
                    "library": "@dagrejs/dagre",
                    "install": "npm install @dagrejs/dagre",
                    "usage": "import dagre from '@dagrejs/dagre'",
                    "recommended_for": "Simple hierarchies without subflows",
                    "recommended_settings": {
                        "rankdir": layout_config.get("dagre_direction", "TB"),
                        "align": "UL",
                        "nodesep": layout_config.get("node_separation", 80),
                        "ranksep": layout_config.get("rank_separation", 120),
                        "marginx": 40,
                        "marginy": 40
                    }
                }
            }
        }

    def _get_layout_config(self, layout_type: str) -> Dict[str, Any]:
        """Get layout configuration based on layout type."""
        configs = {
            "elk": {
                "file1_offset": {"x": 0, "y": 0},
                "file2_offset": {"x": 0, "y": 0},  # Let ELK handle positioning
                "node_spacing_elk": "120",
                "layer_spacing_elk": "200",
                "component_spacing_elk": "100",
                "elk_direction": "DOWN",
                "elk_algorithm": "layered",
                "description": "ELK automatic layout (recommended for complex subflows)",
                "auto_layout": True,
                "subflow_optimized": True
            },
            "dagre": {
                "file1_offset": {"x": 0, "y": 0},
                "file2_offset": {"x": 0, "y": 0},  # Let Dagre handle positioning
                "node_separation": 100,
                "rank_separation": 150,
                "dagre_direction": "TB",  # Top to Bottom
                "description": "Dagre automatic layout (good for simple hierarchies)",
                "auto_layout": True
            },
            "hierarchical": {
                "file1_offset": {"x": 0, "y": 0},
                "file2_offset": {"x": 1200, "y": 0},  # Increased spacing
                "node_spacing": {"x": 300, "y": 120},  # Increased spacing
                "level_spacing": 180,  # Increased spacing
                "description": "Top-down hierarchical layout with increased spacing"
            },
            "force": {
                "file1_offset": {"x": 0, "y": 0},
                "file2_offset": {"x": 800, "y": 0},
                "node_spacing": {"x": 200, "y": 150},  # Increased spacing
                "level_spacing": 200,  # Increased spacing
                "description": "Force-directed layout with better spacing"
            },
            "circular": {
                "file1_offset": {"x": 0, "y": 0},
                "file2_offset": {"x": 1000, "y": 0},  # Increased spacing
                "radius": 250,  # Increased radius
                "center_offset": 400,  # Increased offset
                "description": "Circular layout with larger radius"
            },
            "manual": {
                "file1_offset": {"x": 0, "y": 0},
                "file2_offset": {"x": 1400, "y": 0},  # Increased spacing
                "node_spacing": {"x": 400, "y": 160},  # Increased spacing
                "level_spacing": 200,  # Increased spacing
                "description": "Manual positioning with optimal spacing"
            }
        }
        return configs.get(layout_type, configs["dagre"])

    def _prepare_nodes_for_auto_layout(self, nodes: List[Dict], layout_type: str) -> List[Dict]:
        """Prepare nodes for auto-layout libraries like Dagre or ELK."""
        if layout_type == "dagre":
            # For Dagre, set minimal positions and add layout hints
            for i, node in enumerate(nodes):
                # Set initial positions (Dagre will override these)
                node['position'] = {"x": 0, "y": 0}

                # Add Dagre-specific data
                node['data']['dagre'] = {
                    "rank": node['data'].get('level', 0),  # Hierarchy level
                    "order": i  # Order within level
                }

                # Set node dimensions for better layout
                node_type = node['data'].get('type', 'default')
                if node_type == 'file':
                    node['style']['width'] = 200
                    node['style']['height'] = 60
                elif node_type == 'function':
                    node['style']['width'] = 180
                    node['style']['height'] = 50
                elif node_type == 'import_group':
                    node['style']['width'] = 160
                    node['style']['height'] = 40
                elif node_type == 'similarity_comment':
                    node['style']['width'] = 250
                    node['style']['height'] = 80
                else:
                    node['style']['width'] = 140
                    node['style']['height'] = 40

        elif layout_type == "elk":
            # For ELK, set minimal positions and add ELK-specific properties optimized for subflows
            for i, node in enumerate(nodes):
                node['position'] = {"x": 0, "y": 0}

                # Enhanced ELK-specific data for subflows
                node['data']['elk'] = {
                    "layoutOptions": {
                        "elk.algorithm": "layered",
                        "elk.direction": "DOWN",
                        "elk.spacing.nodeNode": "120",
                        "elk.layered.spacing.nodeNodeBetweenLayers": "200",
                        "elk.spacing.componentComponent": "100",
                        "elk.hierarchyHandling": "INCLUDE_CHILDREN",
                        "elk.layered.thoroughness": "7",
                        "elk.layered.priority.straightness": "7"
                    }
                }

                # Enhanced dimensions for ELK with subflow awareness
                node_type = node['data'].get('type', 'default')
                if node_type == 'file_subflow':
                    # Group/subflow containers need larger dimensions
                    # Extract numeric values from strings like "600px"
                    min_width_str = node.get('style', {}).get('minWidth', '600px')
                    min_height_str = node.get('style', {}).get('minHeight', '400px')

                    # Convert string values to integers (remove 'px' suffix)
                    try:
                        min_width = int(min_width_str.replace('px', '')) if isinstance(min_width_str, str) else int(
                            min_width_str)
                        min_height = int(min_height_str.replace('px', '')) if isinstance(min_height_str, str) else int(
                            min_height_str)
                    except (ValueError, TypeError):
                        min_width = 600
                        min_height = 400

                    node['width'] = max(600, min_width)
                    node['height'] = max(400, min_height)
                    # Special ELK options for group nodes
                    node['data']['elk']['layoutOptions'].update({
                        "elk.algorithm": "layered",
                        "elk.spacing.nodeNode": "80",
                        "elk.padding": "[top=40,left=30,bottom=30,right=30]"
                    })
                elif node_type == 'function':
                    node['width'] = 200
                    node['height'] = 60
                    # Mark as child node for proper hierarchy
                    if node.get('parentNode'):
                        node['data']['elk']['layoutOptions']['elk.hierarchy'] = 'CHILD'
                elif node_type == 'import_group':
                    node['width'] = 180
                    node['height'] = 50
                elif node_type == 'similarity_comment':
                    node['width'] = 280
                    node['height'] = 100
                else:
                    node['width'] = 160
                    node['height'] = 45

        return nodes

    def _generate_file_flow_nodes_with_layout(self, tokens: List[Dict[str, Any]], source_code: str,
                                              filename: str, file_prefix: str, offset: Dict[str, int],
                                              node_id_counter: int, shared_blocks: List[Dict],
                                              layout_type: str) -> tuple:
        """Generate React Flow nodes with layout-aware positioning using subflows for files."""
        nodes = []
        edges = []

        layout_config = self._get_layout_config(layout_type)

        # Create file subflow container
        file_node_id = f"{file_prefix}_root"

        # Extract functions and imports to calculate subflow size
        functions = self._extract_functions_with_positions(tokens, source_code)
        imports = self._extract_imports(tokens, source_code)

        # Calculate subflow dimensions based on content
        content_count = len(functions) + (1 if imports else 0)
        subflow_width = max(400, content_count * 80 + 200)
        subflow_height = max(300, content_count * 100 + 150)

        # Create file subflow node
        file_subflow = {
            "id": file_node_id,
            "type": "group",  # Use group type for subflow container
            "position": {"x": offset["x"], "y": offset["y"]},
            "data": {
                "label": f"📁 {filename}",
                "type": "file_subflow",
                "filename": filename,
                "level": 0,
                "functions_count": len(functions),
                "imports_count": len(imports)
            },
            "style": {
                "background": "linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%)",
                "border": "3px solid #1976d2",
                "borderRadius": "16px",
                "padding": "20px",
                "fontWeight": "bold",
                "boxShadow": "0 6px 16px rgba(25,118,210,0.3)",
                "minWidth": f"{subflow_width}px",
                "minHeight": f"{subflow_height}px",
                "textAlign": "center",
                "opacity": 0.95
            },
            "className": "file-subflow-container",
            # Subflow specific properties
            "expandParent": True,
            "extent": "parent",
            "draggable": True,
            "selectable": True
        }

        nodes.append(file_subflow)

        # Position elements inside the subflow
        internal_x = 30  # Relative to subflow
        internal_y = 60  # Below the subflow title

        # Add imports group inside subflow
        if imports:
            import_group_id = f"{file_prefix}_imports_group"
            import_node = {
                "id": import_group_id,
                "type": "default",
                "position": {"x": offset["x"] + internal_x, "y": offset["y"] + internal_y},
                "data": {
                    "label": f"📦 Imports ({len(imports)})",
                    "type": "import_group",
                    "level": 1,
                    "imports": [imp["module"] for imp in imports]
                },
                "style": {
                    "background": "linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%)",
                    "border": "2px solid #4caf50",
                    "borderRadius": "8px",
                    "padding": "8px",
                    "fontSize": "12px",
                    "boxShadow": "0 2px 6px rgba(76,175,80,0.2)",
                    "minWidth": "160px"
                },
                "parentNode": file_node_id,  # Make it a child of the subflow
                "extent": "parent",
                "draggable": True
            }
            nodes.append(import_node)
            internal_y += 80

        # Group functions by similarity for better organization
        similar_functions = []
        regular_functions = []

        for func_name, func_data in functions.items():
            similar_block = self._find_similarity_for_function(func_name, shared_blocks, file_prefix)
            if similar_block:
                similar_functions.append((func_name, func_data, similar_block))
            else:
                regular_functions.append((func_name, func_data, None))

        # Add similar functions first (highlighted within subflow)
        for i, (func_name, func_data, similar_block) in enumerate(similar_functions):
            func_node_id = f"{file_prefix}_{func_name}"

            position = self._calculate_subflow_child_position(
                i, len(similar_functions), internal_x, internal_y, offset, layout_config
            )

            # Enhanced styling for similar functions
            func_label = f"⚡ {func_data.get('function_name', 'unknown')}"
            func_label += f" (🔗 {similar_block['similarity_score']:.1%})"

            function_node = {
                "id": func_node_id,
                "type": "default",
                "position": position,
                "data": {
                    "label": func_label,
                    "type": "function",
                    "function_name": func_data.get('function_name', 'unknown'),
                    "start_line": func_data.get('start_line', 0),
                    "end_line": func_data.get('end_line', 0),
                    "has_similarity": True,
                    "similarity_score": similar_block['similarity_score'],
                    "level": 2,
                    "is_similar": True
                },
                "style": {
                    "background": "linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%)",
                    "border": "3px solid #f44336",
                    "borderRadius": "12px",
                    "padding": "12px",
                    "fontWeight": "600",
                    "boxShadow": "0 4px 12px rgba(244,67,54,0.4)",
                    "minWidth": "200px"
                },
                "parentNode": file_node_id,  # Make it a child of the subflow
                "extent": "parent",
                "draggable": True
            }

            nodes.append(function_node)

            # Add similarity comment as a floating annotation
            comment_node_id = f"{func_node_id}_similarity_comment"
            comment_position = {
                "x": position["x"] + 220,
                "y": position["y"] + 10
            }

            other_code = ""
            if file_prefix == "file1":
                other_code = similar_block.get('file2_code_block', '')[:120] + "..."
            else:
                other_code = similar_block.get('file1_code_block', '')[:120] + "..."

            comment_node = {
                "id": comment_node_id,
                "type": "annotation",  # Use annotation type for comments
                "position": comment_position,
                "data": {
                    "label": f"💭 Similar to {similar_block.get('file2_filename' if file_prefix == 'file1' else 'file1_filename', 'other file')}\n{other_code}",
                    "type": "similarity_comment",
                    "similarity_score": similar_block['similarity_score'],
                    "level": 2
                },
                "style": {
                    "background": "linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%)",
                    "border": "2px dashed #9c27b0",
                    "borderRadius": "10px",
                    "padding": "10px",
                    "fontSize": "10px",
                    "maxWidth": "280px",
                    "boxShadow": "0 3px 10px rgba(156,39,176,0.3)",
                    "opacity": 0.9
                },
                "parentNode": file_node_id,  # Also a child of the subflow
                "extent": "parent",
                "draggable": True
            }

            nodes.append(comment_node)

            # Connection from function to comment
            edges.append({
                "id": f"edge_{func_node_id}_to_{comment_node_id}",
                "source": func_node_id,
                "target": comment_node_id,
                "type": "bezier",
                "animated": True,
                "style": {"stroke": "#9c27b0", "strokeDasharray": "5,5", "strokeWidth": 2}
            })

            internal_y += 140

        # Add regular functions
        for i, (func_name, func_data, _) in enumerate(regular_functions):
            func_node_id = f"{file_prefix}_{func_name}"

            position = self._calculate_subflow_child_position(
                i, len(regular_functions), internal_x, internal_y, offset, layout_config
            )

            function_node = {
                "id": func_node_id,
                "type": "default",
                "position": position,
                "data": {
                    "label": f"⚙️ {func_data.get('function_name', 'unknown')}",
                    "type": "function",
                    "function_name": func_data.get('function_name', 'unknown'),
                    "start_line": func_data.get('start_line', 0),
                    "end_line": func_data.get('end_line', 0),
                    "has_similarity": False,
                    "similarity_score": 0,
                    "level": 2,
                    "is_similar": False
                },
                "style": {
                    "background": "linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%)",
                    "border": "2px solid #ff9800",
                    "borderRadius": "10px",
                    "padding": "10px",
                    "boxShadow": "0 3px 8px rgba(255,152,0,0.2)",
                    "minWidth": "180px"
                },
                "parentNode": file_node_id,  # Make it a child of the subflow
                "extent": "parent",
                "draggable": True
            }

            nodes.append(function_node)
            internal_y += 100

        # Analyze function calls and create call flow edges (within subflow)
        call_edges = self._analyze_function_calls_in_subflow(tokens, source_code, functions, file_prefix)
        edges.extend(call_edges)

        return nodes, edges, node_id_counter

    def _calculate_subflow_child_position(self, index: int, total: int, base_x: int, base_y: int,
                                          offset: Dict[str, int], layout_config: Dict[str, Any]) -> Dict[str, int]:
        """Calculate position for child nodes within a subflow."""
        return {
            "x": offset["x"] + base_x + (index % 2) * 220,  # Two columns within subflow
            "y": offset["y"] + base_y + (index // 2) * 100  # Rows of pairs
        }

    def _analyze_function_calls_in_subflow(self, tokens: List[Dict[str, Any]], source_code: str,
                                           functions: Dict, file_prefix: str) -> List[Dict]:
        """Analyze function calls within a subflow and create internal edges."""
        call_edges = []

        # Extract function names for reference
        function_names = [func_data.get('function_name', 'unknown') for func_data in functions.values()]
        function_node_map = {
            func_data.get('function_name', 'unknown'): f"{file_prefix}_{func_name}"
            for func_name, func_data in functions.items()
        }

        # Look for function calls in source code
        source_lines = source_code.split('\n') if source_code else []

        for i, line in enumerate(source_lines):
            for func_name in function_names:
                if f"{func_name}(" in line and not line.strip().startswith('def '):
                    # Found a function call
                    calling_function = self._find_containing_function(i + 1, source_lines, function_names)

                    if calling_function and calling_function != func_name:
                        caller_id = function_node_map.get(calling_function)
                        callee_id = function_node_map.get(func_name)

                        if caller_id and callee_id:
                            call_edges.append({
                                "id": f"call_edge_{caller_id}_to_{callee_id}",
                                "source": caller_id,
                                "target": callee_id,
                                "type": "smoothstep",
                                "animated": True,
                                "style": {
                                    "stroke": "#2196f3",
                                    "strokeWidth": 2,
                                    "strokeDasharray": "8,4"
                                },
                                "data": {
                                    "type": "function_call",
                                    "line": i + 1
                                },
                                "label": "calls",
                                "labelStyle": {
                                    "fill": "#2196f3",
                                    "fontWeight": 600,
                                    "fontSize": "10px"
                                }
                            })

        return call_edges

    def _extract_imports(self, tokens: List[Dict[str, Any]], source_code: str) -> List[Dict]:
        """Extract import statements and their details."""
        imports = []
        source_lines = source_code.split('\n') if source_code else []

        for i, line in enumerate(source_lines):
            line = line.strip()
            if line.startswith('import '):
                # Handle 'import module'
                module = line[7:].split()[0].split('.')[0]  # Get first part
                imports.append({
                    'module': module,
                    'type': 'import',
                    'line': i + 1
                })
            elif line.startswith('from '):
                # Handle 'from module import ...'
                parts = line.split()
                if len(parts) >= 4 and parts[2] == 'import':
                    module = parts[1]
                    imports.append({
                        'module': module,
                        'type': 'from_import',
                        'line': i + 1
                    })

        return imports

    def _find_similarity_for_function(self, func_name: str, shared_blocks: List[Dict], file_prefix: str) -> Dict:
        """Find similarity block for a given function."""
        for block in shared_blocks:
            if file_prefix == "file1" and block.get('file1_function') == func_name:
                return block
            elif file_prefix == "file2" and block.get('file2_function') == func_name:
                return block
        return None

    def _generate_similarity_edges(self, shared_blocks: List[Dict], all_nodes: List[Dict]) -> List[Dict]:
        """Generate edges connecting similar functions between files."""
        similarity_edges = []

        # Create a mapping of function names to node IDs
        node_map = {}
        for node in all_nodes:
            if node['data'].get('type') == 'function':
                node_map[node['data']['function_name']] = node['id']

        for i, block in enumerate(shared_blocks):
            file1_func = block.get('file1_function', '')
            file2_func = block.get('file2_function', '')

            # Extract actual function names from the prefixed names
            file1_func_name = file1_func.split('_', 2)[-1] if '_' in file1_func else file1_func
            file2_func_name = file2_func.split('_', 2)[-1] if '_' in file2_func else file2_func

            # Find corresponding nodes
            file1_node_id = f"file1_{file1_func}"
            file2_node_id = f"file2_{file2_func}"

            # Check if both nodes exist
            file1_node_exists = any(node['id'] == file1_node_id for node in all_nodes)
            file2_node_exists = any(node['id'] == file2_node_id for node in all_nodes)

            if file1_node_exists and file2_node_exists:
                similarity_edges.append({
                    "id": f"similarity_edge_{i}",
                    "source": file1_node_id,
                    "target": file2_node_id,
                    "type": "straight",
                    "animated": True,
                    "style": {
                        "stroke": "#f44336",
                        "strokeWidth": 3,
                        "strokeDasharray": "10,5"
                    },
                    "data": {
                        "type": "similarity",
                        "similarity_score": block.get('similarity_score', 0),
                        "label": f"{block.get('similarity_score', 0):.1%} similar"
                    },
                    "label": f"{block.get('similarity_score', 0):.1%}",
                    "labelStyle": {
                        "fill": "#f44336",
                        "fontWeight": 700,
                        "fontSize": "12px"
                    },
                    "labelBgPadding": [10, 6],
                    "labelBgBorderRadius": 6,
                    "labelBgStyle": {
                        "fill": "#ffffff",
                        "color": "#f44336",
                        "fillOpacity": 0.95,
                        "stroke": "#f44336",
                        "strokeWidth": 1
                    }
                })

        return similarity_edges

    def _find_containing_function(self, line_num: int, source_lines: List[str], function_names: List[str]) -> str:
        """Find which function contains a given line number."""
        # Look backwards from the line to find the containing function
        for i in range(line_num - 1, -1, -1):
            line = source_lines[i].strip()
            if line.startswith('def '):
                # Extract function name
                func_part = line[4:].split('(')[0].strip()
                if func_part in function_names:
                    return func_part
        return None

    def _apply_layout_algorithm(self, nodes: List[Dict], edges: List[Dict], layout_type: str) -> List[Dict]:
        """Apply layout algorithm to optimize subflow positioning."""
        if layout_type == "hierarchical":
            return self._apply_hierarchical_subflow_layout(nodes, edges)
        elif layout_type == "force":
            return self._apply_force_directed_subflow_layout(nodes, edges)
        elif layout_type == "circular":
            return self._apply_circular_subflow_layout(nodes, edges)
        else:
            return nodes  # Return as-is for manual layout

    def _apply_hierarchical_subflow_layout(self, nodes: List[Dict], edges: List[Dict]) -> List[Dict]:
        """Apply hierarchical layout to subflow containers."""
        subflows = [n for n in nodes if n['data'].get('type') == 'file_subflow']

        # Position subflows vertically with proper spacing
        y_offset = 50
        for i, subflow in enumerate(subflows):
            subflow['position']['x'] = 50 + (i * 800)  # Side by side
            subflow['position']['y'] = y_offset

        return nodes

    def _apply_force_directed_subflow_layout(self, nodes: List[Dict], edges: List[Dict]) -> List[Dict]:
        """Apply force-directed layout to subflow containers only."""
        subflows = [n for n in nodes if n['data'].get('type') == 'file_subflow']

        # Simple positioning for subflows
        for i, subflow in enumerate(subflows):
            subflow['position']['x'] = 100 + (i * 700)
            subflow['position']['y'] = 100

        return nodes

    def _apply_circular_subflow_layout(self, nodes: List[Dict], edges: List[Dict]) -> List[Dict]:
        """Apply circular layout to subflow containers."""
        subflows = [n for n in nodes if n['data'].get('type') == 'file_subflow']

        if len(subflows) <= 2:
            # Simple side-by-side for two subflows
            for i, subflow in enumerate(subflows):
                subflow['position']['x'] = 200 + (i * 800)
                subflow['position']['y'] = 200

        else:
            # Circular arrangement for more subflows
            center_x, center_y = 600, 400
            radius = 300
            for i, subflow in enumerate(subflows):
                angle = 2 * math.pi * i / len(subflows)
                subflow['position']['x'] = center_x + int(radius * math.cos(angle))
                subflow['position']['y'] = center_y + int(radius * math.sin(angle))

        return nodes
