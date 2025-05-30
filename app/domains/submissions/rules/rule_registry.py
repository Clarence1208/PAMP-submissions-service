from typing import Dict, Type, List
from app.domains.submissions.rules.models.rule import Rule
from app.domains.submissions.rules.models.file_presence_rule import FilePresenceRule
from app.domains.submissions.rules.models.max_archive_size_rule import MaxArchiveSizeRule
from app.domains.submissions.rules.models.directory_structure_rule import DirectoryStructureRule
from app.domains.submissions.rules.models.file_content_rule import FileContentRule


class RuleRegistry:
    """Registry for managing and instantiating rules"""
    
    def __init__(self):
        self._rules: Dict[str, Type[Rule]] = {}
        self._register_default_rules()
    
    def _register_default_rules(self):
        """Register all available rule classes"""
        self.register_rule(FilePresenceRule)
        self.register_rule(MaxArchiveSizeRule)
        self.register_rule(DirectoryStructureRule)
        self.register_rule(FileContentRule)
    
    def register_rule(self, rule_class: Type[Rule]):
        """Register a rule class with its name"""
        self._rules[rule_class.name] = rule_class
    
    def get_rule_names(self) -> List[str]:
        """Get list of all available rule names"""
        return list(self._rules.keys())
    
    def rule_exists(self, rule_name: str) -> bool:
        """Check if a rule with the given name exists"""
        return rule_name in self._rules
    
    def create_rule(self, rule_name: str, params: dict) -> Rule:
        """Create a rule instance by name with parameters"""
        if not self.rule_exists(rule_name):
            raise ValueError(f"Rule '{rule_name}' not found. Available rules: {self.get_rule_names()}")
        
        rule_class = self._rules[rule_name]
        return rule_class(params)
    
    def validate_rules(self, rule_data_list: List[dict]) -> List[str]:
        """Validate a list of rule data and return any missing rule names"""
        missing_rules = []
        for rule_data in rule_data_list:
            rule_name = rule_data.get("name")
            if not rule_name:
                missing_rules.append("(unnamed rule)")
            elif not self.rule_exists(rule_name):
                missing_rules.append(rule_name)
        return missing_rules


# Global rule registry instance
rule_registry = RuleRegistry() 