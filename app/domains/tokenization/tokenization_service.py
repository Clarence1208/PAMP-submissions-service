import logging
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from tree_sitter import Language, Parser, Query
from tree_sitter_language_pack import get_language, get_parser

from app.domains.detection.similarity_detection_service import SimilarityDetectionService
from app.domains.repositories.exceptions import (
    RepositoryFetchException,
    SubmissionValidationException,
    TemporaryDirectoryException,
    UnsupportedRepositoryException,
)
from app.domains.repositories.submission_fetcher import SubmissionFetcher
from app.domains.submissions.dto.create_submission_dto import CreateSubmissionDto
from app.domains.tokenization.custom_cache import CustomCache
from app.shared.exceptions import ValidationException

logger = logging.getLogger(__name__)


class TokenizationService:
    def __init__(self):
        """Initialize the tokenization service with tree-sitter parsers"""
        self.parsers = {}
        self.languages = {}
        self.language_mapping = {}
        self.similarity_service = SimilarityDetectionService()
        self.submission_fetcher = SubmissionFetcher()
        self.cache = CustomCache(
            hot_max_memory_mb=300, cold_db_path="/tmp/tokenization_cache", hot_threshold_percent=80.0, batch_size=50
        )
        self._setup_language_mapping()
        self._setup_parsers()

    def _setup_language_mapping(self):
        """Set up file extension to language mapping"""
        self.language_mapping = {
            # Ada
            ".ada": "ada",
            ".ads": "ada",
            ".adb": "ada",
            # Assembly
            ".asm": "asm",
            ".s": "asm",
            ".S": "asm",
            # Bash/Shell
            ".sh": "bash",
            ".bash": "bash",
            ".zsh": "bash",
            ".fish": "bash",
            # C
            ".c": "c",
            ".h": "c",
            # C#
            ".cs": "csharp",
            ".csx": "csharp",
            # C++
            ".cpp": "cpp",
            ".cxx": "cpp",
            ".cc": "cpp",
            ".c++": "cpp",
            ".hpp": "cpp",
            ".hxx": "cpp",
            ".hh": "cpp",
            ".h++": "cpp",
            # CMake
            ".cmake": "cmake",
            "CMakeLists.txt": "cmake",
            # CSS
            ".css": "css",
            ".scss": "css",
            ".sass": "css",
            ".less": "css",
            # Dart
            ".dart": "dart",
            # Dockerfile
            "Dockerfile": "dockerfile",
            ".dockerfile": "dockerfile",
            # Fortran
            ".f": "fortran",
            ".f90": "fortran",
            ".f95": "fortran",
            ".f03": "fortran",
            ".f08": "fortran",
            ".for": "fortran",
            ".ftn": "fortran",
            ".fpp": "fortran",
            # Go
            ".go": "go",
            ".mod": "gomod",
            ".sum": "gomod",
            # GraphQL
            ".graphql": "graphql",
            ".gql": "graphql",
            # Groovy
            ".groovy": "groovy",
            ".gradle": "groovy",
            # Haskell
            ".hs": "haskell",
            ".lhs": "haskell",
            # HTML
            ".html": "html",
            ".htm": "html",
            ".xhtml": "html",
            # Java
            ".java": "java",
            ".jsp": "java",
            # JavaScript
            ".js": "javascript",
            ".mjs": "javascript",
            ".jsx": "javascript",
            # JSON
            ".json": "json",
            ".jsonc": "json",
            ".json5": "json",
            # Julia
            ".jl": "julia",
            # Kotlin
            ".kt": "kotlin",
            ".kts": "kotlin",
            # Lua
            ".lua": "lua",
            # Make
            "Makefile": "make",
            "makefile": "make",
            ".mk": "make",
            ".make": "make",
            # Markdown
            ".md": "markdown",
            ".markdown": "markdown",
            ".mdown": "markdown",
            ".mkd": "markdown",
            ".mdx": "markdown",
            # MATLAB
            ".m": "matlab",
            ".mlx": "matlab",
            # OCaml
            ".ml": "ocaml",
            ".mli": "ocaml",
            # Pascal/Delphi/Object Pascal
            ".pas": "pascal",
            ".pp": "pascal",
            ".inc": "pascal",
            ".dpr": "pascal",
            ".dpk": "pascal",
            ".dfm": "pascal",
            ".fmx": "pascal",
            # Perl
            ".pl": "perl",
            ".pm": "perl",
            ".perl": "perl",
            # PHP
            ".php": "php",
            ".php3": "php",
            ".php4": "php",
            ".php5": "php",
            ".phtml": "php",
            # Python
            ".py": "python",
            ".pyi": "python",
            ".pyw": "python",
            ".pyx": "python",
            ".pxd": "python",
            ".pxi": "python",
            # R
            ".r": "r",
            ".R": "r",
            ".rmd": "r",
            ".Rmd": "r",
            # Ruby
            ".rb": "ruby",
            ".rbw": "ruby",
            ".rake": "ruby",
            ".gemspec": "ruby",
            "Rakefile": "ruby",
            "Gemfile": "ruby",
            # Rust
            ".rs": "rust",
            # Scala
            ".scala": "scala",
            ".sc": "scala",
            # Solidity
            ".sol": "solidity",
            # SQL
            ".sql": "sql",
            ".mysql": "sql",
            ".pgsql": "sql",
            ".plsql": "sql",
            # Svelte
            ".svelte": "svelte",
            # Swift
            ".swift": "swift",
            # TOML
            ".toml": "toml",
            # TypeScript
            ".ts": "typescript",
            ".tsx": "typescript",
            ".mts": "typescript",
            ".cts": "typescript",
            # Vue.js
            ".vue": "vue",
            # XML
            ".xml": "xml",
            ".xsl": "xml",
            ".xslt": "xml",
            ".xsd": "xml",
            ".wsdl": "xml",
            ".svg": "xml",
            # YAML
            ".yaml": "yaml",
            ".yml": "yaml",
        }

    def extract_supported_files_from_directory(self, directory: Path) -> List[Path]:
        """
        Extracts all files from the given directory that are supported by the tokenization service.
        Returns a list of file paths.
        """
        if not directory.is_dir():
            raise ValidationException(f"Invalid directory path: {directory}")

        supported_files = []
        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in self.language_mapping:
                supported_files.append(file_path)

        logger.info(f"Extracted {len(supported_files)} supported files from {directory}")
        return supported_files

    def _setup_parsers(self):
        """Set up tree-sitter parsers for different languages"""
        # List of languages supported by tree-sitter-language-pack
        # Based on https://pypi.org/project/tree-sitter-language-pack/
        supported_languages = [
            "ada",
            "asm",
            "bash",
            "c",
            "csharp",
            "cpp",
            "cmake",
            "css",
            "dart",
            "dockerfile",
            "fortran",
            "go",
            "gomod",
            "graphql",
            "groovy",
            "haskell",
            "html",
            "java",
            "javascript",
            "json",
            "julia",
            "kotlin",
            "lua",
            "make",
            "markdown",
            "matlab",
            "ocaml",
            "pascal",
            "perl",
            "php",
            "python",
            "r",
            "ruby",
            "rust",
            "scala",
            "solidity",
            "sql",
            "svelte",
            "swift",
            "toml",
            "typescript",
            "vue",
            "xml",
            "yaml",
        ]

        initialized_count = 0
        failed_languages = []

        for language in supported_languages:
            try:
                parser = get_parser(language)
                lang = get_language(language)
                self.parsers[language] = parser
                self.languages[language] = lang
                initialized_count += 1
                logger.debug(f"Initialized parser for {language}")
            except Exception as e:
                failed_languages.append(language)
                logger.warning(f"Failed to initialize parser for {language}: {e}")

        # Map file extensions to parsers
        for ext, lang in self.language_mapping.items():
            if lang in self.parsers:
                self.parsers[ext] = self.parsers[lang]
                self.languages[ext] = self.languages[lang]

        logger.info(
            f"Tree-sitter parsers initialized: {initialized_count}/{len(supported_languages)} languages successful"
        )
        if failed_languages:
            logger.warning(f"Failed to initialize parsers for: {', '.join(failed_languages)}")
        else:
            logger.debug("All supported languages initialized successfully")

    def _get_function_query(self, language: str) -> str:
        """Get language-specific query for extracting functions"""

        # Languages that don't have traditional functions and should be skipped
        non_function_languages = {
            "xml",
            "html",
            "css",
            "json",
            "yaml",
            "toml",
            "markdown",
            "sql",
            "cmake",
            "make",
            "dockerfile",
            "gomod",
        }

        if language in non_function_languages:
            return ""  # Return empty query for languages without functions

        # Language-specific query patterns using correct Tree-sitter node types
        query_patterns = {
            "python": """
                (function_definition
                    name: (identifier) @function.name
                ) @function.definition
                
                (class_definition
                    body: (block
                        (function_definition
                            name: (identifier) @function.method
                        ) @function.method.definition
                    )
                )
            """,
            "javascript": """
                (function_declaration
                    name: (identifier) @function.name
                ) @function.definition
                
                (method_definition
                    name: (property_identifier) @function.method
                ) @function.method.definition
                
                (arrow_function) @function.definition
                
                (function_expression
                    name: (identifier)? @function.name
                ) @function.definition
            """,
            "typescript": """
                (function_declaration
                    name: (identifier) @function.name
                ) @function.definition
                
                (method_definition
                    name: (property_identifier) @function.method
                ) @function.method.definition
                
                (arrow_function) @function.definition
                
                (function_expression
                    name: (identifier)? @function.name
                ) @function.definition
            """,
            "java": """
                (method_declaration
                    name: (identifier) @function.name
                ) @function.definition
                
                (constructor_declaration
                    name: (identifier) @function.constructor
                ) @function.definition
            """,
            "c": """
                (function_definition
                    declarator: (function_declarator
                        declarator: (identifier) @function.name
                    )
                ) @function.definition
                
                (declaration
                    declarator: (function_declarator
                        declarator: (identifier) @function.declaration
                    )
                ) @function.declaration
            """,
            "cpp": """
                (function_definition
                    declarator: (function_declarator
                        declarator: (identifier) @function.name
                    )
                ) @function.definition
                
                (template_declaration
                    (function_definition
                        declarator: (function_declarator
                            declarator: (identifier) @function.template
                        )
                    ) @function.template.definition
                )
                
                (declaration
                    declarator: (function_declarator
                        declarator: (identifier) @function.declaration
                    )
                ) @function.declaration
            """,
            "go": """
                (function_declaration
                    name: (identifier) @function.name
                ) @function.definition
                
                (method_declaration
                    name: (field_identifier) @function.method
                ) @function.method.definition
            """,
            "rust": """
                (function_item
                    name: (identifier) @function.name
                ) @function.definition
                
                (impl_item
                    (function_item
                        name: (identifier) @function.method
                    ) @function.method.definition
                )
            """,
            "php": """
                (function_definition
                    name: (name) @function.name
                ) @function.definition
                
                (method_declaration
                    name: (name) @function.method
                ) @function.method.definition
            """,
            "ruby": """
                (method
                    name: (identifier) @function.name
                ) @function.definition
                
                (singleton_method
                    name: (identifier) @function.singleton
                ) @function.singleton.definition
            """,
            "csharp": """
                (method_declaration
                    name: (identifier) @function.name
                ) @function.definition
                
                (constructor_declaration
                    name: (identifier) @function.constructor
                ) @function.constructor.definition
            """,
            "kotlin": """
                (function_declaration
                    name: (simple_identifier) @function.name
                ) @function.definition
            """,
            "swift": """
                (function_declaration
                    name: (simple_identifier) @function.name
                ) @function.definition
                
                (init_declaration) @function.initializer
            """,
            "scala": """
                (function_definition
                    name: (identifier) @function.name
                ) @function.definition
                
                (function_declaration
                    name: (identifier) @function.declaration
                ) @function.declaration
            """,
            "dart": """
                (function_signature
                    name: (identifier) @function.name
                ) @function.definition
                
                (method_signature
                    name: (identifier) @function.method
                ) @function.method.definition
            """,
            "haskell": """
                (function
                    name: (variable) @function.name
                ) @function.definition
                
                (signature
                    name: (variable) @function.signature
                ) @function.signature
            """,
            "lua": """
                (function_declaration
                    name: (identifier) @function.name
                ) @function.definition
                
                (function_statement
                    name: (identifier) @function.name
                ) @function.definition
            """,
            "perl": """
                (subroutine_declaration
                    name: (identifier) @function.name
                ) @function.definition
            """,
            "r": """
                (binary_operator
                    lhs: (identifier) @function.name
                    operator: "<-"
                    rhs: (function_definition)
                ) @function.definition
            """,
            "julia": """
                (function_definition
                    name: (identifier) @function.name
                ) @function.definition
                
                (assignment
                    lhs: (call_expression
                        function: (identifier) @function.name
                    )
                    rhs: (function_expression)
                ) @function.definition
            """,
            "matlab": """
                (function_definition
                    name: (identifier) @function.name
                ) @function.definition
            """,
            "fortran": """
                (subroutine_subprogram
                    (subroutine_statement
                        name: (identifier) @function.name
                    )
                ) @function.definition
                
                (function_subprogram
                    (function_statement
                        name: (identifier) @function.name
                    )
                ) @function.definition
            """,
            "ada": """
                (subprogram_declaration
                    specification: (function_specification
                        name: (identifier) @function.name
                    )
                ) @function.definition
                
                (subprogram_declaration
                    specification: (procedure_specification
                        name: (identifier) @function.name
                    )
                ) @function.definition
            """,
            "pascal": """
                (function_declaration
                    name: (identifier) @function.name
                ) @function.definition
                
                (procedure_declaration
                    name: (identifier) @function.name
                ) @function.definition
            """,
            "ocaml": """
                (value_definition
                    let_binding: (let_binding
                        pattern: (value_name) @function.name
                        body: (function_expression)
                    )
                ) @function.definition
            """,
            "groovy": """
                (method_declaration
                    name: (identifier) @function.name
                ) @function.definition
            """,
            "solidity": """
                (function_definition
                    name: (identifier) @function.name
                ) @function.definition
                
                (constructor_definition) @function.constructor
            """,
            "svelte": """
                (script_element
                    (raw_text) @script.content
                )
            """,
            "vue": """
                (script_element
                    (raw_text) @script.content
                )
            """,
            "bash": """
                (function_definition
                    name: (word) @function.name
                ) @function.definition
            """,
        }

        return query_patterns.get(language, "")

    def extract_functions_with_positions(self, text: str, file_path: Optional[Path] = None) -> Dict[str, Dict]:
        """
        Extract function definitions with their positions and code blocks using Tree-sitter queries.
        This works across multiple programming languages.

        Args:
            text: Source code text
            file_path: Optional file path to detect language

        Returns:
            Dictionary mapping function identifiers to function data
        """
        try:
            # Detect language
            lang_key = self._detect_language(file_path)

            # Get language-specific function query
            query_string = self._get_function_query(lang_key)

            # Return empty if no query for this language (e.g., XML, SQL)
            if not query_string.strip():
                logger.debug(f"No function extraction query for language: {lang_key}")
                return {}

            # Get parser and language
            parser = self.parsers.get(lang_key)
            language = self.languages.get(lang_key)

            if not parser or not language:
                logger.warning(f"No parser/language available for {lang_key}")
                return {}

            # Parse the text
            tree = parser.parse(bytes(text, "utf8"))
            root_node = tree.root_node

            try:
                query = Query(language, query_string)
            except Exception as e:
                logger.warning(f"Failed to create query for {lang_key}: {e}")
                # Fallback to simple approach
                return self._extract_functions_fallback(tree, text, lang_key)

            functions = {}
            source_lines = text.split("\n")

            # Tree-sitter Python API: query.matches() returns a list of tuples
            # Each tuple is (pattern_index, captures_dict) where captures_dict maps capture names to nodes
            matches = query.matches(root_node)

            for match in matches:
                try:
                    # Each match is a tuple: (pattern_index, captures_dict)
                    if len(match) >= 2:
                        pattern_index, captures_dict = match

                        # Look for function definition captures
                        for capture_name, nodes in captures_dict.items():
                            # nodes is a list of nodes for this capture name
                            if not isinstance(nodes, list):
                                nodes = [nodes]

                            for node in nodes:
                                if (
                                    "function.definition" in capture_name
                                    or "function.method.definition" in capture_name
                                ):
                                    start_line = node.start_point[0]
                                    end_line = node.end_point[0]

                                    # Extract function name from the node
                                    func_name = self._extract_function_name_from_node(node, text.encode("utf8"))

                                    if func_name is None:
                                        # Skip if function name was filtered out (e.g., constructor)
                                        continue
                                    elif not func_name:
                                        func_name = f"function_{len(functions)}"

                                    # Extract code block
                                    code_block = self._extract_code_block_from_lines(
                                        source_lines, start_line, end_line + 1
                                    )

                                    function_id = f"{func_name}_{start_line}"
                                    functions[function_id] = {
                                        "function_name": func_name,
                                        "start_line": start_line,
                                        "end_line": end_line,
                                        "code_block": code_block,
                                        "node_type": node.type,
                                        "language": lang_key,
                                    }

                except Exception as e:
                    logger.debug(f"Error processing match: {e}")
                    continue

            # If no functions found with queries, try fallback
            if not functions:
                logger.debug(f"No functions found with queries, trying fallback for {lang_key}")
                return self._extract_functions_fallback(tree, text, lang_key)

            logger.debug(
                f"Successfully extracted {len(functions)} functions from {lang_key} file using Tree-sitter queries"
            )
            return functions

        except Exception as e:
            logger.error(f"Function extraction failed for {lang_key}: {e}")
            return {}

    def _extract_functions_fallback(self, tree, text: str, language: str) -> Dict[str, Dict]:
        """Fallback function extraction using iterative node traversal to avoid recursion limits"""
        # Skip function extraction for languages that don't have functions
        non_function_languages = {
            "xml",
            "html",
            "css",
            "json",
            "yaml",
            "toml",
            "markdown",
            "sql",
            "cmake",
            "make",
            "dockerfile",
            "gomod",
        }

        if language in non_function_languages:
            logger.debug(f"Skipping function extraction for {language} (no traditional functions)")
            return {}

        functions = {}
        source_lines = text.split("\n")

        # Common function-related node types across languages
        function_types = {
            "function_definition",
            "function_declaration",
            "method_declaration",
            "method_definition",
            "function_item",
            "constructor_declaration",
            "init_declaration",
            "singleton_method",
            "lambda",
        }

        # Use iterative approach with a stack to avoid recursion depth issues
        nodes_to_process = [tree.root_node]
        processed_count = 0
        max_nodes = 10000000  # Safety limit to prevent infinite processing

        logger.debug(f"Starting fallback function extraction for {language}")

        while nodes_to_process and processed_count < max_nodes:
            node = nodes_to_process.pop()
            processed_count += 1

            if node.type in function_types:
                try:
                    start_line = node.start_point[0]
                    end_line = node.end_point[0]

                    # Try to extract function name
                    func_name = self._extract_function_name_from_node(node, text.encode("utf8"))
                    if func_name is None:
                        # Skip if function name was filtered out (e.g., constructor)
                        continue
                    elif not func_name:
                        # Assign generic name for unnamed functions
                        func_name = f"function_{len(functions)}"

                    # Extract code block
                    code_block = self._extract_code_block_from_lines(source_lines, start_line, end_line + 1)

                    function_id = f"{func_name}_{start_line}"
                    functions[function_id] = {
                        "function_name": func_name,
                        "start_line": start_line,
                        "end_line": end_line,
                        "code_block": code_block,
                        "node_type": node.type,
                        "language": language,
                    }

                    logger.debug(f"Extracted function '{func_name}' at line {start_line} via fallback method")
                except Exception as e:
                    logger.debug(f"Error processing node of type {node.type}: {e}")
                    continue

            # Add children to the stack for processing (in reverse order to maintain depth-first traversal)
            try:
                for child in reversed(node.children):
                    nodes_to_process.append(child)
            except Exception as e:
                logger.debug(f"Error accessing children of node type {node.type}: {e}")
                continue

        if processed_count >= max_nodes:
            logger.warning(f"Reached maximum node processing limit ({max_nodes}) for {language} file")

        logger.debug(
            f"Fallback extraction completed for {language}: {len(functions)} functions found after processing {processed_count} nodes"
        )
        return functions

    def _extract_function_name_from_node(self, node, source_bytes: bytes) -> Optional[str]:
        """Extract function name from a tree-sitter node"""
        # Try to find identifier child nodes
        for child in node.children:
            if child.type in ["identifier", "simple_identifier", "name", "property_identifier", "field_identifier"]:
                try:
                    name = source_bytes[child.start_byte : child.end_byte].decode("utf8")
                    if name and name.isidentifier():
                        # Filter out constructor methods as they are typically boilerplate
                        if self._is_constructor_method(name):
                            return None
                        # Filter out annotation names (they start with @ or are common annotation names)
                        if name.startswith("@") or name in [
                            "Test",
                            "DisplayName",
                            "Override",
                            "Deprecated",
                            "SuppressWarnings",
                        ]:
                            continue
                        return name
                except:
                    continue

            # Recursively search in children (limited depth)
            if child.child_count > 0:
                name = self._extract_function_name_from_node(child, source_bytes)
                if name:
                    return name

        return None

    def _is_constructor_method(self, function_name: str) -> bool:
        """Check if a function name is a constructor method that should be filtered out"""
        # Common constructor patterns across languages
        constructor_patterns = {
            "__init__",  # Python
            "__construct",  # PHP
            "constructor",  # JavaScript/TypeScript
            "init",  # Some languages use init
            "initialize",  # Common initialization method
            "ctor",  # C# abbreviation sometimes used
        }

        # Check exact matches
        if function_name in constructor_patterns:
            return True

        # Check if it's a class name (common constructor pattern in many languages)
        # This is heuristic - if function name starts with capital letter and matches
        # common constructor naming patterns, it might be a constructor
        if function_name and function_name[0].isupper():
            # This is a simple heuristic - in many languages constructors are named
            # the same as the class, which typically start with capital letters
            # We can be more conservative here and only filter obvious ones
            pass

        return False

    def _extract_code_block_from_lines(self, source_lines: List[str], start_line: int, end_line: int) -> str:
        """Extract code block from source lines between start and end line numbers."""
        if not source_lines:
            return ""

        # Ensure line numbers are valid
        start_idx = max(0, start_line)
        end_idx = min(len(source_lines), end_line)

        if start_idx >= end_idx:
            return ""

        code_lines = source_lines[start_idx:end_idx]
        return "\n".join(code_lines)

    def _detect_language(self, file_path: Optional[Path] = None, content: Optional[str] = None) -> str:
        """Detect the programming language based on file extension or content"""
        if file_path:
            # Check for exact filename matches first (e.g., Dockerfile, Makefile)
            filename = file_path.name
            if filename in self.language_mapping:
                detected_lang = self.language_mapping[filename]
                logger.debug(f"Detected language by filename '{filename}': {detected_lang}")
                return detected_lang

            # Check file extension
            suffix = file_path.suffix.lower()
            if suffix in self.language_mapping:
                detected_lang = self.language_mapping[suffix]
                logger.debug(f"Detected language by extension '{suffix}': {detected_lang}")
                return detected_lang

            # Special cases for files without extensions
            if not suffix:
                filename_lower = filename.lower()
                special_files = {
                    "dockerfile": "dockerfile",
                    "makefile": "make",
                    "rakefile": "ruby",
                    "gemfile": "ruby",
                    "cmakelists.txt": "cmake",
                }
                if filename_lower in special_files:
                    detected_lang = special_files[filename_lower]
                    logger.debug(f"Detected language by special filename '{filename}': {detected_lang}")
                    return detected_lang

        # Content-based detection as fallback (simplified heuristics)
        if content:
            content_lower = content.lower().strip()

            # Check for shebang lines
            if content_lower.startswith("#!"):
                first_line = content.split("\n")[0].lower()
                if "python" in first_line:
                    return "python"
                elif "bash" in first_line or "sh" in first_line:
                    return "bash"
                elif "node" in first_line:
                    return "javascript"

            # Check for XML-like content
            if content_lower.startswith("<?xml") or "<" in content_lower and ">" in content_lower:
                # Could be XML, HTML, or similar
                if "<!doctype html" in content_lower or "<html" in content_lower:
                    return "html"
                else:
                    return "xml"

            # Check for JSON content
            if (content_lower.startswith("{") and content_lower.endswith("}")) or (
                content_lower.startswith("[") and content_lower.endswith("]")
            ):
                return "json"

        # Default fallback
        logger.debug(f"Could not detect language, defaulting to 'python'")
        return "python"  # Default to Python if we can't detect the language

    def get_supported_languages(self) -> List[str]:
        """Get list of all supported programming languages"""
        return list(set(self.language_mapping.values()))

    def get_supported_extensions(self) -> List[str]:
        """Get list of all supported file extensions"""
        return list(self.language_mapping.keys())

    def _extract_relative_path(self, file_path: Path, temp_base_path: Optional[Path] = None) -> str:
        """
        Extract relative path from project root for consistent caching.

        This method handles different extraction scenarios:
        1. GitHub/GitLab: /tmp/tempXXX/repo-name/src/main/java/File.java -> repo-name/src/main/java/File.java
        2. S3: /tmp/tempXXX/extracted_content/src/main/java/File.java -> extracted_content/src/main/java/File.java

        Args:
            file_path: Full path to the file
            temp_base_path: Base temporary directory path (optional)

        Returns:
            Relative path from project root as string
        """
        try:
            path_parts = file_path.parts

            # Strategy 1: Look for temp directory patterns and find project root
            temp_indicators = ["tmp", "temp", "tempfile"]
            project_root_index = None

            # Find the last temp directory in the path
            last_temp_index = None
            for i, part in enumerate(path_parts):
                if any(temp_ind in part.lower() for temp_ind in temp_indicators):
                    last_temp_index = i

            if last_temp_index is not None:
                # Look for the first meaningful directory after temp directories
                # Skip UUID-like patterns (temporary directory names)
                for i in range(last_temp_index + 1, len(path_parts)):
                    part = path_parts[i]

                    # Skip hidden directories and files
                    if part.startswith("."):
                        continue

                    # Skip UUID-like patterns (temp directory names)
                    # UUIDs are typically 32+ chars with hyphens, or long random strings
                    if len(part) >= 8 and (
                        part.count("-") >= 2  # UUID-like with hyphens
                        or (len(part) > 20 and part.replace("-", "").replace("_", "").isalnum())
                    ):  # Long temp names
                        continue

                    # This looks like a meaningful directory (project root)
                    project_root_index = i
                    break

            # Strategy 2: If no temp pattern found, look for common project indicators
            if project_root_index is None:
                project_indicators = [
                    "src",
                    "lib",
                    "app",
                    "main",
                    "java",
                    "python",
                    "js",
                    "ts",
                    "components",
                    "modules",
                    "packages",
                    "bin",
                    "build",
                    "target",
                    "node_modules",
                    ".git",
                    "assets",
                    "resources",
                    "static",
                ]

                for i, part in enumerate(path_parts):
                    if part.lower() in project_indicators and i > 0:
                        # The parent directory is likely the project root
                        project_root_index = max(0, i - 1)
                        break

            # Strategy 3: Fallback - find first non-system directory
            if project_root_index is None:
                system_dirs = ["tmp", "temp", "var", "usr", "opt", "home", "root"]
                for i, part in enumerate(path_parts):
                    if (
                        not any(sys_dir in part.lower() for sys_dir in system_dirs)
                        and not part.startswith(".")
                        and len(part) > 0
                    ):
                        project_root_index = i
                        break

            # Extract relative path from project root
            if project_root_index is not None and project_root_index < len(path_parts):
                relative_parts = path_parts[project_root_index:]
                relative_path = "/".join(relative_parts)
                logger.debug(f"Extracted relative path: {relative_path} from {file_path}")
                return relative_path

            # Final fallback: use the last few meaningful parts
            if len(path_parts) >= 2:
                # Take last 2-3 parts as a reasonable relative path
                meaningful_parts = [p for p in path_parts[-3:] if not p.startswith(".")]
                if meaningful_parts:
                    relative_path = "/".join(meaningful_parts)
                    logger.debug(f"Using fallback relative path: {relative_path} from {file_path}")
                    return relative_path

            # Ultimate fallback
            return file_path.name

        except Exception as e:
            logger.warning(f"Failed to extract relative path from {file_path}: {e}")
            return file_path.name if file_path else "unknown_file"

    def tokenize(
        self,
        text: str,
        file_path: Optional[Path] = None,
        submission_id: Optional[UUID] = None,
        project_root_path: Optional[Path] = None,
    ) -> List[Dict[str, Any]]:
        """
        Tokenizes the input text into a list of tokens using tree-sitter.

        Args:
            text: Source code text to tokenize
            file_path: Full path to the file being tokenized
            submission_id: UUID of the submission for cache key
            project_root_path: Root path of the extracted project (optional, used for relative path calculation)
        """
        try:
            # CACHE DISABLED FOR PERFORMANCE REASON -> it was ruining everything sadly
            # Generate cache key using relative path for consistency
            cache_key = None
            # if submission_id and file_path:
            #     # Extract relative path from project root
            #     if project_root_path:
            #         try:
            #             relative_path = str(file_path.relative_to(project_root_path))
            #         except ValueError:
            #             # file_path is not relative to project_root_path, use extraction method
            #             relative_path = self._extract_relative_path(file_path)
            #     else:
            #         relative_path = self._extract_relative_path(file_path)
            #
            #     cache_key = f"{submission_id}:{relative_path}"
            #
            #     # Check cache
            #     tokens = self.cache.get(cache_key)
            #     if tokens is not None:
            #         logger.debug(f"Cache hit for {cache_key}, returning cached tokens")
            #         return tokens

            # Detect language
            lang_key = self._detect_language(file_path)

            # Try to get parser by language name first, then by extension
            parser = self.parsers.get(lang_key)
            if not parser and file_path:
                # Try the detected language mapping
                detected_lang = self.language_mapping.get(lang_key)
                if detected_lang:
                    parser = self.parsers.get(detected_lang)

            if not parser:
                logger.warning(f"No parser available for {lang_key}, skipping tokenization")
                return []

            # Parse the text
            tree = parser.parse(bytes(text, "utf8"))
            root_node = tree.root_node

            # Extract tokens
            tokens = []
            self._extract_tokens(root_node, text.encode("utf8"), tokens)

            logger.debug(f"Tokenized {len(tokens)} tokens for language: {lang_key}")

            # Store in cache if we have a cache key
            # if cache_key:
            #     self.cache.set(cache_key, tokens)
            #     logger.debug(f"Stored {len(tokens)} tokens in cache for {cache_key}")

            return tokens

        except Exception as e:
            logger.error(f"Tokenization failed for {lang_key}: {e}")
            return []

    def _extract_tokens(self, node, source_code: bytes, tokens: List[Dict[str, Any]]):
        """Iteratively extract tokens from the syntax tree to avoid recursion limits"""
        # Use iterative approach with a stack to avoid recursion depth issues
        nodes_to_process = [node]
        processed_count = 0
        max_nodes = 20000  # Higher limit for token extraction as it processes more nodes

        while nodes_to_process and processed_count < max_nodes:
            current_node = nodes_to_process.pop()
            processed_count += 1

            # Add current node as token if it has meaningful content and is named
            if current_node.start_byte < current_node.end_byte and current_node.is_named:
                token_text = source_code[current_node.start_byte : current_node.end_byte].decode("utf8")

                token = {
                    "type": current_node.type,
                    "text": token_text,
                    "start": current_node.start_point[0],  # Just row number
                    "end": current_node.end_point[0],  # Just row number
                }
                tokens.append(token)

            # Add children to the stack for processing (in reverse order to maintain depth-first traversal)
            for child in reversed(current_node.children):
                nodes_to_process.append(child)

        if processed_count >= max_nodes:
            logger.warning(f"Reached maximum node processing limit ({max_nodes}) for token extraction")

    def detokenize(self, tokens: List[Dict[str, Any]]) -> str:
        """
        Detokenizes a list of tokens back into a string.
        """
        if not tokens:
            return ""

        try:
            # concatenate token texts with spaces
            return " ".join(token.get("text", "") for token in tokens if token.get("text"))

        except Exception as e:
            logger.error(f"Detokenization failed: {e}")
            return ""

    def tokenize_project(self, project_path: Path) -> None:
        """
        Tokenizes all files in the given project directory.
        """
        # Implement tokenization logic for project files
        if not project_path.is_dir():
            raise ValidationException(f"Invalid project path: {project_path}")
        logger.info(f"Tokenizing project files in: {project_path}")
        for file_path in project_path.rglob("*"):
            if file_path.is_file():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    tokens = self.tokenize(content, file_path)
                    logger.debug(f"Tokenized {file_path}: {len(tokens)} tokens")
                    print(f"Tokenized {file_path}: {len(tokens)} tokens")
                    print(tokens)
                    print("\n\n\n\n")

                    # Optionally save tokens or process further
                except Exception as e:
                    logger.error(f"Failed to tokenize {file_path}: {str(e)}")
            else:
                logger.warning(f"Skipping non-file path: {file_path}")

    def tokenize_submission_files(
        self, submission_id: UUID, project_root_path: Path, file_paths: List[Path]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Tokenize multiple files from a submission with consistent caching.

        Args:
            submission_id: UUID of the submission
            project_root_path: Root path of the extracted/cloned project
            file_paths: List of file paths to tokenize

        Returns:
            Dictionary mapping relative file paths to their tokens
        """
        results = {}

        for file_path in file_paths:
            try:
                # Read file content
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # Tokenize with proper cache key using relative path
                tokens = self.tokenize(
                    text=content, file_path=file_path, submission_id=submission_id, project_root_path=project_root_path
                )

                # Use relative path as key in results
                try:
                    relative_path = str(file_path.relative_to(project_root_path))
                except ValueError:
                    relative_path = self._extract_relative_path(file_path)

                results[relative_path] = tokens

            except Exception as e:
                logger.error(f"Failed to tokenize file {file_path}: {e}")
                continue

        logger.info(f"Tokenized {len(results)} files for submission {submission_id}")
        return results
