import os
from math import log10
import pandas as pd
import scipy
from matplotlib import pyplot as plt
from rich.traceback import install
from typing import Callable

from src.interpolate import create_interpolators
from src.minmax_wavelength import minmax_wavelength
from src.read_spectrum import read_spectrum
from src.plot import *
from src.constants import *
from src.integrate import integrate_spectrum

install(show_locals=True, width=300)

spectrums: dict[str, pd.DataFrame] = {}
filters: dict[str, pd.DataFrame] = {}
perfect_filters: dict[str, pd.DataFrame] = {}

camera_data: pd.DataFrame
filters_full: dict[str, pd.DataFrame] = {}

for filename in os.listdir(path_to_spectrums):
	if '7' in filename:
		continue

	path_to_current_file = os.path.join(path_to_spectrums, filename)
	df = read_spectrum(path_to_current_file)
	i = filename.removeprefix('uk').removesuffix('iii.dat')
	spectrums[i] = df
for filename in os.listdir(path_to_filters):
	path_to_current_file = os.path.join(path_to_filters, filename)

	df = pd.read_csv(path_to_current_file, delimiter='\s+', names=['wavelength', 'sensitivity'])
	label = filename.removesuffix('_rc600.txt')

	df['sensitivity'] /= 100

	if label == 'camera':
		camera_data = df
	else:
		filters[label] = df
	filters_full[label] = df
for filename in os.listdir(path_to_perfect_filters):
	path_to_current_file = os.path.join(path_to_perfect_filters, filename)

	df = pd.read_csv(path_to_current_file, delimiter='\s+', names=['wavelength', 'sensitivity'])
	label = filename.removesuffix('1.DAT')

	df['wavelength'] /= 10
	perfect_filters[label] = df

filters_names = tuple(filters.keys())
perfect_filters_names = tuple(perfect_filters.keys())
spectrums_names = tuple(spectrums.keys())

camera_min, camera_max = minmax_wavelength(filters_full)

# cropping UBV datasets to camera's limits
for filter, df in filters.items():
	df = df[(df.wavelength >= camera_min) & (df.wavelength <= camera_max)]
	filters[filter] = df
	filters_full[filter] = df

camera_min, camera_max = minmax_wavelength(filters_full)

# filling missing values
for perfect_filter, df in perfect_filters.items():
	minfill = min(df.wavelength)
	maxfill = max(df.wavelength)

	for i in range(int(camera_min), int(minfill)+5, 5):
		df.loc[len(df)] = [float(i), 0.]
	for i in range(int(maxfill), int(camera_max)+5, 5):
		df.loc[len(df)] = [float(i), 0.]

# creating interpolators
camera_interpolator = scipy.interpolate.interp1d(camera_data.wavelength, camera_data.sensitivity, kind='cubic')  # noqa
filters_interpolators: dict[str, Callable] = create_interpolators(filters, ('wavelength', 'sensitivity'))
perfect_filters_interpolators: dict[str, Callable] = create_interpolators(perfect_filters, ('wavelength', 'sensitivity'))
spectrums_interpolators: dict[str, Callable] = create_interpolators(spectrums, ('lk', 'ukf_miii'))

# spectrums_interpolators = dict(zip(spectrums_names, [planck_construct(temperature) for temperature in (3600, 3500, 3400, 3200, 3100)]))

# rolling up filters+camera
filters_cam: dict[str, pd.DataFrame] = {}
perfect_filters_cam: dict[str, pd.DataFrame] = {}

filters_cam_interpolators: dict[str, Callable] = dict(zip(filters_names, [lambda x: (filters_interpolators[filter](x) * camera_interpolator(x)) for filter in filters_names]))
perfect_filters_cam_interpolators: dict[str, Callable] = dict(zip(perfect_filters_names, [lambda x: (perfect_filters_interpolators[perfect_filter](x) * camera_interpolator(x)) for perfect_filter in perfect_filters_names]))

for filter, df in filters.items():
	x = df['wavelength']
	new_sensitivity = [filters_cam_interpolators[filter](i) for i in x]
	new_filter = pd.DataFrame(zip(x, new_sensitivity), columns=['wavelength', 'sensitivity'])

	filters_cam[filter] = new_filter
for filter, df in perfect_filters.items():
	x = df['wavelength']
	new_sensitivity = [perfect_filters_cam_interpolators[filter](i) for i in x]
	new_filter = pd.DataFrame(zip(x, new_sensitivity), columns=['wavelength', 'sensitivity'])

	perfect_filters_cam[filter] = new_filter

spectrums_modified_interpolators: dict[str, dict[str, Callable]] = {}  # noqa
spectrums_perfect_modified_interpolators: dict[str, dict[str, Callable]] = {}  # noqa

for spectrum in spectrums_names:
	spectrums_modified_interpolators[spectrum] = {}
	for filter in filters_names:
		spectrums_modified_interpolators[spectrum][filter] = lambda x: (filters_cam_interpolators[filter](x) * spectrums_interpolators[spectrum](x))
for spectrum in spectrums_names:
	spectrums_perfect_modified_interpolators[spectrum] = {}
	for filter in filters_names:
		spectrums_perfect_modified_interpolators[spectrum][filter] = lambda x: (perfect_filters_cam_interpolators[filter](x) * spectrums_interpolators[spectrum](x))

spectrums_modified: dict[str, dict[str, pd.DataFrame]] = {}
spectrums_perfect_modified: dict[str, dict[str, pd.DataFrame]] = {}

for spectrum, df in spectrums.items():
	x = df['lk']
	for filter in filters_names:
		new_sensitivity = [spectrums_modified_interpolators[spectrum][filter](i) for i in x]
		new_filter = pd.DataFrame(zip(x, new_sensitivity), columns=['lk', 'ukf_miii'])

		spectrums_modified[spectrum][filter] = new_filter
for spectrum, df in spectrums.items():
	x = df['lk']
	for filter in perfect_filters_names:
		new_sensitivity = [spectrums_perfect_modified_interpolators[spectrum][filter](i) for i in x]
		new_filter = pd.DataFrame(zip(x, new_sensitivity), columns=['lk', 'ukf_miii'])

		spectrums_perfect_modified[spectrum][filter] = new_filter

print(spectrums_modified)

for spectrum, df_spectrum in spectrums_modified.items():
	integrated_spectrums: dict[str, float] = integrate_spectrum(filters_names, spectrums_modified_interpolators[spectrum], camera_min, camera_max)
	integrated_perfect_spectrums: dict[str, float] = integrate_spectrum(perfect_filters_names, spectrums_perfect_modified_interpolators[spectrum], camera_min, camera_max)

	dm_filters: dict[str, float] = {}
	full_sp_density_ratio_filters: dict[str, float] = {}

	for i in perfect_filters_names:
		ratio = integrated_spectrums[i] / integrated_perfect_spectrums[i]
		full_sp_density_ratio_filters[i] = 100 * (ratio-1)
		dm_filters[i] = -2.5 * log10(ratio)

	print(spectrum)
	# print(dm_filters)
	print(full_sp_density_ratio_filters)
	print()

for sp, df in spectrums.items():
	plot_spectrum(df, sp)

plt.figure()
plt.grid(True, linestyle='dashed')

plt.title('m2-6')
plt.xlabel('Wavelength, angstron')
plt.ylabel('Spectral radiance')

plt.plot(spectrums['m2'].lk, spectrums['m2'].ukf_miii)
plt.plot(spectrums['m6'].lk, spectrums['m6'].ukf_miii)

plt.savefig(f'images/spectrum_m2-6.png')
