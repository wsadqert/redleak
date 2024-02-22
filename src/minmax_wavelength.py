import pandas as pd


def minmax_wavelength(filters: dict[str, pd.DataFrame]):
	minimal_filters = [min(filters[filter].wavelength) for filter in filters.keys()]
	maximal_filters = [max(filters[filter].wavelength) for filter in filters.keys()]

	min_ = max(minimal_filters)
	max_ = min(maximal_filters)

	return min_, max_
