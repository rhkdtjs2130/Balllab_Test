# %% 
import pandas as pd
import re
import numpy as np

from IPython.display import display
# %%
df_orig = pd.read_excel("./patient_list.xlsx")
display(df_orig)

# %%
df_orig = df_orig.assign(
    phone = lambda x: x['phone'].apply(lambda y: re.sub('-', '', y)),
    birth = lambda x: x['birth'].apply(lambda y: re.sub('\.', '', y)),
    agreement = lambda x: x['agreement'].map({"Y":1, "N":0}), 
    register_date = lambda x: pd.to_datetime(x['register_date']).dt.date,
    password = "0000", 
    user_type = 0, 
    password_date = '2022-09-22',
    email = np.nan
)

# %%
columns = [
    'phone', 'email', 'username', 'birth', 'password', 
    'point', 'user_type', 'password_date', 'agreement', 'register_date'
]

patient = [
    '우가현', '박태영', '김준현', '정진규', '이원석', '이일동', '이희빈', '김우경'
]
# %%
df_orig = df_orig.query("~username.isin(@patient)")
# %%
df_orig[columns].to_csv("patient_list_2.csv", index=False, encoding='utf-8')
# %%
