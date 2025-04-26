import os
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger("vulnerability-scanner.config")

DEFAULT_CONFIG = {
    "models": {
        "default": "gpt-4",
        "alternatives": ["gpt-3.5-turbo", "gpt-4-turbo"]
    },
    "scan_settings": {
        "max_file_size_kb": 500,
        "max_files_per_scan": 100,
        "supported_languages": [
            {"name": "python", "extensions": [".py"], "enabled": True},
            {"name": "javascript", "extensions": [".js", ".jsx", ".ts", ".tsx"], "enabled": True},
            {"name": "php", "extensions": [".php"], "enabled": True},
            {"name": "java", "extensions": [".java"], "enabled": True},
            {"name": "csharp", "extensions": [".cs"], "enabled": True},
            {"name": "go", "extensions": [".go"], "enabled": True},
            {"name": "ruby", "extensions": [".rb"], "enabled": True},
            {"name": "c_cpp", "extensions": [".c", ".cpp", ".h"], "enabled": True}  # ✅ Added C/C++ support
        ],
        "excluded_directories": ["node_modules", "venv", "__pycache__", ".git"],
        "excluded_files": [".env", "package-lock.json", "yarn.lock"]
    },
    "vulnerability_database": {
        "use_local_db": True,
        "local_db_path": "vulnerabilities.json",
        "use_external_apis": False,
        "external_apis": []
    },
    "reporting": {
        "output_formats": ["json", "html", "markdown"],
        "default_format": "json",
        "include_code_snippets": True,
        "max_snippet_lines": 10
    },
    "advanced": {
        "llm_temperature": 0.1,
        "llm_max_tokens": 1500,
        "use_pattern_matching": True,
        "confidence_threshold": 0.7
    }
}

class ConfigManager:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.join(os.path.expanduser("~"), ".vulnscan", "config.json")
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_path}")
                return config
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load config: {str(e)}. Using default configuration.")
            return self._create_default_config()

    def _create_default_config(self) -> Dict[str, Any]:
        config_dir = os.path.dirname(self.config_path)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        with open(self.config_path, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        logger.info(f"Created default configuration at {self.config_path}")
        return DEFAULT_CONFIG

    def save_config(self) -> None:
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
        logger.info(f"Saved configuration to {self.config_path}")

    def get(self, key_path: str, default=None) -> Any:
        keys = key_path.split('.')
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set(self, key_path: str, value: Any) -> None:
        keys = key_path.split('.')
        config_section = self.config
        for key in keys[:-1]:
            if key not in config_section:
                config_section[key] = {}
            config_section = config_section[key]
        config_section[keys[-1]] = value

    def get_supported_extensions(self) -> List[str]:
        extensions = []
        languages = self.get("scan_settings.supported_languages", [])
        for lang in languages:
            if lang.get("enabled", False):
                extensions.extend(lang.get("extensions", []))
        return extensions

    def is_excluded_path(self, path: str) -> bool:
        path_obj = Path(path)
        excluded_dirs = self.get("scan_settings.excluded_directories", [])
        for part in path_obj.parts:
            if part in excluded_dirs:
                return True
        if path_obj.name in self.get("scan_settings.excluded_files", []):
            return True
        return False

    def is_file_too_large(self, file_path: str) -> bool:
        max_size_kb = self.get("scan_settings.max_file_size_kb", 500)
        file_size_kb = os.path.getsize(file_path) / 1024
        return file_size_kb > max_size_kb
