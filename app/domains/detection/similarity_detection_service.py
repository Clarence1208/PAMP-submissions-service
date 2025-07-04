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

                if func_similarity['similarity_score'] > 0.8:
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
            'average_similarity': sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0,
            'functions_file1': len(functions1),
            'functions_file2': len(functions2),
            'shared_percentage': len(shared_blocks) / max(len(functions1),
                                                          len(functions2)) * 100 if functions1 or functions2 else 0.0
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
        """Compare similarity between two function token sequences using improved algorithm."""
        # Prepare tokens for similarity comparison
        sim_tokens1 = self.prepare_for_similarity(func1_tokens)
        sim_tokens2 = self.prepare_for_similarity(func2_tokens)

        # 1. STRUCTURAL SEQUENCE SIMILARITY (most important)
        # Create normalized sequences focusing on control flow and operations
        seq1 = self._create_structural_sequence(sim_tokens1)
        seq2 = self._create_structural_sequence(sim_tokens2)
        
        structural_similarity = self._sequence_similarity(seq1, seq2)

        # 2. TOKEN TYPE PATTERN SIMILARITY
        types1 = [token['type'] for token in sim_tokens1]
        types2 = [token['type'] for token in sim_tokens2]
        
        # Use sequence similarity instead of just set intersection
        type_sequence_similarity = self._sequence_similarity(types1, types2)
        
        # Also check set-based type similarity (for different order but same operations)
        common_types = set(types1) & set(types2)
        total_types = set(types1) | set(types2)
        type_set_similarity = len(common_types) / len(total_types) if total_types else 0.0

        # 3. LOGICAL FLOW SIMILARITY
        # Extract logical patterns (if-else, loops, returns, etc.)
        flow1 = self._extract_logical_flow(sim_tokens1)
        flow2 = self._extract_logical_flow(sim_tokens2)
        flow_similarity = self._sequence_similarity(flow1, flow2)

        # 4. OPERATION SIMILARITY  
        # Extract mathematical/logical operations
        ops1 = self._extract_operations(sim_tokens1)
        ops2 = self._extract_operations(sim_tokens2)
        operation_similarity = self._sequence_similarity(ops1, ops2)

        # WEIGHTED COMBINATION (emphasizing structure over text)
        # Add penalty for very different function lengths
        len1, len2 = len(sim_tokens1), len(sim_tokens2)
        length_ratio = min(len1, len2) / max(len1, len2) if max(len1, len2) > 0 else 0.0
        length_penalty = 1.0 if length_ratio > 0.5 else (0.8 if length_ratio > 0.3 else 0.6)
        
        similarity_score = (
            structural_similarity * 0.4 +      # Most important: overall structure
            type_sequence_similarity * 0.25 +  # Token sequence patterns
            flow_similarity * 0.2 +            # Control flow logic
            operation_similarity * 0.1 +       # Mathematical operations
            type_set_similarity * 0.05         # Basic type overlap
        ) * length_penalty  # Apply length penalty

        return {
            'similarity_score': similarity_score,
            'structural_similarity': structural_similarity,
            'type_sequence_similarity': type_sequence_similarity,
            'type_set_similarity': type_set_similarity,
            'flow_similarity': flow_similarity,
            'operation_similarity': operation_similarity,
            'common_patterns': list(common_types)
        }

    def _create_structural_sequence(self, tokens: List[Dict[str, Any]]) -> List[str]:
        """Create a normalized structural sequence from tokens."""
        sequence = []
        for token in tokens:
            token_type = token.get('type', '')
            
            # Map similar concepts to same structural element
            if token_type in ['function_definition', 'method_definition']:
                sequence.append('FUNC_DEF')
            elif token_type in ['if_statement', 'elif_clause']:
                sequence.append('CONDITIONAL')
            elif token_type == 'else_clause':
                sequence.append('ELSE')
            elif token_type in ['for_statement', 'while_statement']:
                sequence.append('LOOP')
            elif token_type == 'return_statement':
                sequence.append('RETURN')
            elif token_type in ['assignment', 'augmented_assignment']:
                sequence.append('ASSIGN')
            elif token_type in ['binary_operator', 'unary_operator']:
                sequence.append('OPERATOR')
            elif token_type in ['call']:
                sequence.append('CALL')
            elif token_type in ['list', 'tuple', 'dictionary', 'set']:
                sequence.append('COLLECTION')
            elif token_type in ['string', 'integer', 'float']:
                sequence.append('LITERAL')
            elif token_type == 'identifier':
                sequence.append('VAR')
            else:
                sequence.append(token_type.upper())
        
        return sequence

    def _extract_logical_flow(self, tokens: List[Dict[str, Any]]) -> List[str]:
        """Extract logical flow patterns from tokens."""
        flow = []
        for token in tokens:
            token_type = token.get('type', '')
            if token_type in ['if_statement', 'elif_clause', 'else_clause', 
                            'for_statement', 'while_statement', 'break_statement', 
                            'continue_statement', 'return_statement', 'try_statement',
                            'except_clause', 'finally_clause']:
                flow.append(token_type)
        return flow

    def _extract_operations(self, tokens: List[Dict[str, Any]]) -> List[str]:
        """Extract mathematical and logical operations from tokens."""
        operations = []
        for token in tokens:
            token_type = token.get('type', '')
            token_text = token.get('text', '').strip()
            
            if token_type in ['binary_operator', 'unary_operator', 'comparison_operator', 
                            'boolean_operator', 'augmented_assignment']:
                # Normalize common operations
                if token_text in ['+', '-', '*', '/', '//', '%', '**']:
                    operations.append('MATH_OP')
                elif token_text in ['==', '!=', '<', '>', '<=', '>=']:
                    operations.append('COMPARE_OP')
                elif token_text in ['and', 'or', 'not']:
                    operations.append('LOGIC_OP')
                else:
                    operations.append('OPERATOR')
        return operations

    def _sequence_similarity(self, seq1: List[str], seq2: List[str]) -> float:
        """Calculate similarity between two sequences using longest common subsequence."""
        if not seq1 or not seq2:
            return 0.0
        
        # Use dynamic programming to find longest common subsequence
        m, n = len(seq1), len(seq2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if seq1[i-1] == seq2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        lcs_length = dp[m][n]
        max_length = max(m, n)
        
        # Calculate similarity as LCS ratio with bonus for exact matches
        if m == n and lcs_length == m:
            return 1.0  # Perfect match
        
        return lcs_length / max_length








