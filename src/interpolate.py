import pandas as pd
from scipy import interpolate
from typing import Callable, Sequence


def create_interpolators(dataset: dict[str, pd.DataFrame], columns: Sequence) -> dict[str, Callable]:
	ans: dict[str, Callable] = {}
	for spectrum, df in dataset.items():
		x = df[columns[0]]
		y = df[columns[1]]

		dict__ = dict(zip(x, y))
		x = list(dict__.keys())
		y = list(dict__.values())

		interpolator = interpolate.interp1d(x, y, kind='cubic')
		ans[spectrum] = interpolator
	return ans
