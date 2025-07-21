import pandas as pd
from datetime import datetime, timedelta

# Load Doctor Database (make sure doctors.csv is present in the same directory)
doctor_df = pd.read_csv("doctors.csv")

# Symptom-to-Specialization Map
symptom_specialization_map = {
    "fever": "General Medicine",
    "cough": "General Medicine",
    "heart pain": "Cardiologist",
    "chest pain": "Cardiologist",
    "ear pain": "ENT Surgeon",
    "throat pain": "ENT Surgeon",
    "skin rash": "Dermatology",
    "pimple": "Dermatology",
    "tooth pain": "Dentist",
    "urine issue": "Urologist",
    "pregnancy": "Gynecologist",
    "child fever": "Pediatrician",
    "muscle pain": "Orthopedic",
    "joint pain": "Orthopedic",
    "mental stress": "Neuropsychiatrist"
}

def predict_specialization(symptom):
    for keyword, specialization in symptom_specialization_map.items():
        if keyword in symptom.lower():
            return specialization
    return "General Medicine"  # fallback to general

def generate_slots(visiting_time):
    try:
        if visiting_time.lower() == "not specified":
            return ["Visiting Time Not Specified"]
        
        start, end = visiting_time.replace('pm', 'PM').replace('am', 'AM').split('-')
        start_time = datetime.strptime(start.strip(), "%I.%M%p")
        end_time = datetime.strptime(end.strip(), "%I.%M%p")

        slots = []
        while start_time + timedelta(minutes=30) <= end_time:
            slot = f"{start_time.strftime('%I:%M %p')} - {(start_time + timedelta(minutes=30)).strftime('%I:%M %p')}"
            slots.append(slot)
            start_time += timedelta(minutes=30)
        return slots
    except Exception as e:
        return ["Slot Info Unavailable"]

def recommend_doctors(symptom, preferred_time=None):
    specialization = predict_specialization(symptom)
    filtered = doctor_df[doctor_df['Specialization'].str.contains(specialization, case=False, na=False)]

    if filtered.empty:
        return f"\n❌ No doctors available for {specialization} specialization.", []

    recommendations = []
    for _, row in filtered.iterrows():
        slots = generate_slots(row['Visiting Time'])
        recommendations.append({
            "Doctor": row['Doctor Name'],
            "Specialization": row['Specialization'],
            "Chamber": row['Chamber'],
            "Slots": slots
        })

    return f"\n✅ Recommended Doctors for symptom '{symptom}' (Specialization: {specialization}):", recommendations

# Example Usage
if __name__ == "__main__":
    symptom_input = input("Enter your symptom: ")
    message, doctor_recommendations = recommend_doctors(symptom_input)
    print(message)
    for doc in doctor_recommendations:
        print(f"\nDoctor: {doc['Doctor']}\nSpecialization: {doc['Specialization']}\nChamber: {doc['Chamber']}\nAvailable Slots:")
        for slot in doc['Slots']:
            print(f" - {slot}")
