import pandas as pd
import numpy as np

df = pd.read_csv('Properties.csv')

sqm_to_sqft = 10.7639

clean_area= df.area.str.replace(',','').str.replace('sq. ft', '').astype(float) / sqm_to_sqft
df['sqft_in_sqm'] = df.sqft / sqm_to_sqft
best_parsed = df[['sqft_in_sqm','sqm']].mean(axis=1)

df['link'] = df.link.str.replace('//','/')

df['best_sqm'] = np.where(pd.isnull(clean_area), best_parsed, clean_area)

df = df.drop(columns=['area', 'Unnamed: 0'])

df.to_csv('processed_data.csv')

print(df.sort_values('best_sqm',ascending=False))