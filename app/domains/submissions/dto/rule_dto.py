from typing import Dict, Any
from pydantic import BaseModel, ConfigDict


class RuleDto(BaseModel):
    """DTO for representing rule data in API requests"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "file_presence",
                "params": {
                    "must_exist": ["README*", "*.md"],
                    "forbidden": ["*.tmp", "*.log", "*.class"]
                }
            }
        }
    )
    
    name: str
    params: Dict[str, Any] 