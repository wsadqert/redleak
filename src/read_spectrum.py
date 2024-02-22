import pandas as pd
import re


def read_spectrum(path: str) -> pd.DataFrame:
	with open(path) as f:
		line = f.readline()
		line = f.readline()

	df = pd.read_csv(path, delimiter='\s+', skiprows=range(3), names=line.replace('#', '').split())

	spectral_class = [int(s) for s in re.findall(r'\d+', path)][-1]
	df.rename(columns={f'ukf_m{spectral_class}iii': 'ukf_miii'}, inplace=True)

	df['lk'] /= 10

	return df[['lk', 'ukf_miii']]
