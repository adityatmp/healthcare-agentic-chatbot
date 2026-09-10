"""
Authoritative Healthcare Terminology Reference Dataset.

Sources:
- American Heart Association (AHA)
- Centers for Disease Control and Prevention (CDC)
- World Health Organization (WHO) Clinical Terminology Standards
"""

CLINICAL_TERMINOLOGY: dict[str, dict] = {
    "hypertension": {
        "canonical_name": "Hypertension (High Blood Pressure)",
        "definition": (
            "A chronic medical condition where the force of blood against the artery walls "
            "is consistently too high, clinically defined by the American Heart Association and "
            "CDC as systolic blood pressure >= 130 mmHg or diastolic blood pressure >= 80 mmHg."
        ),
        "category": "Cardiovascular",
        "clinical_reference": "AHA/ACC 2017 Guidelines & CDC Blood Pressure Standards",
        "related_terms": [
            "systolic blood pressure",
            "diastolic blood pressure",
            "stage 1 hypertension",
            "stage 2 hypertension",
            "hypertensive crisis",
            "dash diet",
        ],
    },
    "systolic blood pressure": {
        "canonical_name": "Systolic Blood Pressure (SBP)",
        "definition": (
            "The top number in a blood pressure reading, measuring the lateral pressure exerted "
            "by blood against arterial walls when the heart's ventricles contract and pump blood."
        ),
        "category": "Vital Signs & Hemodynamics",
        "clinical_reference": "AHA / CDC Clinical Measurement Standards",
        "related_terms": ["diastolic blood pressure", "hypertension", "blood pressure"],
    },
    "diastolic blood pressure": {
        "canonical_name": "Diastolic Blood Pressure (DBP)",
        "definition": (
            "The bottom number in a blood pressure reading, measuring the pressure in the arteries "
            "when the heart muscle rests between contractions and refills with blood."
        ),
        "category": "Vital Signs & Hemodynamics",
        "clinical_reference": "AHA / CDC Clinical Measurement Standards",
        "related_terms": ["systolic blood pressure", "hypertension", "blood pressure"],
    },
    "blood pressure": {
        "canonical_name": "Blood Pressure (BP)",
        "definition": (
            "The hydrostatic pressure exerted by circulating blood upon the walls of blood vessels, "
            "conventionally measured in millimeters of mercury (mmHg) as systolic over diastolic pressure."
        ),
        "category": "Vital Signs & Hemodynamics",
        "clinical_reference": "WHO Medical Terminology Standards",
        "related_terms": ["systolic blood pressure", "diastolic blood pressure", "hypertension", "hypotension"],
    },
    "dash diet": {
        "canonical_name": "DASH Diet (Dietary Approaches to Stop Hypertension)",
        "definition": (
            "An evidence-based nutritional eating pattern designed to lower blood pressure without medication. "
            "It emphasizes whole grains, fruits, vegetables, and low-fat dairy products while limiting saturated "
            "fats and restricting sodium intake to 2,300 mg (standard) or 1,500 mg (lower sodium tier) daily."
        ),
        "category": "Dietary & Lifestyle Intervention",
        "clinical_reference": "National Heart, Lung, and Blood Institute (NHLBI) & CDC",
        "related_terms": ["hypertension", "sodium restriction", "cardiovascular health"],
    },
    "tachycardia": {
        "canonical_name": "Tachycardia",
        "definition": (
            "A cardiac rhythm condition characterized by a resting heart rate that exceeds 100 beats per minute (bpm) "
            "in adults, which can arise from physiological stress, fever, or electrical conduction anomalies."
        ),
        "category": "Cardiovascular & Electrophysiology",
        "clinical_reference": "AHA Clinical Electrophysiology Guidelines",
        "related_terms": ["bradycardia", "arrhythmia", "vital signs"],
    },
    "bradycardia": {
        "canonical_name": "Bradycardia",
        "definition": (
            "A cardiac rhythm condition characterized by an abnormally slow resting heart rate under 60 beats "
            "per minute (bpm) in adults, which may be benign in conditioned athletes or indicate conduction pathway dysfunction."
        ),
        "category": "Cardiovascular & Electrophysiology",
        "clinical_reference": "AHA Clinical Electrophysiology Guidelines",
        "related_terms": ["tachycardia", "arrhythmia", "vital signs"],
    },
    "hypotension": {
        "canonical_name": "Hypotension (Low Blood Pressure)",
        "definition": (
            "A condition characterized by abnormally low blood pressure readings, generally defined as less than "
            "90 mmHg systolic or 60 mmHg diastolic, which may cause dizziness, fainting, or inadequate organ perfusion."
        ),
        "category": "Cardiovascular",
        "clinical_reference": "AHA Hemodynamic Reference",
        "related_terms": ["hypertension", "blood pressure", "orthostatic hypotension"],
    },
    "arrhythmia": {
        "canonical_name": "Cardiac Arrhythmia",
        "definition": (
            "A group of conditions in which the heartbeat is irregular, too fast, or too slow, caused by "
            "disruptions in the heart's electrical conduction system."
        ),
        "category": "Cardiovascular & Electrophysiology",
        "clinical_reference": "AHA / Heart Rhythm Society Guidelines",
        "related_terms": ["tachycardia", "bradycardia", "atrial fibrillation"],
    },
    "atherosclerosis": {
        "canonical_name": "Atherosclerosis",
        "definition": (
            "A specific type of arteriosclerosis characterized by the progressive narrowing and stiffening of arteries "
            "due to the buildup of fibrofatty plaques (atheromas) consisting of cholesterol, calcium, and cellular debris."
        ),
        "category": "Cardiovascular Pathology",
        "clinical_reference": "AHA Vascular Disease Guidelines",
        "related_terms": ["hypertension", "coronary artery disease", "myocardial infarction"],
    },
    "myocardial infarction": {
        "canonical_name": "Myocardial Infarction (Heart Attack)",
        "definition": (
            "Ischemic necrosis of myocardial tissue resulting from acute and sustained obstruction of a coronary artery, "
            "depriving cardiac myocytes of vital oxygen."
        ),
        "category": "Cardiovascular Pathology",
        "clinical_reference": "ACC / AHA Universal Definition of Myocardial Infarction",
        "related_terms": ["atherosclerosis", "angina", "coronary artery disease"],
    },
    "stage 1 hypertension": {
        "canonical_name": "Stage 1 Hypertension",
        "definition": (
            "A blood pressure category defined by a systolic reading of 130–139 mmHg or a diastolic reading of 80–89 mmHg. "
            "Clinical guidelines typically recommend lifestyle modifications and risk evaluation."
        ),
        "category": "Cardiovascular Staging",
        "clinical_reference": "2017 ACC/AHA Guideline",
        "related_terms": ["hypertension", "stage 2 hypertension", "dash diet"],
    },
    "stage 2 hypertension": {
        "canonical_name": "Stage 2 Hypertension",
        "definition": (
            "A blood pressure category defined by a systolic reading of 140 mmHg or higher, or a diastolic reading of 90 mmHg or higher. "
            "Guidelines typically recommend combination lifestyle intervention and clinical monitoring."
        ),
        "category": "Cardiovascular Staging",
        "clinical_reference": "2017 ACC/AHA Guideline",
        "related_terms": ["hypertension", "stage 1 hypertension", "hypertensive crisis"],
    },
    "hypertensive crisis": {
        "canonical_name": "Hypertensive Crisis",
        "definition": (
            "A severe, acute spike in blood pressure where systolic exceeds 180 mmHg and/or diastolic exceeds 120 mmHg, "
            "requiring urgent or emergent medical evaluation to assess or prevent target organ damage."
        ),
        "category": "Cardiovascular Emergencies",
        "clinical_reference": "AHA Emergency Cardiovascular Care Guidelines",
        "related_terms": ["hypertension", "stage 2 hypertension"],
    },
}
