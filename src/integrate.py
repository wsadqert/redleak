from typing import Callable, Sequence
from scipy import integrate


def integrate_spectrum(filters_names: Sequence[str], interpolators: dict[str, Callable], start: float, stop: float) -> dict[str, float]:
	ans: dict[str, float] = {}  # noqa

	for filter in filters_names:
		integral_ = integrate.quad(interpolators[filter], start, stop)[0]  # noqa
		ans[filter] = integral_  # noqa

	return ans
