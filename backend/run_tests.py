import unittest
import sys
import os

# Append app source directory to python load path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def run_all_backend_tests():
    print("=============================================================")
    print("         AI GOVERNANCE PLATFORM UNIFIED TEST RUNNER          ")
    print("=============================================================\n")
    
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir="tests", pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n=============================================================")
    print("                      TEST RUN SUMMARY                       ")
    print("=============================================================")
    print(f"Total Tests Run: {result.testsRun}")
    print(f"Errors Found:    {len(result.errors)}")
    print(f"Failures Found:  {len(result.failures)}")
    
    if result.wasSuccessful():
        print("   >>> STATUS: ALL PLATFORM TESTS PASSED SUCCESSFULLY! <<<")
        sys.exit(0)
    else:
        print("   >>> STATUS: SYSTEM TESTING ENCOUNTERED UNEXPECTED FAILURES! <<<")
        sys.exit(1)

if __name__ == "__main__":
    run_all_backend_tests()
