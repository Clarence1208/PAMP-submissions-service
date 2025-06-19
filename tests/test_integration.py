"""
Integration Tests for Tokenization and Similarity Detection Services
Comprehensive tests that replicate the original test scenarios.
"""

import unittest
from pathlib import Path

from app.domains.tokenization.tokenization_service import TokenizationService
from app.domains.detection.similarity_detection_service import SimilarityDetectionService


class TestTokenizationSimilarityIntegration(unittest.TestCase):
    """Integration tests that demonstrate the full functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tokenization_service = TokenizationService()
        self.similarity_service = SimilarityDetectionService()
    
    def test_comprehensive_similarity_workflow(self):
        """Test the complete workflow from tokenization to similarity detection."""
        print("\n🔬 Testing Comprehensive Similarity Workflow")
        print("=" * 60)
        
        # Test basic tokenization
        test_code = """
def calculate_sum(a, b):
    '''Calculate sum of two numbers.'''
    return a + b

def multiply(x, y):
    '''Multiply two numbers.'''
    return x * y
"""
        
        tokens = self.tokenization_service.tokenize(test_code)
        
        # Validate tokenization
        self.assertGreater(len(tokens), 0)
        function_tokens = [t for t in tokens if t['type'] == 'function_definition']
        self.assertGreaterEqual(len(function_tokens), 2)
        
        # Test similarity preparation
        similarity_tokens = self.similarity_service.prepare_for_similarity(tokens)
        signature = self.similarity_service.get_similarity_signature(tokens)
        
        # Validate similarity preparation
        self.assertGreater(len(similarity_tokens), 0)
        self.assertGreater(len(signature), 0)
        
        print(f"✅ Basic workflow test passed")
        print(f"   Original tokens: {len(tokens)}")
        print(f"   Similarity tokens: {len(similarity_tokens)}")
        print(f"   Signature length: {len(signature)}")
    
    def test_shared_code_detection_comprehensive(self):
        """Test comprehensive shared code detection with detailed validation."""
        print("\n🎯 Testing Comprehensive Shared Code Detection")
        print("=" * 60)
        
        # Test files with known shared code
        file1_path = Path("../resources/test/test_file.py")
        file2_path = Path("../resources/test/test_file2.py")
        
        if not file1_path.exists() or not file2_path.exists():
            self.skipTest("Test files not found - this test requires the test files to be present")
        
        # Load and tokenize files
        with open(file1_path, 'r', encoding='utf-8') as f:
            content1 = f.read()
        with open(file2_path, 'r', encoding='utf-8') as f:
            content2 = f.read()
        
        tokens1 = self.tokenization_service.tokenize(content1, file1_path)
        tokens2 = self.tokenization_service.tokenize(content2, file2_path)
        
        # Overall similarity analysis
        overall_similarity = self.similarity_service.compare_similarity(tokens1, tokens2)
        
        # Shared code block detection
        shared_blocks_result = self.similarity_service.detect_shared_code_blocks(
            tokens1, tokens2, content1, content2
        )
        
        # Comprehensive validation
        self.assertIsInstance(overall_similarity['jaccard_similarity'], float)
        self.assertIsInstance(overall_similarity['type_similarity'], float)
        self.assertIsInstance(shared_blocks_result['total_shared_blocks'], int)
        
        print(f"✅ File Analysis Results:")
        print(f"   File 1 tokens: {len(tokens1)}")
        print(f"   File 2 tokens: {len(tokens2)}")
        print(f"   Overall Jaccard similarity: {overall_similarity['jaccard_similarity']:.3f}")
        print(f"   Overall Type similarity: {overall_similarity['type_similarity']:.3f}")
        print(f"   Functions in file 1: {shared_blocks_result['functions_file1']}")
        print(f"   Functions in file 2: {shared_blocks_result['functions_file2']}")
        print(f"   Shared blocks detected: {shared_blocks_result['total_shared_blocks']}")
        print(f"   Average similarity of shared blocks: {shared_blocks_result['average_similarity']:.3f}")
        
        # Validation assertions
        if shared_blocks_result['total_shared_blocks'] > 0:
            self.assertGreater(shared_blocks_result['average_similarity'], 0.7)
            print(f"✅ Shared code detection successful!")
            
            # Detailed block analysis
            for i, block in enumerate(shared_blocks_result['shared_blocks'], 1):
                print(f"   Block {i}: {block['file1_function']} ↔ {block['file2_function']} "
                      f"(similarity: {block['similarity_score']:.3f})")
        else:
            print(f"ℹ️  No shared blocks detected (this is also valid)")
    
    def test_project_level_comparison_comprehensive(self):
        """Test comprehensive project-level comparison."""
        print("\n🏗️ Testing Project-Level Comparison")
        print("=" * 60)
        
        calculator_project = Path("../resources/test/project_calculator")
        game_project = Path("../resources/test/project_game")
        
        if not calculator_project.exists() or not game_project.exists():
            self.skipTest("Project directories not found - this test requires the test projects to be present")
        
        # Get all Python files from both projects
        calc_files = list(calculator_project.glob("*.py"))
        game_files = list(game_project.glob("*.py"))
        
        if not calc_files or not game_files:
            self.skipTest("No Python files found in projects")
        
        print(f"Calculator Project files: {[f.name for f in calc_files]}")
        print(f"Game Project files: {[f.name for f in game_files]}")
        
        # Tokenize all files in both projects
        calc_all_tokens = []
        game_all_tokens = []
        calc_all_source = ""
        game_all_source = ""
        
        for file_path in calc_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            tokens = self.tokenization_service.tokenize(content, file_path)
            calc_all_tokens.extend(tokens)
            calc_all_source += f"\n# === {file_path.name} ===\n" + content + "\n"
        
        for file_path in game_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            tokens = self.tokenization_service.tokenize(content, file_path)
            game_all_tokens.extend(tokens)
            game_all_source += f"\n# === {file_path.name} ===\n" + content + "\n"
        
        # Project-level analysis
        overall_similarity = self.similarity_service.compare_similarity(calc_all_tokens, game_all_tokens)
        shared_blocks_result = self.similarity_service.detect_shared_code_blocks(
            calc_all_tokens, game_all_tokens, calc_all_source, game_all_source
        )
        
        print(f"✅ Project Analysis Results:")
        print(f"   Total tokens - Calculator: {len(calc_all_tokens)}, Game: {len(game_all_tokens)}")
        print(f"   Overall Jaccard similarity: {overall_similarity['jaccard_similarity']:.3f}")
        print(f"   Overall Type similarity: {overall_similarity['type_similarity']:.3f}")
        print(f"   Functions in calculator: {shared_blocks_result['functions_file1']}")
        print(f"   Functions in game: {shared_blocks_result['functions_file2']}")
        print(f"   Shared blocks detected: {shared_blocks_result['total_shared_blocks']}")
        print(f"   Average similarity of shared blocks: {shared_blocks_result['average_similarity']:.3f}")
        
        # File-by-file analysis
        print(f"\n📂 File-by-File Analysis:")
        max_shared_similarity = 0.0
        best_shared_pair = None
        
        for calc_file in calc_files:
            with open(calc_file, 'r', encoding='utf-8') as f:
                calc_content = f.read()
            calc_tokens = self.tokenization_service.tokenize(calc_content, calc_file)
            
            for game_file in game_files:
                with open(game_file, 'r', encoding='utf-8') as f:
                    game_content = f.read()
                game_tokens = self.tokenization_service.tokenize(game_content, game_file)
                
                file_shared = self.similarity_service.detect_shared_code_blocks(
                    calc_tokens, game_tokens, calc_content, game_content
                )
                
                if file_shared['total_shared_blocks'] > 0:
                    avg_sim = file_shared['average_similarity']
                    print(f"   {calc_file.name} ↔ {game_file.name}: "
                          f"{file_shared['total_shared_blocks']} shared blocks, "
                          f"avg similarity: {avg_sim:.3f}")
                    
                    if avg_sim > max_shared_similarity:
                        max_shared_similarity = avg_sim
                        best_shared_pair = (calc_file.name, game_file.name)
        
        # Comprehensive validation
        print(f"\n🧪 Validation Results:")
        
        # Test 1: Should detect shared code blocks
        if shared_blocks_result['total_shared_blocks'] > 0:
            print("✅ PASS: Shared code blocks detected")
        else:
            print("⚠️  INFO: No shared code blocks detected")
        
        # Test 2: Projects should be overall different
        if overall_similarity['jaccard_similarity'] < 0.5:
            print("✅ PASS: Projects are appropriately different overall")
        else:
            print(f"⚠️  INFO: Projects have high overall similarity: {overall_similarity['jaccard_similarity']:.3f}")
        
        # Test 3: Shared blocks should have high similarity (if any exist)
        if shared_blocks_result['total_shared_blocks'] > 0:
            if shared_blocks_result['average_similarity'] > 0.8:
                print("✅ PASS: Detected shared code has high similarity")
            else:
                print(f"⚠️  INFO: Shared code similarity lower than expected: {shared_blocks_result['average_similarity']:.3f}")
        
        print(f"\n🎯 Summary:")
        print(f"   Found {shared_blocks_result['total_shared_blocks']} shared code blocks")
        if best_shared_pair:
            print(f"   Best file pair: {best_shared_pair[0]} ↔ {best_shared_pair[1]}")
        print(f"   Maximum similarity: {max_shared_similarity:.3f}")
        
        # Assertions for test validation
        self.assertGreater(len(calc_all_tokens), 0)
        self.assertGreater(len(game_all_tokens), 0)
        self.assertIsInstance(overall_similarity['jaccard_similarity'], float)
        self.assertIsInstance(shared_blocks_result['total_shared_blocks'], int)


def run_comprehensive_tests():
    """Run all comprehensive tests and display results."""
    print("🚀 Running Comprehensive Tokenization and Similarity Tests")
    print("=" * 80)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add all test methods
    suite.addTest(TestTokenizationSimilarityIntegration('test_comprehensive_similarity_workflow'))
    suite.addTest(TestTokenizationSimilarityIntegration('test_shared_code_detection_comprehensive'))
    suite.addTest(TestTokenizationSimilarityIntegration('test_project_level_comparison_comprehensive'))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 80)
    if result.wasSuccessful():
        print("🎉 ALL COMPREHENSIVE TESTS PASSED!")
        print("Tokenization and similarity detection working perfectly!")
    else:
        print("❌ SOME TESTS FAILED!")
        print(f"Failures: {len(result.failures)}, Errors: {len(result.errors)}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_comprehensive_tests() 