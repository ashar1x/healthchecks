"""Micro-calibration B: one if + one elif + implicit fall-through."""


def if_elif(x, y):
    if x:
        return 1
    elif y:
        return 2
    return 3
