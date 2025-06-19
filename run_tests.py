#!/usr/bin/env python3
"""
Test Runner for Tokenization and Similarity Detection Services
Runs all organized tests and provides a comprehensive test summary.
"""

import subprocess
import sys


def run_command(cmd, description):
    """Run a command and return its result."""
    print(f"\n{'=' * 60}")
    print(f"🧪 {description}")
    print(f"{'=' * 60}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ FAILED: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False


def main():
    """Run all tests and provide summary."""
    print("🚀 Running Comprehensive Test Suite")
    print("=" * 80)

    tests_passed = 0
    tests_failed = 0

    # Test suite configuration
    test_suites = [
        {
            "cmd": ["python", "-m", "pytest", "tests/domains/tokenization/", "-v"],
            "description": "Tokenization Service Tests",
        },
        {
            "cmd": ["python", "-m", "pytest", "tests/domains/detection/", "-v"],
            "description": "Similarity Detection Service Tests",
        },
        {
            "cmd": ["python", "-m", "tests.test_integration"],
            "description": "Integration Tests (Comprehensive Workflow)",
        },
    ]

    # Run each test suite
    for suite in test_suites:
        if run_command(suite["cmd"], suite["description"]):
            tests_passed += 1
        else:
            tests_failed += 1

    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print(f"✅ Test Suites Passed: {tests_passed}")
    print(f"❌ Test Suites Failed: {tests_failed}")
    print(f"📈 Success Rate: {(tests_passed / (tests_passed + tests_failed)) * 100:.1f}%")

    if tests_failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("✨ Tokenization and similarity detection services are working perfectly!")

        # Quick functionality check
        print("\n🔍 Quick Functionality Check:")
        try:
            from app.domains.tokenization.tokenization_service import TokenizationService
            from app.domains.detection.similarity_detection_service import SimilarityDetectionService

            tokenizer = TokenizationService()
            similarity = SimilarityDetectionService()

            # Quick test
            tokens = tokenizer.tokenize("def hello(): return 'world'")
            sig = similarity.get_similarity_signature(tokens)

            print(f"   ✅ Services instantiated successfully")
            print(f"   ✅ Basic tokenization: {len(tokens)} tokens")
            print(f"   ✅ Similarity signature: {len(sig)} characters")

        except Exception as e:
            print(f"   ❌ Quick check failed: {e}")

        return 0
    else:
        print(f"\n💥 {tests_failed} TEST SUITE(S) FAILED!")
        print("Please check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
