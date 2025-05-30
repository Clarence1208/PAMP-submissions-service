from abc import abstractmethod, ABC
from pathlib import Path


class Rule(ABC):
    """
    Abstract base class for submission rules.
    Each sub class must implement an unique name and the validate method.
    """
    name: str

    def __init__(self, params: dict):
        self.params = params

    @abstractmethod
    def validate(self, submission_path: Path) -> (bool, str):
        """
        Must return a tuple (isValidate, message):
         - ok = True if the rule is validated else False
         - message = a string with the error message if not validated, or an empty string if ok
        """
        pass