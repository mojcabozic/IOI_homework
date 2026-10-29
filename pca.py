import json, os
import pandas as pd
from sklearn.impute import SimpleImputer # for imputing missing values
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
#from sklearn.linear_model import LogisticRegression

# load json file
with open("penguins.json") as f:
    data = json.load(f)

df = pd.DataFrame(data)

numerical_cols = [
    "bill_length_mm",
    "bill_depth_mm",
    "flipper_length_mm",
    "body_mass_g"
]

# samo stevilcni atributi
X = df[numerical_cols]

# Handle missing values using the median
imputer = SimpleImputer(strategy="median")
X_imputed = imputer.fit_transform(X)

# normaliziramo podatke
Z = StandardScaler().fit_transform(X_imputed)

# ustvari pca objekt (hocemo 2 komponenti)
pca = PCA(n_components=2)
pc = pca.fit_transform(Z)

# ustvarimo novo tabelo
df_pca = pd.DataFrame({
    "PC1": pc[:, 0],
    "PC2": pc[:, 1],
    "species": df["species"],
    "sex": df["sex"],
    "island": df["island"]
})

df_pca.to_json("pca_penguins.json", orient="records", indent=2)
