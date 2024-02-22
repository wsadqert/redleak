from typing import Callable
from math import exp
from src.constants import *


def planck_construct(T: float) -> Callable:
	def planck(wavelength: float) -> float:
		return (2 * planck_constant * wavelength ** 3) / speed_of_light ** 2 * 1 / (exp((planck_constant * wavelength) / (boltzmann_constant * T)) - 1)

	return planck
