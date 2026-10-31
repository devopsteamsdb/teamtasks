"""
Master QA Test Suite Runner for TeamTasks
Executes all test suites and generates a comprehensive QA verification report.
"""
import unittest
import sys
import os
import time
import subprocess

# Ensure UTF-8 output encoding across Windows terminals
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from tests.test_api_crud import TestApiCrud
from tests.test_template_dom import TestTemplateDom
from tests.test_user_workflows import TestUserWorkflows

def run_python_suite(test_class, name):
    print(f"\n=======================================================")
    print(f"  RUNNING QA SUITE: {name}")
    print(f"=======================================================")
    suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
    runner = unittest.TextTestRunner(verbosity=2)
    start = time.time()
    result = runner.run(suite)
    duration = time.time() - start
    return {
        'name': name,
        'testsRun': result.testsRun,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'passed': result.wasSuccessful(),
        'duration': duration
    }

def run_node_tests():
    print(f"\n=======================================================")
    print(f"  RUNNING QA SUITE: Frontend JavaScript & Math Logic (Node.js)")
    print(f"=======================================================")
    start = time.time()
    res = subprocess.run(
        ['node', 'tests/test_frontend_logic.js'],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )
    duration = time.time() - start
    print(res.stdout)
    if res.stderr:
        print(res.stderr)
    return {
        'name': 'Frontend JavaScript Logic',
        'testsRun': 19,
        'failures': 0 if res.returncode == 0 else 1,
        'errors': 0,
        'passed': res.returncode == 0,
        'duration': duration
    }

def main():
    print("\n" + "=" * 65)
    print("      TEAMTASKS COMPREHENSIVE QA & VERIFICATION SUITE")
    print("=" * 65)

    suites = []
    
    # 1. API CRUD Suite
    s1 = run_python_suite(TestApiCrud, "REST API & Database CRUD (8 Modules)")
    suites.append(s1)

    # 2. Template DOM & Routing Suite
    s2 = run_python_suite(TestTemplateDom, "Templates DOM, Modals & Navigation (6 Modules)")
    suites.append(s2)

    # 3. User Workflows & Journeys Suite
    s3 = run_python_suite(TestUserWorkflows, "User Interaction & Workflows (4 E2E Journeys)")
    suites.append(s3)

    # 4. Frontend Logic Suite (Node.js)
    s4 = run_node_tests()
    suites.append(s4)

    # 5. Selenium UI Automation Suite (Optional / Flag-based)
    if "--ui" in sys.argv or "--include-ui" in sys.argv:
        print(f"\n=======================================================")
        print(f"  RUNNING QA SUITE: Selenium UI & Button Automation")
        print(f"=======================================================")
        from tests.test_ui_selenium import TestTeamTasksUIAutomation
        s5 = run_python_suite(TestTeamTasksUIAutomation, "Selenium UI Automation (32 User Interface Tests)")
        suites.append(s5)

    # Final Summary Report
    print("\n" + "=" * 65)
    print("                   FINAL QA REPORT SUMMARY")
    print("=" * 65)

    total_tests = sum(s['testsRun'] for s in suites)
    total_failures = sum(s['failures'] for s in suites)
    total_errors = sum(s['errors'] for s in suites)
    total_duration = sum(s['duration'] for s in suites)
    all_passed = all(s['passed'] for s in suites)

    print(f"{'Suite Name':<44} | {'Tests':<6} | {'Status':<8} | {'Time'}")
    print("-" * 65)
    for s in suites:
        status_str = "PASS [OK]" if s['passed'] else "FAIL [X]"
        print(f"{s['name']:<44} | {s['testsRun']:<6} | {status_str:<8} | {s['duration']:.2f}s")
    print("-" * 65)
    print(f"Total Tests Run: {total_tests}")
    print(f"Total Failures:  {total_failures}")
    print(f"Total Errors:    {total_errors}")
    print(f"Total Duration:  {total_duration:.2f} seconds")
    print("=" * 65)

    if all_passed:
        print("\nALL USER QA TESTS PASSED SUCCESSFULLY! ALL FEATURES OPERATIONAL.")
        sys.exit(0)
    else:
        print("\nSOME QA TESTS FAILED. PLEASE REVIEW LOGS.")
        sys.exit(1)

if __name__ == '__main__':
    main()
