"""
CodeGraph Backend - Language Configuration for Tree-sitter
"""
from dataclasses import dataclass, field
from typing import Callable
from pathlib import Path


@dataclass
class LanguageConfig:
    """Configuration for a programming language."""
    name: str
    extensions: list[str]
    tree_sitter_name: str
    
    # Node type mappings for this language
    function_types: list[str] = field(default_factory=list)
    class_types: list[str] = field(default_factory=list)
    import_types: list[str] = field(default_factory=list)
    variable_types: list[str] = field(default_factory=list)
    
    # Field names for extracting information
    name_field: str = "name"
    body_field: str = "body"
    parameters_field: str = "parameters"


# Language configurations
PYTHON_CONFIG = LanguageConfig(
    name="python",
    extensions=[".py", ".pyi"],
    tree_sitter_name="python",
    function_types=["function_definition", "async_function_definition"],
    class_types=["class_definition"],
    import_types=["import_statement", "import_from_statement"],
    variable_types=["assignment", "annotated_assignment"],
    name_field="name",
    body_field="body",
    parameters_field="parameters",
)

JAVASCRIPT_CONFIG = LanguageConfig(
    name="javascript",
    extensions=[".js", ".jsx", ".mjs", ".cjs"],
    tree_sitter_name="javascript",
    function_types=[
        "function_declaration",
        "arrow_function",
        "function_expression",
        "generator_function_declaration",
    ],
    class_types=["class_declaration", "class_expression"],
    import_types=["import_statement"],
    variable_types=["variable_declaration", "lexical_declaration"],
    name_field="name",
    body_field="body",
    parameters_field="parameters",
)

TYPESCRIPT_CONFIG = LanguageConfig(
    name="typescript",
    extensions=[".ts", ".tsx"],
    tree_sitter_name="typescript",
    function_types=[
        "function_declaration",
        "arrow_function",
        "function_expression",
        "generator_function_declaration",
        "method_definition",
    ],
    class_types=["class_declaration", "abstract_class_declaration"],
    import_types=["import_statement"],
    variable_types=["variable_declaration", "lexical_declaration"],
    name_field="name",
    body_field="body",
    parameters_field="parameters",
)


# Mapping of extensions to configs
LANGUAGE_CONFIGS: dict[str, LanguageConfig] = {}

for config in [PYTHON_CONFIG, JAVASCRIPT_CONFIG, TYPESCRIPT_CONFIG]:
    for ext in config.extensions:
        LANGUAGE_CONFIGS[ext] = config


def get_language_config(file_path: str | Path) -> LanguageConfig | None:
    """Get language configuration for a file."""
    path = Path(file_path)
    ext = path.suffix.lower()
    return LANGUAGE_CONFIGS.get(ext)


def is_supported_file(file_path: str | Path) -> bool:
    """Check if a file type is supported."""
    return get_language_config(file_path) is not None


# Files and directories to ignore during parsing
IGNORE_PATTERNS = [
    "__pycache__",
    "node_modules",
    ".git",
    ".venv",
    "venv",
    "env",
    ".env",
    "dist",
    "build",
    ".next",
    "coverage",
    ".pytest_cache",
    ".mypy_cache",
    "*.min.js",
    "*.bundle.js",
]


def should_ignore(path: Path) -> bool:
    """Check if a path should be ignored."""
    name = path.name
    for pattern in IGNORE_PATTERNS:
        if pattern.startswith("*"):
            if name.endswith(pattern[1:]):
                return True
        elif name == pattern:
            return True
    return False
