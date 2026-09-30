"""Tiny verified example used only to test the promotion path."""
__capability__ = {
    "name": "clamp-probability",
    "origin": "lab_toolkit/examples/verified_example_test.py",
    "status": "verified",
    "verified_on": ["lower-bound", "interior", "upper-bound"],
    "known_limits": ["accepts numeric values only"],
}

def run(value):
    return max(0.0,min(1.0,float(value)))
