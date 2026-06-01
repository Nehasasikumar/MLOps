import re
import pickle

sensor_model = pickle.load(
    open("sensor_model.pkl", "rb")
)

scaler = pickle.load(
    open("scaler.pkl", "rb")
)

text_model = pickle.load(
    open("text_model.pkl", "rb")
)

# ==========================
# CHECK FOR NUMBERS
# ==========================

def contains_numbers(text):

    return bool(
        re.search(r'\d', text)
    )

# ==========================
# EXTRACT SENSOR VALUES
# ==========================

def extract_values(text):

    text = text.lower()

    temp = re.search(
        r'(\d+)\s*(?:c|°c)',
        text
    )

    vib = re.search(
        r'(\d+\.?\d*)\s*(?:mm/s)',
        text
    )

    rpm = re.search(
        r'(\d+)\s*rpm',
        text
    )

    pressure = re.search(
        r'(\d+\.?\d*)\s*bar',
        text
    )

    humidity = re.search(
        r'(\d+)\s*%',
        text
    )

    power = re.search(
        r'(\d+\.?\d*)\s*kw',
        text
    )

    values = [

        float(temp.group(1))
        if temp else 0,

        float(vib.group(1))
        if vib else 0,

        float(rpm.group(1))
        if rpm else 0,

        float(pressure.group(1))
        if pressure else 0,

        float(humidity.group(1))
        if humidity else 0,

        float(power.group(1))
        if power else 0

    ]

    return values

def predict_machine(text):

    if contains_numbers(text):

        values = extract_values(text)

        values_scaled = scaler.transform(
            [values]
        )

        prediction = sensor_model.predict(
            values_scaled
        )[0]

        if prediction == "Normal":

            action = "No Action Required"

        elif prediction == "Service Required":

            action = "Schedule Maintenance"

        else:

            action = "Immediate Repair Required"

        return {

            "status": prediction,

            "action": action

        }


    prediction = text_model.predict(
        [text]
    )[0]

    if prediction == "Normal":

        action = "No Action Required"

    elif prediction == "Service Required":

        action = "Schedule Maintenance"

    else:

        action = "Immediate Repair Required"

    return {

        "status": prediction,

        "action": action

    }