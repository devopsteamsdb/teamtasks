"""
Master UI & Button Automation Test Runner for TeamTasks
Executes the comprehensive Selenium WebDriver UI automation test suite covering
all views, wide 2-column modals, buttons, interactive features, admin, AI assistant,
and print views.
"""

import os
import sys
import time
import unittest
import logging

# Ensure UTF-8 output across Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Suppress noisy HTTP logs during testing for a clean presentation
logging.getLogger('werkzeug').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)
logging.getLogger('selenium').setLevel(logging.ERROR)

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from tests.test_ui_selenium import TestTeamTasksUIAutomation


def run_ui_suite():
    print("\n" + "=" * 70)
    print("      TEAMTASKS SELENIUM UI & BUTTON AUTOMATION TEST SUITE")
    print("      Modernized Wide Modals, Views, Interactions & Admin Panel")
    print("=" * 70 + "\n")

    suite = unittest.TestLoader().loadTestsFromTestCase(TestTeamTasksUIAutomation)
    runner = unittest.TextTestRunner(verbosity=2)
    start = time.time()
    result = runner.run(suite)
    duration = time.time() - start

    print("\n" + "=" * 70)
    print("                       UI AUTOMATION SUMMARY")
    print("=" * 70)
    print(f"Total Tests Run:      {result.testsRun}")
    print(f"Successful Tests:     {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed Tests:         {len(result.failures)}")
    print(f"Error Tests:          {len(result.errors)}")
    print(f"Execution Duration:   {duration:.2f} seconds")
    print("=" * 70)

    if result.wasSuccessful():
        print("\n[SUCCESS] ALL 32 UI & BUTTON AUTOMATION TESTS PASSED WITH 100% SUCCESS!\n")
        return 0
    else:
        print("\n[FAILURE] SOME UI TESTS FAILED. PLEASE CHECK TRACEBACK ABOVE.\n")
        return 1


if __name__ == '__main__':
    exit_code = run_ui_suite()
    sys.exit(exit_code)
