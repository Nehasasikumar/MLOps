import pandas as pd
import pickle

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

df = pd.read_csv(
    "dataset/CNC_WashingMachine_Anomaly_Dataset_2000Rows.csv"
)

X = df[
    [
        "Temperature_C",
        "Vibration_mm_s",
        "RPM",
        "Pressure_bar",
        "Humidity_percent",
        "Power_kW"
    ]
]

y = df["Status"]

scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)

model = RandomForestClassifier(
    n_estimators=200,
    random_state=42
)

model.fit(X_scaled, y)

pickle.dump(
    model,
    open("sensor_model.pkl", "wb")
)

pickle.dump(
    scaler,
    open("scaler.pkl", "wb")
)

print("Sensor Model Trained")