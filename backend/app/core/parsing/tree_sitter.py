"""
CodeGraph Backend - Tree-sitter AST Parser
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Any
import logging

try:
    import tree_sitter
    import tree_sitter_python
    import tree_sitter_javascript
    import tree_sitter_typescript
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False

from app.core.parsing.languages import (
    LanguageConfig,
    get_language_config,
    is_supported_file,
    should_ignore,
    PYTHON_CONFIG,
    JAVASCRIPT_CONFIG,
    TYPESCRIPT_CONFIG,
)

logger = logging.getLogger(__name__)


@dataclass
class ParsedNode:
    """A parsed code node from the AST."""
    node_type: str  # function, class, method, import, variable
    name: str
    qualified_name: str
    file_path: str
    start_line: int
    end_line: int
    start_column: int
    end_column: int
    signature: str | None = None
    docstring: str | None = None
    source_code: str | None = None
    parent_name: str | None = None
    children: list[str] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []


class TreeSitterParser:
    """Multi-language parser using Tree-sitter."""
    
    def __init__(self):
        self._parsers: dict[str, Any] = {}
        self._languages: dict[str, Any] = {}
        self._init_languages()
    
    def _init_languages(self):
        """Initialize Tree-sitter languages."""
        if not TREE_SITTER_AVAILABLE:
            logger.warning("Tree-sitter not available, using fallback parser")
            return
        
        try:
            # Initialize Python
            self._languages["python"] = tree_sitter.Language(
                tree_sitter_python.language()
            )
            
            # Initialize JavaScript  
            self._languages["javascript"] = tree_sitter.Language(
                tree_sitter_javascript.language()
            )
            
            # Initialize TypeScript
            self._languages["typescript"] = tree_sitter.Language(
                tree_sitter_typescript.language_typescript()
            )
            
            # Create parsers for each language
            for lang_name, language in self._languages.items():
                parser = tree_sitter.Parser(language)
                self._parsers[lang_name] = parser
                
        except Exception as e:
            logger.error(f"Failed to initialize Tree-sitter: {e}")
    
    def parse_file(self, file_path: Path, content: str | None = None) -> list[ParsedNode]:
        """Parse a single file and extract code nodes."""
        if content is None:
            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception as e:
                logger.error(f"Failed to read {file_path}: {e}")
                return []
        
        config = get_language_config(file_path)
        if not config:
            return []
        
        if not TREE_SITTER_AVAILABLE:
            return self._fallback_parse(file_path, content, config)
        
        parser = self._parsers.get(config.tree_sitter_name)
        if not parser:
            return self._fallback_parse(file_path, content, config)
        
        try:
            tree = parser.parse(content.encode("utf-8"))
            return self._extract_nodes(tree.root_node, file_path, content, config)
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return []
    
    def _extract_nodes(
        self,
        root_node: Any,
        file_path: Path,
        content: str,
        config: LanguageConfig,
        parent_name: str | None = None,
    ) -> list[ParsedNode]:
        """Extract relevant nodes from AST."""
        nodes = []
        lines = content.split("\n")
        
        def visit(node: Any, current_parent: str | None = None):
            node_type = node.type
            
            # Check if this is a relevant node type
            parsed_type = None
            if node_type in config.function_types:
                parsed_type = "function"
            elif node_type in config.class_types:
                parsed_type = "class"
            elif node_type in config.import_types:
                parsed_type = "import"
            
            if parsed_type:
                # Extract name
                name = self._get_node_name(node, config)
                if name:
                    qualified_name = f"{current_parent}.{name}" if current_parent else name
                    
                    # Get source code
                    start_line = node.start_point[0]
                    end_line = node.end_point[0]
                    source = "\n".join(lines[start_line:end_line + 1])
                    
                    # Get signature and docstring
                    signature = self._get_signature(node, parsed_type, source)
                    docstring = self._get_docstring(node, config)
                    
                    parsed_node = ParsedNode(
                        node_type=parsed_type,
                        name=name,
                        qualified_name=qualified_name,
                        file_path=str(file_path),
                        start_line=start_line + 1,  # 1-indexed
                        end_line=end_line + 1,
                        start_column=node.start_point[1],
                        end_column=node.end_point[1],
                        signature=signature,
                        docstring=docstring,
                        source_code=source,
                        parent_name=current_parent,
                    )
                    nodes.append(parsed_node)
                    
                    # Use this as parent for nested definitions
                    if parsed_type == "class":
                        current_parent = qualified_name
            
            # Visit children
            for child in node.children:
                visit(child, current_parent)
        
        visit(root_node)
        return nodes
    
    def _get_node_name(self, node: Any, config: LanguageConfig) -> str | None:
        """Extract name from a node."""
        for child in node.children:
            if child.type in ["identifier", "property_identifier", "name"]:
                return child.text.decode("utf-8") if isinstance(child.text, bytes) else child.text
        return None
    
    def _get_signature(self, node: Any, node_type: str, source: str) -> str:
        """Extract function/class signature."""
        # Get first line as signature
        first_line = source.split("\n")[0].strip()
        return first_line
    
    def _get_docstring(self, node: Any, config: LanguageConfig) -> str | None:
        """Extract docstring if present."""
        # Look for string literal as first statement in body
        for child in node.children:
            if child.type in ["block", "body", "statement_block"]:
                for stmt in child.children:
                    if stmt.type in ["expression_statement", "string"]:
                        for sub in stmt.children if hasattr(stmt, 'children') else [stmt]:
                            if sub.type == "string":
                                text = sub.text.decode("utf-8") if isinstance(sub.text, bytes) else sub.text
                                # Clean up quotes
                                return text.strip('"""\'\'\'').strip()
                break
        return None
    
    def _fallback_parse(
        self,
        file_path: Path,
        content: str,
        config: LanguageConfig
    ) -> list[ParsedNode]:
        """Simple regex-based fallback parser for when Tree-sitter isn't available."""
        import re
        nodes = []
        lines = content.split("\n")
        
        # Simple patterns for Python
        if config.name == "python":
            patterns = {
                "function": r"^\s*(async\s+)?def\s+(\w+)\s*\(",
                "class": r"^\s*class\s+(\w+)",
                "import": r"^(?:from\s+\S+\s+)?import\s+",
            }
            
            for i, line in enumerate(lines):
                for node_type, pattern in patterns.items():
                    match = re.match(pattern, line)
                    if match:
                        if node_type == "function":
                            name = match.group(2)
                        elif node_type == "class":
                            name = match.group(1)
                        else:
                            name = line.strip()
                        
                        nodes.append(ParsedNode(
                            node_type=node_type,
                            name=name,
                            qualified_name=name,
                            file_path=str(file_path),
                            start_line=i + 1,
                            end_line=i + 1,
                            start_column=0,
                            end_column=len(line),
                            signature=line.strip(),
                        ))
        
        return nodes
    
    def parse_directory(
        self,
        directory: Path,
        recursive: bool = True
    ) -> Generator[ParsedNode, None, None]:
        """Parse all supported files in a directory."""
        if not directory.is_dir():
            return
        
        for item in directory.iterdir():
            if should_ignore(item):
                continue
            
            if item.is_file() and is_supported_file(item):
                for node in self.parse_file(item):
                    yield node
            elif item.is_dir() and recursive:
                yield from self.parse_directory(item, recursive=True)


# Singleton parser instance
_parser: TreeSitterParser | None = None


def get_parser() -> TreeSitterParser:
    """Get the global parser instance."""
    global _parser
    if _parser is None:
        _parser = TreeSitterParser()
    return _parser
