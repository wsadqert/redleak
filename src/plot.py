import matplotlib.pyplot as plt

__all__ = ['plot_spectrum']


def plot_spectrum(df, name: str = ''):
	plt.figure()
	plt.grid(True, linestyle='dashed')

	plt.title(name)
	plt.xlabel('Wavelength, angstron')
	plt.ylabel('Spectral radiance')

	plt.plot(df['lk'], df['ukf_miii'])
	plt.savefig(f'images/spectrum_{name}.png')
