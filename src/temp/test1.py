import numpy as np
import pandas as pd

df = pd.DataFrame([1, 2, 3, 4, 5], columns=['a'])
print(df[df['a']>2 ].index)
