"""

Testing guidelines:             
 
1. Tests should use the test_xxx.py naming schema.
 
2. Place unit tests in the matching library folder. These tests should be part
   of the normal code-test cycle and aren't allowed to use resources or
   interface with the OS in any way (i.e no touching the disk, accessing DB or
   network, etc). Use mockups to break dependencies. As a rule of thumb the
   entire test-suite must run under 10s on a standard developer machine.

3. Functional (acceptance) tests are placed in the matching func_* folder
   either as straight test_*.py files or a in separate sub-directories together
   with external dependencies (files, DB schemas, etc). These tests don't have
   any real limitations other than that they restore any OS and software
   configuration changes made during test execution.

"""
