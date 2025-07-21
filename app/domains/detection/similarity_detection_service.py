"""
Similarity Detection Service
Handles code similarity analysis, comparison, and shared code block detection.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List

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
            "if_statement",
            "else_clause",
            "elif_clause",
            "for_statement",
            "while_statement",
            "break_statement",
            "continue_statement",
            "function_definition",
            "class_definition",
            "method_definition",
            "call",
            "attribute",
            "subscript",
            "import_statement",
            "import_from_statement",
            "return_statement",
            "yield_statement",
            "try_statement",
            "except_clause",
            "finally_clause",
            "with_statement",
            "assert_statement",
            "list",
            "dictionary",
            "set",
            "tuple",
            "list_comprehension",
            "dictionary_comprehension",
            "set_comprehension",
            "lambda",
            "generator_expression",
            "binary_operator",
            "unary_operator",
            "comparison_operator",
            "boolean_operator",
            "assignment",
            "augmented_assignment",
            "decorated_definition",
        }

        # Types normalized to generic placeholders
        normalize_types = {
            "string": "<STRING>",
            "integer": "<NUMBER>",
            "float": "<NUMBER>",
            "identifier": "<VAR>",
            "comment": "<COMMENT>",
        }

        # Types to completely filter out
        skip_types = {"comment", "ERROR"}  # Parsing errors

        for token in tokens:
            token_type = token.get("type", "")

            # Skip irrelevant types
            if token_type in skip_types:
                continue

            if token_type in keep_types:
                similarity_tokens.append({"type": token_type, "text": token.get("text", ""), "normalized": False})
                continue

            # Normalize certain types
            if token_type in normalize_types:
                similarity_tokens.append({"type": token_type, "text": normalize_types[token_type], "normalized": True})
                continue

            similarity_tokens.append({"type": token_type, "text": token.get("text", ""), "normalized": False})

        return similarity_tokens

    def get_similarity_signature(self, tokens: List[Dict[str, Any]]) -> str:
        """
        Generate a compact signature for similarity comparison.
        This creates a normalized string representation focusing on structure.
        """
        similarity_tokens = self.prepare_for_similarity(tokens)

        signature_parts = []
        for token in similarity_tokens:
            if token["normalized"]:
                # For normalized tokens, just use the placeholder
                signature_parts.append(token["text"])
            else:
                # For structural tokens, use type + simplified text
                token_text = token["text"].strip()
                if len(token_text) > 20:
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

        sig1_parts = signature1.split(" | ")
        sig2_parts = signature2.split(" | ")

        # Calculate overlap
        common_parts = set(sig1_parts) & set(sig2_parts)
        total_unique_parts = set(sig1_parts) | set(sig2_parts)

        jaccard_similarity = len(common_parts) / len(total_unique_parts) if total_unique_parts else 0

        # Structure similarity (focusing on types only)
        types1 = [token["type"] for token in sim_tokens1]
        types2 = [token["type"] for token in sim_tokens2]

        common_types = set(types1) & set(types2)
        total_types = set(types1) | set(types2)

        type_similarity = len(common_types) / len(total_types) if total_types else 0

        return {
            "jaccard_similarity": jaccard_similarity,
            "type_similarity": type_similarity,
            "common_elements": len(common_parts),
            "total_unique_elements": len(total_unique_parts),
            "signature1_length": len(sig1_parts),
            "signature2_length": len(sig2_parts),
            "common_types": list(common_types),
            "signatures": {
                "file1": signature1[:100] + "..." if len(signature1) > 100 else signature1,
                "file2": signature2[:100] + "..." if len(signature2) > 100 else signature2,
            },
        }

    def detect_shared_code_blocks(
        self,
        source1: str,
        source2: str,
        file1_name: str = "",
        file2_name: str = "",
        file1_path: Path = None,
        file2_path: Path = None,
        tokenization_service=None,
    ) -> Dict[str, Any]:
        """
        Detect shared code blocks between two source files using Tree-sitter queries.

        Args:
            source1: Original source code of first file
            source2: Original source code of second file
            file1_name: Name of the first file (for reporting)
            file2_name: Name of the second file (for reporting)
            file1_path: Path object for first file (for language detection)
            file2_path: Path object for second file (for language detection)
            tokenization_service: Instance of TokenizationService for function extraction
        """
        if not tokenization_service:
            logger.warning("No tokenization service provided, cannot extract functions")
            return {
                "shared_blocks": [],
                "total_shared_blocks": 0,
                "average_similarity": 0.0,
                "functions_file1": 0,
                "functions_file2": 0,
                "shared_percentage": 0.0,
            }

        # Extract functions from both files using the improved tokenization service
        functions1 = tokenization_service.extract_functions_with_positions(source1, file1_path)
        functions2 = tokenization_service.extract_functions_with_positions(source2, file2_path)

        logger.info(f"Extracted {len(functions1)} functions from {file1_name}")
        logger.info(f"Extracted {len(functions2)} functions from {file2_name}")

        # PRE-TOKENIZE ALL FUNCTIONS ONCE to avoid repeated tokenization calls
        logger.debug(
            f"Pre-tokenizing {len(functions1)} functions from file1 and {len(functions2)} functions from file2"
        )

        # Tokenize all functions from file1 once
        func1_tokens_cache = {}
        for func1_id, func1_data in functions1.items():
            func1_tokens = tokenization_service.tokenize(func1_data["code_block"], file1_path)
            func1_tokens_cache[func1_id] = func1_tokens

        # Tokenize all functions from file2 once
        func2_tokens_cache = {}
        for func2_id, func2_data in functions2.items():
            func2_tokens = tokenization_service.tokenize(func2_data["code_block"], file2_path)
            func2_tokens_cache[func2_id] = func2_tokens

        logger.debug(
            f"Pre-tokenization complete. Starting {len(functions1)} × {len(functions2)} = {len(functions1) * len(functions2)} function comparisons"
        )

        # Fast comparison using pre-tokenized data - NO MORE TOKENIZATION CALLS IN LOOP
        shared_blocks = []
        similarity_scores = []

        # Compare all function pairs using pre-tokenized data
        for func1_id, func1_data in functions1.items():
            for func2_id, func2_data in functions2.items():
                # Skip comparison for functions with less than 5 lines (too trivial for meaningful comparison)
                func1_line_count = func1_data["end_line"] - func1_data["start_line"] + 1
                func2_line_count = func2_data["end_line"] - func2_data["start_line"] + 1

                if func1_line_count < 5 or func2_line_count < 5:
                    logger.debug(
                        f"Skipping comparison of short functions: {func1_data['function_name']} ({func1_line_count} lines) vs {func2_data['function_name']} ({func2_line_count} lines)"
                    )
                    continue

                # Use pre-tokenized data - NO TOKENIZATION CALLS HERE
                func1_tokens = func1_tokens_cache[func1_id]
                func2_tokens = func2_tokens_cache[func2_id]

                # Compare function similarity
                func_similarity = self._compare_function_similarity(func1_tokens, func2_tokens)

                logger.debug(
                    f"Comparing {func1_data['function_name']} with {func2_data['function_name']}: {func_similarity['similarity_score']:.2f}"
                )

                if func_similarity["similarity_score"] > 0.7:

                    shared_block = {
                        "file1_function": func1_data["function_name"],
                        "file2_function": func2_data["function_name"],
                        "file1_filename": file1_name,
                        "file2_filename": file2_name,
                        "similarity_score": func_similarity["similarity_score"],
                        "common_patterns": func_similarity["common_patterns"],
                        "file1_code_block": func1_data["code_block"],
                        "file2_code_block": func2_data["code_block"],
                        "file1_start_line": func1_data["start_line"],
                        "file1_end_line": func1_data["end_line"],
                        "file2_start_line": func2_data["start_line"],
                        "file2_end_line": func2_data["end_line"],
                        "file1_language": func1_data.get("language", "unknown"),
                        "file2_language": func2_data.get("language", "unknown"),
                        "file1_node_type": func1_data.get("node_type", "unknown"),
                        "file2_node_type": func2_data.get("node_type", "unknown"),
                    }
                    shared_blocks.append(shared_block)
                    similarity_scores.append(func_similarity["similarity_score"])

        return {
            "shared_blocks": shared_blocks,
            "total_shared_blocks": len(shared_blocks),
            "average_similarity": sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0,
            "functions_file1": len(functions1),
            "functions_file2": len(functions2),
            "shared_percentage": (
                len(shared_blocks) / max(len(functions1), len(functions2)) * 100 if functions1 or functions2 else 0.0
            ),
        }

    def detect_shared_code_blocks_with_cache(
        self,
        source1: str,
        source2: str,
        file1_name: str = "",
        file2_name: str = "",
        file1_path: Path = None,
        file2_path: Path = None,
        tokenization_service=None,
        submission1_id: str = None,
        submission2_id: str = None,
        project1_root: Path = None,
        project2_root: Path = None,
    ) -> Dict[str, Any]:
        """
        Cache-aware version of detect_shared_code_blocks that leverages tokenization cache
        when submission context is available.

        Args:
            source1: Original source code of first file
            source2: Original source code of second file
            file1_name: Name of the first file (for reporting)
            file2_name: Name of the second file (for reporting)
            file1_path: Path object for first file (for language detection)
            file2_path: Path object for second file (for language detection)
            tokenization_service: Instance of TokenizationService for function extraction
            submission1_id: UUID of first submission for cache lookup
            submission2_id: UUID of second submission for cache lookup
            project1_root: Root path of first project for relative path calculation
            project2_root: Root path of second project for relative path calculation
        """
        if not tokenization_service:
            logger.warning("No tokenization service provided, cannot extract functions")
            return {
                "shared_blocks": [],
                "total_shared_blocks": 0,
                "average_similarity": 0.0,
                "functions_file1": 0,
                "functions_file2": 0,
                "shared_percentage": 0.0,
            }

        # Extract functions from both files using cache when context is available
        if submission1_id and file1_path and project1_root:
            # Use cached function extraction
            functions1 = tokenization_service.extract_functions_with_positions(source1, file1_path)
        else:
            # Fallback to non-cached
            functions1 = tokenization_service.extract_functions_with_positions(source1, file1_path)

        if submission2_id and file2_path and project2_root:
            # Use cached function extraction
            functions2 = tokenization_service.extract_functions_with_positions(source2, file2_path)
        else:
            # Fallback to non-cached
            functions2 = tokenization_service.extract_functions_with_positions(source2, file2_path)

        logger.info(f"Extracted {len(functions1)} functions from {file1_name}")
        logger.info(f"Extracted {len(functions2)} functions from {file2_name}")

        # PRE-TOKENIZE ALL FUNCTIONS ONCE to avoid repeated tokenization calls
        logger.debug(
            f"Pre-tokenizing {len(functions1)} functions from file1 and {len(functions2)} functions from file2"
        )

        # Tokenize all functions from file1 once
        func1_tokens_cache = {}
        for func1_id, func1_data in functions1.items():
            if submission1_id and file1_path and project1_root:
                func1_tokens = tokenization_service.tokenize(
                    func1_data["code_block"], file1_path, submission_id=submission1_id, project_root_path=project1_root
                )
            else:
                func1_tokens = tokenization_service.tokenize(func1_data["code_block"], file1_path)
            func1_tokens_cache[func1_id] = func1_tokens

        # Tokenize all functions from file2 once
        func2_tokens_cache = {}
        for func2_id, func2_data in functions2.items():
            if submission2_id and file2_path and project2_root:
                func2_tokens = tokenization_service.tokenize(
                    func2_data["code_block"], file2_path, submission_id=submission2_id, project_root_path=project2_root
                )
            else:
                func2_tokens = tokenization_service.tokenize(func2_data["code_block"], file2_path)
            func2_tokens_cache[func2_id] = func2_tokens

        logger.debug(
            f"Pre-tokenization complete. Starting {len(functions1)} × {len(functions2)} = {len(functions1) * len(functions2)} function comparisons"
        )

        # Fast comparison using pre-tokenized data - NO MORE TOKENIZATION CALLS IN LOOP
        shared_blocks = []
        similarity_scores = []

        # Compare all function pairs using pre-tokenized data
        for func1_id, func1_data in functions1.items():
            for func2_id, func2_data in functions2.items():
                # Skip comparison for functions with less than 5 lines (too trivial for meaningful comparison)
                func1_line_count = func1_data["end_line"] - func1_data["start_line"] + 1
                func2_line_count = func2_data["end_line"] - func2_data["start_line"] + 1

                if func1_line_count < 5 or func2_line_count < 5:
                    logger.debug(
                        f"Skipping comparison of short functions: {func1_data['function_name']} ({func1_line_count} lines) vs {func2_data['function_name']} ({func2_line_count} lines)"
                    )
                    continue

                # Use pre-tokenized data - NO TOKENIZATION CALLS HERE
                func1_tokens = func1_tokens_cache[func1_id]
                func2_tokens = func2_tokens_cache[func2_id]

                # Compare function similarity
                func_similarity = self._compare_function_similarity(func1_tokens, func2_tokens)

                logger.debug(
                    f"Comparing {func1_data['function_name']} with {func2_data['function_name']}: {func_similarity['similarity_score']:.2f}"
                )

                # Only consider functions with significant similarity
                if func_similarity["similarity_score"] > 0.6:  # Threshold for shared blocks
                    shared_block = {
                        "file1_function": func1_data["function_name"],
                        "file2_function": func2_data["function_name"],
                        "file1_start_line": func1_data["start_line"],
                        "file1_end_line": func1_data["end_line"],
                        "file2_start_line": func2_data["start_line"],
                        "file2_end_line": func2_data["end_line"],
                        "file1_code_block": func1_data["code_block"],
                        "file2_code_block": func2_data["code_block"],
                        "similarity_score": func_similarity["similarity_score"],
                        "structural_similarity": func_similarity["structural_similarity"],
                        "common_elements": func_similarity["common_patterns"],
                    }
                    shared_blocks.append(shared_block)
                    similarity_scores.append(func_similarity["similarity_score"])

        # Calculate statistics
        total_shared_blocks = len(shared_blocks)
        average_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0

        result = {
            "shared_blocks": shared_blocks,
            "total_shared_blocks": total_shared_blocks,
            "average_similarity": average_similarity,
            "functions_file1": len(functions1),
            "functions_file2": len(functions2),
            "shared_percentage": (
                (total_shared_blocks / max(len(functions1), len(functions2))) * 100 if functions1 or functions2 else 0.0
            ),
        }

        logger.info(
            f"Cache-aware comparison: {total_shared_blocks} shared blocks found with average similarity {average_similarity:.3f}"
        )
        return result

    def _compare_function_similarity(
        self, func1_tokens: List[Dict[str, Any]], func2_tokens: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compare similarity between two function token sequences using improved algorithm."""
        # Prepare tokens for similarity comparison
        sim_tokens1 = self.prepare_for_similarity(func1_tokens)
        sim_tokens2 = self.prepare_for_similarity(func2_tokens)

        #  STRUCTURAL SEQUENCE SIMILARITY (most important)
        seq1 = self._create_structural_sequence(sim_tokens1)
        seq2 = self._create_structural_sequence(sim_tokens2)

        structural_similarity = self._sequence_similarity(seq1, seq2)

        #  TOKEN TYPE PATTERN SIMILARITY
        types1 = [token["type"] for token in sim_tokens1]
        types2 = [token["type"] for token in sim_tokens2]

        type_sequence_similarity = self._sequence_similarity(types1, types2)

        # Also check set-based type similarity, for different order but same operations
        common_types = set(types1) & set(types2)
        total_types = set(types1) | set(types2)
        type_set_similarity = len(common_types) / len(total_types) if total_types else 0.0

        #  LOGICAL FLOW SIMILARITY (if-else, loops, returns)
        flow1 = self._extract_logical_flow(sim_tokens1)
        flow2 = self._extract_logical_flow(sim_tokens2)
        flow_similarity = self._sequence_similarity(flow1, flow2)

        #  OPERATION SIMILARITY
        ops1 = self._extract_operations(sim_tokens1)
        ops2 = self._extract_operations(sim_tokens2)
        operation_similarity = self._sequence_similarity(ops1, ops2)

        # Add penalty for very different function lengths
        len1, len2 = len(sim_tokens1), len(sim_tokens2)
        length_ratio = min(len1, len2) / max(len1, len2) if max(len1, len2) > 0 else 0.0
        length_penalty = 1.0 if length_ratio > 0.5 else (0.8 if length_ratio > 0.3 else 0.6)

        similarity_score = (
            structural_similarity * 0.4  # Most important: overall structure
            + type_sequence_similarity * 0.25  # Token sequence patterns
            + flow_similarity * 0.2  # Control flow logic
            + operation_similarity * 0.1  # Mathematical operations
            + type_set_similarity * 0.05  # Basic type overlap
        ) * length_penalty  # Apply length penalty

        return {
            "similarity_score": similarity_score,
            "structural_similarity": structural_similarity,
            "type_sequence_similarity": type_sequence_similarity,
            "type_set_similarity": type_set_similarity,
            "flow_similarity": flow_similarity,
            "operation_similarity": operation_similarity,
            "common_patterns": list(common_types),
        }

    def _create_structural_sequence(self, tokens: List[Dict[str, Any]]) -> List[str]:
        """Create a normalized structural sequence from tokens."""
        sequence = []
        for token in tokens:
            token_type = token.get("type", "")

            # Map similar concepts to same structural element
            if token_type in ["function_definition", "method_definition"]:
                sequence.append("FUNC_DEF")
            elif token_type in ["if_statement", "elif_clause"]:
                sequence.append("CONDITIONAL")
            elif token_type == "else_clause":
                sequence.append("ELSE")
            elif token_type in ["for_statement", "while_statement"]:
                sequence.append("LOOP")
            elif token_type == "return_statement":
                sequence.append("RETURN")
            elif token_type in ["assignment", "augmented_assignment"]:
                sequence.append("ASSIGN")
            elif token_type in ["binary_operator", "unary_operator"]:
                sequence.append("OPERATOR")
            elif token_type in ["call"]:
                sequence.append("CALL")
            elif token_type in ["list", "tuple", "dictionary", "set"]:
                sequence.append("COLLECTION")
            elif token_type in ["string", "integer", "float"]:
                sequence.append("LITERAL")
            elif token_type == "identifier":
                sequence.append("VAR")
            else:
                sequence.append(token_type.upper())

        return sequence

    # fixme it should use dynamic queries
    def _extract_logical_flow(self, tokens: List[Dict[str, Any]]) -> List[str]:
        """Extract logical flow patterns from tokens (multi-language support)."""
        flow = []
        for token in tokens:
            token_type = token.get("type", "")
            # Python patterns
            if token_type in [
                "if_statement",
                "elif_clause",
                "else_clause",
                "for_statement",
                "while_statement",
                "break_statement",
                "continue_statement",
                "return_statement",
                "try_statement",
                "except_clause",
                "finally_clause",
            ]:
                flow.append(token_type)
            # Java patterns
            elif token_type in [
                "if_statement",
                "for_statement",
                "while_statement",
                "do_statement",
                "switch_statement",
                "case_statement",
                "break_statement",
                "continue_statement",
                "return_statement",
                "try_statement",
                "catch_clause",
                "finally_clause",
                "throw_statement",
            ]:
                flow.append(token_type)
            # JavaScript patterns
            elif token_type in [
                "if_statement",
                "for_statement",
                "while_statement",
                "for_in_statement",
                "for_of_statement",
                "do_statement",
                "switch_statement",
                "case_statement",
                "break_statement",
                "continue_statement",
                "return_statement",
                "try_statement",
                "catch_clause",
                "finally_clause",
                "throw_statement",
            ]:
                flow.append(token_type)
        return flow

    def _extract_operations(self, tokens: List[Dict[str, Any]]) -> List[str]:
        """Extract mathematical and logical operations from tokens (multi-language support)."""
        operations = []
        for token in tokens:
            token_type = token.get("type", "")
            token_text = token.get("text", "").strip()

            # Python/JavaScript patterns
            if token_type in [
                "binary_operator",
                "unary_operator",
                "comparison_operator",
                "boolean_operator",
                "augmented_assignment",
            ]:
                # Normalize common operations
                if token_text in ["+", "-", "*", "/", "//", "%", "**"]:
                    operations.append("MATH_OP")
                elif token_text in ["==", "!=", "<", ">", "<=", ">="]:
                    operations.append("COMPARE_OP")
                elif token_text in ["and", "or", "not"]:
                    operations.append("LOGIC_OP")
                else:
                    operations.append("OPERATOR")
            # Java patterns
            elif token_type in [
                "binary_expression",
                "unary_expression",
                "assignment_expression",
                "update_expression",
                "conditional_expression",
            ]:
                if token_text in ["+", "-", "*", "/", "%"]:
                    operations.append("MATH_OP")
                elif token_text in ["==", "!=", "<", ">", "<=", ">="]:
                    operations.append("COMPARE_OP")
                elif token_text in ["&&", "||", "!"]:
                    operations.append("LOGIC_OP")
                else:
                    operations.append("OPERATOR")
            # Method calls and assignments (common across languages)
            elif token_type in ["method_invocation", "call", "assignment"]:
                operations.append("METHOD_CALL")
        return operations

    def _sequence_similarity(self, seq1: List[str], seq2: List[str]) -> float:
        """Calculate similarity between two sequences using longest common subsequence."""
        # If both sequences are empty, they are identical
        if not seq1 and not seq2:
            return 1.0
        # If only one sequence is empty, they are completely different
        if not seq1 or not seq2:
            return 0.0

        m, n = len(seq1), len(seq2)
        lcs_matrix = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if seq1[i - 1] == seq2[j - 1]:
                    lcs_matrix[i][j] = lcs_matrix[i - 1][j - 1] + 1
                else:
                    lcs_matrix[i][j] = max(lcs_matrix[i - 1][j], lcs_matrix[i][j - 1])

        lcs_length = lcs_matrix[m][n]
        max_length = max(m, n)

        # If both sequences are identical and of the same length, return 1.0 (100% similarity)
        if m == n and lcs_length == m:
            return 1.0

        return lcs_length / max_length
