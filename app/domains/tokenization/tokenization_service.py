import logging
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from uuid import uuid4, UUID

from tree_sitter import Parser, Language, Query
from tree_sitter_language_pack import get_language, get_parser

from app.domains.detection.similarity_detection_service import SimilarityDetectionService
from app.domains.repositories.submission_fetcher import SubmissionFetcher
from app.domains.submissions.dto.create_submission_dto import CreateSubmissionDto
from app.domains.tokenization.custom_cache import CustomCache
from app.shared.exceptions import ValidationException
from app.domains.repositories.exceptions import (
    RepositoryFetchException, UnsupportedRepositoryException,
    SubmissionValidationException, TemporaryDirectoryException
)

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
            hot_max_memory_mb=300,
            cold_db_path="/tmp/tokenization_cache",
            hot_threshold_percent=80.0,
            batch_size=50
        )
        self._setup_language_mapping()
        self._setup_parsers()

    def _setup_language_mapping(self):
        """Set up file extension to language mapping"""
        self.language_mapping = {
            # Ada
            '.ada': 'ada',
            '.ads': 'ada',
            '.adb': 'ada',

            # Assembly
            '.asm': 'asm',
            '.s': 'asm',
            '.S': 'asm',

            # Bash/Shell
            '.sh': 'bash',
            '.bash': 'bash',
            '.zsh': 'bash',
            '.fish': 'bash',

            # C
            '.c': 'c',
            '.h': 'c',

            # C#
            '.cs': 'csharp',
            '.csx': 'csharp',

            # C++
            '.cpp': 'cpp',
            '.cxx': 'cpp',
            '.cc': 'cpp',
            '.c++': 'cpp',
            '.hpp': 'cpp',
            '.hxx': 'cpp',
            '.hh': 'cpp',
            '.h++': 'cpp',

            # CMake
            '.cmake': 'cmake',
            'CMakeLists.txt': 'cmake',

            # CSS
            '.css': 'css',
            '.scss': 'css',
            '.sass': 'css',
            '.less': 'css',

            # Dart
            '.dart': 'dart',

            # Dockerfile
            'Dockerfile': 'dockerfile',
            '.dockerfile': 'dockerfile',

            # Fortran
            '.f': 'fortran',
            '.f90': 'fortran',
            '.f95': 'fortran',
            '.f03': 'fortran',
            '.f08': 'fortran',
            '.for': 'fortran',
            '.ftn': 'fortran',
            '.fpp': 'fortran',

            # Go
            '.go': 'go',
            '.mod': 'gomod',
            '.sum': 'gomod',

            # GraphQL
            '.graphql': 'graphql',
            '.gql': 'graphql',

            # Groovy
            '.groovy': 'groovy',
            '.gradle': 'groovy',

            # Haskell
            '.hs': 'haskell',
            '.lhs': 'haskell',

            # HTML
            '.html': 'html',
            '.htm': 'html',
            '.xhtml': 'html',

            # Java
            '.java': 'java',
            '.jsp': 'java',

            # JavaScript
            '.js': 'javascript',
            '.mjs': 'javascript',
            '.jsx': 'javascript',

            # JSON
            '.json': 'json',
            '.jsonc': 'json',
            '.json5': 'json',

            # Julia
            '.jl': 'julia',

            # Kotlin
            '.kt': 'kotlin',
            '.kts': 'kotlin',

            # Lua
            '.lua': 'lua',

            # Make
            'Makefile': 'make',
            'makefile': 'make',
            '.mk': 'make',
            '.make': 'make',

            # Markdown
            '.md': 'markdown',
            '.markdown': 'markdown',
            '.mdown': 'markdown',
            '.mkd': 'markdown',
            '.mdx': 'markdown',

            # MATLAB
            '.m': 'matlab',
            '.mlx': 'matlab',

            # OCaml
            '.ml': 'ocaml',
            '.mli': 'ocaml',

            # Pascal/Delphi/Object Pascal
            '.pas': 'pascal',
            '.pp': 'pascal',
            '.inc': 'pascal',
            '.dpr': 'pascal',
            '.dpk': 'pascal',
            '.dfm': 'pascal',
            '.fmx': 'pascal',

            # Perl
            '.pl': 'perl',
            '.pm': 'perl',
            '.perl': 'perl',

            # PHP
            '.php': 'php',
            '.php3': 'php',
            '.php4': 'php',
            '.php5': 'php',
            '.phtml': 'php',

            # Python
            '.py': 'python',
            '.pyi': 'python',
            '.pyw': 'python',
            '.pyx': 'python',
            '.pxd': 'python',
            '.pxi': 'python',

            # R
            '.r': 'r',
            '.R': 'r',
            '.rmd': 'r',
            '.Rmd': 'r',

            # Ruby
            '.rb': 'ruby',
            '.rbw': 'ruby',
            '.rake': 'ruby',
            '.gemspec': 'ruby',
            'Rakefile': 'ruby',
            'Gemfile': 'ruby',

            # Rust
            '.rs': 'rust',

            # Scala
            '.scala': 'scala',
            '.sc': 'scala',

            # Solidity
            '.sol': 'solidity',

            # SQL
            '.sql': 'sql',
            '.mysql': 'sql',
            '.pgsql': 'sql',
            '.plsql': 'sql',

            # Svelte
            '.svelte': 'svelte',

            # Swift
            '.swift': 'swift',

            # TOML
            '.toml': 'toml',

            # TypeScript
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.mts': 'typescript',
            '.cts': 'typescript',

            # Vue.js
            '.vue': 'vue',

            # XML
            '.xml': 'xml',
            '.xsl': 'xml',
            '.xslt': 'xml',
            '.xsd': 'xml',
            '.wsdl': 'xml',
            '.svg': 'xml',

            # YAML
            '.yaml': 'yaml',
            '.yml': 'yaml',
        }

    def extract_supported_files_from_directory(self, directory: Path) -> List[Path]:
        """
        Extracts all files from the given directory that are supported by the tokenization service.
        Returns a list of file paths.
        """
        if not directory.is_dir():
            raise ValidationException(f"Invalid directory path: {directory}")

        supported_files = []
        for file_path in directory.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in self.language_mapping:
                supported_files.append(file_path)

        logger.info(f"Extracted {len(supported_files)} supported files from {directory}")
        return supported_files

    def _setup_parsers(self):
        """Set up tree-sitter parsers for different languages"""
        # List of languages supported by tree-sitter-language-pack
        # Based on https://pypi.org/project/tree-sitter-language-pack/
        supported_languages = [
            'ada', 'asm', 'bash', 'c', 'csharp', 'cpp', 'cmake', 'css', 'dart',
            'dockerfile', 'fortran', 'go', 'gomod', 'graphql', 'groovy', 'haskell',
            'html', 'java', 'javascript', 'json', 'julia', 'kotlin', 'lua', 'make',
            'markdown', 'matlab', 'ocaml', 'pascal', 'perl', 'php', 'python', 'r',
            'ruby', 'rust', 'scala', 'solidity', 'sql', 'svelte', 'swift', 'toml',
            'typescript', 'vue', 'xml', 'yaml'
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

        logger.info(f"Tree-sitter parsers initialized: {initialized_count} successful")
        if failed_languages:
            logger.warning(f"Failed to initialize parsers for: {', '.join(failed_languages)}")

    def _get_function_query(self, language: str) -> str:
        """Get language-specific query for extracting functions"""
        
        # Universal query patterns that work across most languages
        # Using common node type patterns found in tree-sitter grammars
        query_patterns = {
            'python': """
                (function_definition
                    name: (identifier) @function.name
                ) @function.definition
                
                (class_definition
                    name: (identifier) @class.name
                    body: (block
                        (function_definition
                            name: (identifier) @function.method
                        ) @function.method.definition
                    )
                )
            """,
            
            'javascript': """
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
            
            'java': """
                (method_declaration
                    name: (identifier) @function.name
                ) @function.definition
                
                (constructor_declaration
                    name: (identifier) @function.constructor
                ) @function.definition
            """,
            
            'c': """
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
            
            'cpp': """
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
            
            'go': """
                (function_declaration
                    name: (identifier) @function.name
                ) @function.definition
                
                (method_declaration
                    name: (field_identifier) @function.method
                ) @function.method.definition
            """,
            
            'rust': """
                (function_item
                    name: (identifier) @function.name
                ) @function.definition
                
                (impl_item
                    (function_item
                        name: (identifier) @function.method
                    ) @function.method.definition
                )
            """,
            
            'php': """
                (function_definition
                    name: (name) @function.name
                ) @function.definition
                
                (method_declaration
                    name: (name) @function.method
                ) @function.method.definition
            """,
            
            'ruby': """
                (method
                    name: (identifier) @function.name
                ) @function.definition
                
                (singleton_method
                    name: (identifier) @function.singleton
                ) @function.singleton.definition
            """,
            
            'csharp': """
                (method_declaration
                    name: (identifier) @function.name
                ) @function.definition
                
                (constructor_declaration
                    name: (identifier) @function.constructor
                ) @function.constructor.definition
            """,
            
            'kotlin': """
                (function_declaration
                    (simple_identifier) @function.name
                ) @function.definition
            """,
            
            'swift': """
                (function_declaration
                    name: (simple_identifier) @function.name
                ) @function.definition
                
                (init_declaration) @function.initializer
            """,
            
            'scala': """
                (function_definition
                    name: (identifier) @function.name
                ) @function.definition
                
                (function_declaration
                    name: (identifier) @function.declaration
                ) @function.declaration
            """
        }
        
        # Default query that attempts to work with most languages
        default_query = """
            (function_definition
                name: (_) @function.name
            ) @function.definition
            
            (method_declaration
                name: (_) @function.method
            ) @function.method.definition
            
            (function_declaration
                name: (_) @function.name
            ) @function.definition
        """
        
        return query_patterns.get(language, default_query)

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
            
            # Get parser and language
            parser = self.parsers.get(lang_key)
            language = self.languages.get(lang_key)
            
            if not parser or not language:
                logger.warning(f"No parser/language available for {lang_key}")
                return {}
            
            # Parse the text
            tree = parser.parse(bytes(text, "utf8"))
            root_node = tree.root_node
            
            # Get language-specific function query
            query_string = self._get_function_query(lang_key)
            
            try:
                query = Query(language, query_string)
            except Exception as e:
                logger.warning(f"Failed to create query for {lang_key}: {e}")
                # Fallback to simple approach
                return self._extract_functions_fallback(tree, text, lang_key)
            
            functions = {}
            source_lines = text.split('\n')
            
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
                                if 'function.definition' in capture_name or 'function.method.definition' in capture_name:
                                    start_line = node.start_point[0]
                                    end_line = node.end_point[0]
                                    
                                    # Extract function name from the node
                                    func_name = self._extract_function_name_from_node(node, text.encode('utf8'))
                                    
                                    if func_name is None:
                                        # Skip if function name was filtered out (e.g., constructor)
                                        continue
                                    elif not func_name:
                                        func_name = f"function_{len(functions)}"
                                    
                                    # Extract code block
                                    code_block = self._extract_code_block_from_lines(source_lines, start_line, end_line + 1)
                                    
                                    function_id = f"{func_name}_{start_line}"
                                    functions[function_id] = {
                                        'function_name': func_name,
                                        'start_line': start_line,
                                        'end_line': end_line,
                                        'code_block': code_block,
                                        'node_type': node.type,
                                        'language': lang_key
                                    }
                                    
                except Exception as e:
                    logger.debug(f"Error processing match: {e}")
                    continue
            
            # If no functions found with queries, try fallback
            if not functions:
                logger.debug(f"No functions found with queries, trying fallback for {lang_key}")
                return self._extract_functions_fallback(tree, text, lang_key)
            
            logger.info(f"Extracted {len(functions)} functions from {lang_key} file")
            return functions
            
        except Exception as e:
            logger.error(f"Function extraction failed for {lang_key}: {e}")
            return {}

    def _extract_functions_fallback(self, tree, text: str, language: str) -> Dict[str, Dict]:
        """Fallback function extraction using iterative node traversal to avoid recursion limits"""
        functions = {}
        source_lines = text.split('\n')
        
        # Common function-related node types across languages
        function_types = {
            'function_definition', 'function_declaration', 'method_declaration',
            'method_definition', 'function_item', 'constructor_declaration',
            'init_declaration', 'singleton_method', 'lambda'
        }
        
        # Use iterative approach with a stack to avoid recursion depth issues
        nodes_to_process = [tree.root_node]
        processed_count = 0
        max_nodes = 10000000  # Safety limit to prevent infinite processing
        
        while nodes_to_process and processed_count < max_nodes:
            node = nodes_to_process.pop()
            processed_count += 1
            
            if node.type in function_types:
                start_line = node.start_point[0]
                end_line = node.end_point[0]
                
                # Try to extract function name
                func_name = self._extract_function_name_from_node(node, text.encode('utf8'))
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
                    'function_name': func_name,
                    'start_line': start_line,
                    'end_line': end_line,
                    'code_block': code_block,
                    'node_type': node.type,
                    'language': language
                }
            
            # Add children to the stack for processing (in reverse order to maintain depth-first traversal)
            for child in reversed(node.children):
                nodes_to_process.append(child)
        
        if processed_count >= max_nodes:
            logger.warning(f"Reached maximum node processing limit ({max_nodes}) for {language} file")
        
        return functions

    def _extract_function_name_from_node(self, node, source_bytes: bytes) -> Optional[str]:
        """Extract function name from a tree-sitter node"""
        # Try to find identifier child nodes
        for child in node.children:
            if child.type in ['identifier', 'simple_identifier', 'name', 'property_identifier', 'field_identifier']:
                try:
                    name = source_bytes[child.start_byte:child.end_byte].decode('utf8')
                    if name and name.isidentifier():
                        # Filter out constructor methods as they are typically boilerplate
                        if self._is_constructor_method(name):
                            return None
                        # Filter out annotation names (they start with @ or are common annotation names)
                        if name.startswith('@') or name in ['Test', 'DisplayName', 'Override', 'Deprecated', 'SuppressWarnings']:
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
            '__init__',      # Python
            '__construct',   # PHP  
            'constructor',   # JavaScript/TypeScript
            'init',          # Some languages use init
            'initialize',    # Common initialization method
            'ctor',          # C# abbreviation sometimes used
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
        return '\n'.join(code_lines)

    def _detect_language(self, file_path: Optional[Path] = None, content: Optional[str] = None) -> str:
        """Detect the programming language based on file extension or content"""
        if file_path:
            # Check for exact filename matches first (e.g., Dockerfile, Makefile)
            filename = file_path.name
            if filename in self.language_mapping:
                return self.language_mapping[filename]

            # Check file extension
            suffix = file_path.suffix.lower()
            if suffix in self.language_mapping:
                return self.language_mapping[suffix]

            # Special cases for files without extensions
            if not suffix:
                if filename.lower() in ['dockerfile', 'makefile', 'rakefile', 'gemfile']:
                    return self.language_mapping.get(filename, 'text')

        # Default fallback
        return 'python'  # Default to Python if we can't detect the language

    def get_supported_languages(self) -> List[str]:
        """Get list of all supported programming languages"""
        return list(set(self.language_mapping.values()))

    def get_supported_extensions(self) -> List[str]:
        """Get list of all supported file extensions"""
        return list(self.language_mapping.keys())

    def tokenize(self, text: str, file_path: Optional[Path] = None, submission_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """
        Tokenizes the input text into a list of tokens using tree-sitter.
        """
        try:
            if submission_id and file_path:
                tokens = self.cache.get(submission_id + file_path)

                if tokens is not None:
                    logger.debug(f"Cache hit for {submission_id} + {file_path}, returning cached tokens")
                    return tokens

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
            self._extract_tokens(root_node, text.encode('utf8'), tokens)

            logger.debug(f"Tokenized {len(tokens)} tokens for language: {lang_key}")

            if submission_id and file_path:
                # Store tokens in cache
                self.cache.set(submission_id + file_path, tokens)
                logger.debug(f"Stored {len(tokens)} tokens in cache for {submission_id} + {file_path}")


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
                token_text = source_code[current_node.start_byte:current_node.end_byte].decode('utf8')

                token = {
                    'type': current_node.type,
                    'text': token_text,
                    'start': current_node.start_point[0],  # Just row number
                    'end': current_node.end_point[0]  # Just row number
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
            return ' '.join(token.get('text', '') for token in tokens if token.get('text'))

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
                    with open(file_path, 'r', encoding='utf-8') as f:
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
