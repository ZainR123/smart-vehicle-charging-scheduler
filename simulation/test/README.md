# Offline Simulation Testing

This directory contains all tests for the functionality of the offline simulation.

## Python Unit Testing

To write unit tests, `import` the `unittest` module for Python and subclass the `TestCase` class in the module (i.e. 
`unittest.TestCase`). All test methods **must** be prefixed with `test_`. For example, a test for the validation 
procedure 
of a component may be named something along the lines of: `test_scheduler_rejects_none_values`.

Sample code for a test class:

```python
from djangoProject.simulation import SomeScheduler
import unittest


class MyTestClass(unittest.TestCase):
    def generate_sample_timeslot_data(self):
        pass  # Generation code goes here...

    def test_scheduler_rejects_none_vehicles(self):
        """Tests if the scheduler rejects passing of None as the vehicle to be scheduled"""
        scheduler = SomeScheduler()
        timeslots = self.generate_sample_timeslot_data()  # Function for testing

        result = scheduler.schedule(None, timeslots)
        self.assertFalse(result)  # Check if returned list is empty (empty means scheduler rejected the arguments)
```

For more information on the `unittest` module, visit the [official Python standard library documentation](https://docs.python.org/3/library/unittest.html).