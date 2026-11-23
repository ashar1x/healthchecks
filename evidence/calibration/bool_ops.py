"""Micro-calibration C: boolean operators in one condition."""


def bool_ops(a, b, c):
    if a and b or c:
        return 1
    return 0
