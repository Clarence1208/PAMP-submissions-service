# PAMP Submissions Service

A high-performance Python microservice for detecting cheating in project submissions using FastAPI, SQLModel, and PostgreSQL.

## Rule System

The PAMP Submissions Service includes a comprehensive rule validation system that can automatically clone GitHub repositories and validate them against customizable rules.

### Available Rules

#### 1. File Presence Rule (`file_presence`)
Validates the presence of required files and absence of forbidden files using glob patterns.

<details>
<summary><strong>📖 File Presence Rule Examples</strong></summary>

**Basic Usage:**
```json
{
  "name": "file_presence",
  "params": {
    "must_exist": ["README*", "*.md"],
    "forbidden": ["*.tmp", "*.log", "*.class"]
  }
}
```

**Advanced Patterns:**
```json
{
  "name": "file_presence",
  "params": {
    "must_exist": [
      "README*",
      "package.json",
      "src/**/*.py",
      "docs/*.md"
    ],
    "forbidden": [
      "*.tmp",
      "*.log", 
      "*.class",
      "*.exe",
      "node_modules/*",
      "__pycache__/*",
      "*.pyc"
    ]
  }
}
```

**Error Response Example:**
```json
{
  "detail": {
    "validation_failed": true,
    "errors": [
      {
        "code": "missingRequiredFiles",
        "missing_files": ["README.md", "package.json"],
        "patterns": ["README*", "package.json"],
        "message": "Missing required files: README.md, package.json"
      },
      {
        "code": "forbiddenFilesFound",
        "forbidden_files": ["temp.log"],
        "patterns": ["*.log"],
        "message": "Forbidden files found: temp.log"
      }
    ]
  }
}
```

</details>

#### 2. Maximum Archive Size Rule (`max_archive_size`)
Validates that the repository size doesn't exceed a specified limit.

<details>
<summary><strong>📊 Archive Size Rule Examples</strong></summary>

**Basic Usage:**
```json
{
  "name": "max_archive_size",
  "params": {
    "max_size_mb": 100
  }
}
```

**Different Size Limits:**
```json
{
  "name": "max_archive_size",
  "params": {
    "max_size_mb": 50    // 50MB limit
  }
}
```

**Error Response Example:**
```json
{
  "detail": {
    "validation_failed": true,
    "errors": [
      {
        "code": "repositorySizeExceeded",
        "actual_size_mb": 125.45,
        "actual_size_bytes": 131534848,
        "max_size_mb": 100,
        "file_count": 1247,
        "excess_mb": 25.45,
        "message": "Repository size 125.45MB exceeds maximum allowed size of 100MB"
      }
    ]
  }
}
```

</details>

#### 3. Directory Structure Rule (`directory_structure`)
Validates project directory structure and architecture patterns.

<details>
<summary><strong>🏗️ Directory Structure Rule Examples</strong></summary>

**Basic Usage:**
```json
{
  "name": "directory_structure",
  "params": {
    "required_directories": ["src", "tests", "docs"],
    "forbidden_directories": ["node_modules", "__pycache__"]
  }
}
```

**Architecture Validation:**
```json
{
  "name": "directory_structure",
  "params": {
    "required_directories": [
      "src",
      "src/components",
      "src/utils",
      "tests",
      "tests/unit",
      "tests/integration",
      "docs",
      "config"
    ],
    "forbidden_directories": [
      "node_modules",
      "__pycache__",
      "*.tmp",
      "build",
      "dist",
      ".vscode",
      ".idea"
    ],
    "max_depth": 5,
    "allow_empty_dirs": false
  }
}
```

**Clean Code Structure:**
```json
{
  "name": "directory_structure",
  "params": {
    "required_directories": [
      "src",
      "tests",
      "docs"
    ],
    "forbidden_directories": [
      "node_modules",
      "__pycache__",
      "*.log",
      "tmp",
      "temp"
    ],
    "max_depth": 4,
    "allow_empty_dirs": false
  }
}
```

**Error Response Example:**
```json
{
  "detail": {
    "validation_failed": true,
    "errors": [
      {
        "code": "directoryStructureValidationFailed",
        "errors": [
          {
            "code": "missingRequiredDirectories",
            "missing_directories": ["tests", "docs"],
            "patterns": ["src", "tests", "docs"],
            "message": "Missing required directories: tests, docs"
          },
          {
            "code": "forbiddenDirectoriesFound",
            "forbidden_directories": ["node_modules", "__pycache__"],
            "patterns": ["node_modules", "__pycache__", "*.tmp"],
            "message": "Forbidden directories found: node_modules, __pycache__"
          },
          {
            "code": "directoryDepthExceeded",
            "violations": [
              {
                "directory": "src/components/ui/buttons/primary",
                "depth": 6,
                "max_allowed": 4
              }
            ],
            "max_depth": 4,
            "message": "Directory depth exceeded: 1 directories exceed maximum depth of 4"
          }
        ],
        "message": "Directory structure validation failed with 3 error(s)"
      }
    ]
  }
}
```

</details>

### Creating Submissions with Rules

<details>
<summary><strong>🚀 Complete Submission Examples</strong></summary>

**Simple Submission with Rules:**
```bash
curl -X POST http://localhost:8001/submissions \
  -H "Content-Type: application/json" \
  -d '{
    "link": "https://github.com/user/repository.git",
    "project_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "group_uuid": "550e8400-e29b-41d4-a716-446655440001",
    "project_step_uuid": "550e8400-e29b-41d4-a716-446655440002",
    "description": "Final submission for step 1",
    "submitted_by_uuid": "550e8400-e29b-41d4-a716-446655440005",
    "rules": [
      {
        "name": "file_presence",
        "params": {
          "must_exist": ["README*", "*.md"],
          "forbidden": ["*.tmp", "*.log"]
        }
      },
      {
        "name": "max_archive_size",
        "params": {
          "max_size_mb": 50
        }
      }
    ]
  }'
```

**Complex Validation Example:**
```bash
curl -X POST http://localhost:8001/submissions \
  -H "Content-Type: application/json" \
  -d '{
    "link": "https://github.com/student/project.git",
    "project_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "group_uuid": "550e8400-e29b-41d4-a716-446655440001",
    "project_step_uuid": "550e8400-e29b-41d4-a716-446655440003",
    "description": "Final project submission",
    "submitted_by_uuid": "550e8400-e29b-41d4-a716-446655440006",
    "rules": [
      {
        "name": "file_presence",
        "params": {
          "must_exist": [
            "README.md",
            "requirements.txt",
            "src/**/*.py",
            "tests/**/*.py",
            "docs/*.md"
          ],
          "forbidden": [
            "*.pyc",
            "__pycache__/*",
            "*.tmp",
            "*.log",
            ".env",
            "node_modules/*",
            "*.class"
          ]
        }
      },
      {
        "name": "directory_structure",
        "params": {
          "required_directories": [
            "src",
            "tests",
            "docs",
            "src/models",
            "src/utils"
          ],
          "forbidden_directories": [
            "node_modules",
            "__pycache__",
            "build",
            "dist",
            "*.tmp"
          ],
          "max_depth": 4,
          "allow_empty_dirs": false
        }
      },
      {
        "name": "max_archive_size",
        "params": {
          "max_size_mb": 25
        }
      }
    ]
  }'
```

**Successful Response:**
```json
{
  "success": true,
  "message": "Submission created successfully",
  "submission_id": "uuid-here",
  "data": {
    "link": "https://github.com/user/repository.git",
    "project_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "group_uuid": "550e8400-e29b-41d4-a716-446655440001",
    "project_step_uuid": "550e8400-e29b-41d4-a716-446655440002",
    "link_type": "github",
    "description": "Final submission for step 1",
    "id": "uuid-here",
    "upload_date_time": "2024-01-15T10:30:00Z",
    "status": "pending"
  },
  "rule_results": [
    {
      "rule_name": "file_presence", 
      "passed": true,
      "message": "All required files are present and no forbidden files found"
    },
    {
      "rule_name": "directory_structure",
      "passed": true,
      "message": "Directory structure validation passed: 8 directories checked, max depth: 4"
    },
    {
      "rule_name": "max_archive_size",
      "passed": true, 
      "message": "Repository size 15.2MB is within limit of 25MB"
    }
  ]
}
```

</details>

### Error Handling

The service provides detailed, structured error responses for better debugging and programmatic handling.

<details>
<summary><strong>🚨 Error Response Examples</strong></summary>

**Parameter Type Error:**
```json
{
  "detail": {
    "validation_failed": true,
    "failed_rule_count": 1,
    "total_rule_count": 1,
    "errors": [
      {
        "code": "invalidParameterType",
        "parameter": "forbidden",
        "expected_type": "array",
        "actual_type": "str", 
        "actual_value": "*.md",
        "message": "Parameter 'forbidden' must be a list of patterns, got str: *.md",
        "rule_name": "file_presence",
        "rule_params": {
          "must_exist": ["README*"],
          "forbidden": "*.md"
        }
      }
    ],
    "summary": "Submission validation failed: 1 of 1 rules failed"
  }
}
```

**Multiple Rule Failures:**
```json
{
  "detail": {
    "validation_failed": true,
    "failed_rule_count": 2,
    "total_rule_count": 2,
    "errors": [
      {
        "code": "fileValidationFailed",
        "errors": [
          {
            "code": "missingRequiredFiles",
            "missing_files": ["README.md", "requirements.txt"],
            "message": "Missing required files: README.md, requirements.txt"
          }
        ],
        "rule_name": "file_presence"
      },
      {
        "code": "repositorySizeExceeded",
        "actual_size_mb": 75.2,
        "max_size_mb": 50,
        "excess_mb": 25.2,
        "rule_name": "max_archive_size"
      }
    ],
    "summary": "Submission validation failed: 2 of 2 rules failed"
  }
}
```

**Error Codes:**
- `invalidParameterType`: Wrong parameter data type
- `invalidParameterValue`: Parameter value out of valid range
- `invalidPatternType`: File pattern not a string
- `missingRequiredParameters`: Required parameters not provided
- `missingRequiredFiles`: Required files not found
- `forbiddenFilesFound`: Forbidden files detected
- `fileValidationFailed`: Multiple file validation errors
- `repositorySizeExceeded`: Repository too large
- `missingRequiredDirectories`: Required directories not found
- `forbiddenDirectoriesFound`: Forbidden directories detected
- `directoryDepthExceeded`: Directory nesting too deep
- `emptyDirectoriesFound`: Empty directories detected (when not allowed)
- `directoryStructureValidationFailed`: Multiple directory validation errors
- `ruleExecutionError`: Unexpected rule execution error

</details>

### Rule Management

<details>
<summary><strong>⚙️ Rule Management API</strong></summary>

**Get Available Rules:**
```bash
curl http://localhost:8001/submissions/rules/available
```

Response:
```json
{
  "available_rules": ["file_presence", "max_archive_size"],
  "total_count": 2,
  "description": "These rules can be used in the 'rules' field when creating submissions"
}
```

**Get Detailed Rule Documentation:**
```bash
curl http://localhost:8001/submissions/rules/documentation
```

**Disable Rule Execution:**
```bash
curl -X POST "http://localhost:8001/submissions" \
  -H "Content-Type: application/json" \
  -d '{"link": "...", "rules": [...]}'
```

</details>

## API Endpoints

Swagger UI is available at [http://localhost:8000/swagger-ui](http://localhost:8000/swagger-ui) for interactive API documentation.

## Quick Start

<details>
<summary><strong>🏃‍♂️ Getting Started</strong></summary>

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd PAMP-submissions-service
   ```

2. **Start with Docker Compose:**
   ```bash
   docker compose up --build
   ```

3. **Access the API:**
   - API: http://localhost:8001
   - Swagger UI: http://localhost:8001/swagger-ui
   - Health Check: http://localhost:8001/health

4. **Test with a simple submission:**
   ```bash
   curl -X POST http://localhost:8001/submissions \
     -H "Content-Type: application/json" \
     -d '{
       "link": "https://github.com/octocat/Hello-World.git",
       "project_uuid": "550e8400-e29b-41d4-a716-446655440000",
       "group_uuid": "550e8400-e29b-41d4-a716-446655440001",
       "project_step_uuid": "550e8400-e29b-41d4-a716-446655440004",
       "rules": [
         {
           "name": "file_presence",
           "params": {
             "must_exist": ["README*"]
           }
         }
       ]
     }'
   ```

</details>

## Technology Stack

- **FastAPI** - High-performance async web framework
- **SQLModel** - SQL databases with Python objects
- **PostgreSQL** - Reliable ACID-compliant database
- **Pydantic** - Data validation and serialization
- **Docker** - Containerization
- **Git** - Repository cloning and analysis

## Contributing
Clarence HIRSCH
Loriane HILDERALE
Malik LAFIA