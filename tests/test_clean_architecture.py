import pytest
from datetime import datetime
from app.domain.entities.submission import Submission
from app.domain.entities.cheat_detection import CheatDetection
from app.domain.value_objects.submission_status import SubmissionStatus
from app.domain.value_objects.cheat_type import CheatType
from app.domain.value_objects.file_info import FileInfo
from app.application.dto.submission_dto import CreateSubmissionDTO
from app.application.dto.cheat_detection_dto import CreateCheatDetectionDTO


class TestDomainEntities:
    """Test domain entities and business rules"""
    
    def test_submission_creation(self):
        """Test submission entity creation with business rules"""
        file_info = FileInfo(path="test.py", hash="sha256:abc123", size=1024)
        
        submission = Submission(
            id=None,
            student_id="student123",
            project_id="project456",
            file_info=file_info,
            submission_time=datetime.utcnow(),
            status=SubmissionStatus.PENDING,
            metadata={"language": "python"}
        )
        
        assert submission.student_id == "student123"
        assert submission.project_id == "project456"
        assert submission.status == SubmissionStatus.PENDING
        assert not submission.is_suspicious()
        assert submission.can_be_analyzed()
    
    def test_submission_business_rules(self):
        """Test submission business rules"""
        file_info = FileInfo(path="test.py", size=50)  # Suspicious size
        
        submission = Submission(
            id=1,
            student_id="student123",
            project_id="project456",
            file_info=file_info,
            submission_time=datetime.utcnow(),
            status=SubmissionStatus.PENDING,
            metadata={}
        )
        
        # Test flagging
        submission.flag_for_review("Test reason")
        assert submission.status == SubmissionStatus.FLAGGED
        assert submission.is_suspicious()
        
        # Test approval
        submission.approve()
        assert submission.status == SubmissionStatus.COMPLETED
    
    def test_cheat_detection_creation(self):
        """Test cheat detection entity creation"""
        detection = CheatDetection(
            id=None,
            submission_id=1,
            cheat_type=CheatType.PLAGIARISM,
            confidence_score=0.95,
            description="High similarity detected",
            evidence={"similarity": 0.95}
        )
        
        assert detection.submission_id == 1
        assert detection.cheat_type == CheatType.PLAGIARISM
        assert detection.confidence_score == 0.95
        assert detection.is_high_confidence()
        assert detection.requires_human_review()
        assert detection.get_severity_level() == "CRITICAL"
    
    def test_cheat_detection_business_rules(self):
        """Test cheat detection business rules"""
        detection = CheatDetection(
            id=1,
            submission_id=1,
            cheat_type=CheatType.PLAGIARISM,
            confidence_score=0.95,
            description="Test detection",
            evidence={}
        )
        
        # Test confirmation
        detection.confirm("reviewer123")
        assert detection.is_confirmed
        assert detection.confirmed_by == "reviewer123"
        assert detection.confirmed_at is not None
        
        # Test dismissal (should fail for confirmed detection)
        with pytest.raises(ValueError):
            detection.dismiss()


class TestValueObjects:
    """Test value objects and their business logic"""
    
    def test_submission_status_transitions(self):
        """Test submission status transition rules"""
        status = SubmissionStatus.PENDING
        
        # Valid transitions
        assert status.can_transition_to(SubmissionStatus.PROCESSING)
        assert status.can_transition_to(SubmissionStatus.FLAGGED)
        assert status.can_transition_to(SubmissionStatus.REJECTED)
        
        # Invalid transitions
        assert not status.can_transition_to(SubmissionStatus.COMPLETED)
        
        # Terminal states
        assert not SubmissionStatus.COMPLETED.can_transition_to(SubmissionStatus.PENDING)
        assert SubmissionStatus.COMPLETED.is_terminal()
    
    def test_cheat_type_properties(self):
        """Test cheat type business logic"""
        plagiarism = CheatType.PLAGIARISM
        
        assert plagiarism.get_base_severity() == 10
        assert plagiarism.requires_immediate_action()
        assert not plagiarism.is_automated_detectable()
        assert plagiarism.get_default_threshold() == 0.9
    
    def test_file_info_validation(self):
        """Test file info value object validation"""
        # Valid file info
        file_info = FileInfo(path="test.py", hash="sha256:abc123", size=1024)
        assert file_info.get_file_extension() == "py"
        assert file_info.is_supported_file_type()
        assert not file_info.is_suspicious_size()
        
        # Suspicious file size
        small_file = FileInfo(path="test.py", size=50)
        assert small_file.is_suspicious_size()
        
        # Invalid file info
        with pytest.raises(ValueError):
            FileInfo(path="", size=1024)


class TestDTOs:
    """Test Data Transfer Objects"""
    
    def test_create_submission_dto(self):
        """Test submission creation DTO"""
        dto = CreateSubmissionDTO(
            student_id="student123",
            project_id="project456",
            file_path="test.py",
            file_hash="sha256:abc123",
            file_size=1024,
            metadata={"language": "python"}
        )
        
        assert dto.student_id == "student123"
        assert dto.project_id == "project456"
        assert dto.file_path == "test.py"
    
    def test_create_cheat_detection_dto(self):
        """Test cheat detection creation DTO"""
        dto = CreateCheatDetectionDTO(
            submission_id=1,
            cheat_type=CheatType.PLAGIARISM,
            confidence_score=0.95,
            description="Test detection",
            evidence={"similarity": 0.95}
        )
        
        assert dto.submission_id == 1
        assert dto.cheat_type == CheatType.PLAGIARISM
        assert dto.confidence_score == 0.95


class TestArchitecturalConstraints:
    """Test architectural constraints and dependencies"""
    
    def test_domain_has_no_infrastructure_dependencies(self):
        """Ensure domain layer has no infrastructure dependencies"""
        # This test ensures domain entities don't import infrastructure modules
        import app.domain.entities.submission as submission_module
        import app.domain.entities.cheat_detection as detection_module
        
        # Check that domain modules don't import infrastructure
        submission_imports = str(submission_module.__dict__)
        detection_imports = str(detection_module.__dict__)
        
        # Should not contain infrastructure imports
        assert "sqlmodel" not in submission_imports.lower()
        assert "fastapi" not in submission_imports.lower()
        assert "sqlmodel" not in detection_imports.lower()
        assert "fastapi" not in detection_imports.lower()
    
    def test_application_depends_only_on_domain(self):
        """Ensure application layer only depends on domain"""
        import app.application.use_cases.submission_use_cases as use_cases_module
        
        # Use cases should import domain but not infrastructure directly
        use_cases_source = str(use_cases_module.__dict__)
        
        # Should contain domain imports
        assert "domain" in use_cases_source.lower()
        
        # Should not directly import database models
        assert "sql_models" not in use_cases_source.lower()


if __name__ == "__main__":
    pytest.main([__file__]) 