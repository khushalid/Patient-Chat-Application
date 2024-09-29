NODES = {
    'Patient': [
        'First Name', 'Last Name', 'Date of Birth', 'Phone Number', 
        'Email', 'Medical Condition', 'Medication Regimen', 
        'Last Appointment DateTime', 'Next Appointment DateTime'
    ],
    'Doctor': ['Name'],
    'Appointment': ['DateTime'],
    'Medication': ['Name', 'Dosage', 'Frequency'],
    'MedicalCondition': ['Name']
}

RELATIONSHIPS = {
    'Patient': ['HAS_APPOINTMENT', 'HAS_CONDITION', 'TAKES_MEDICATION'],
    'Doctor': ['TREATS'],
    'Appointment': ['WITH_DOCTOR'],
    'Medication': ['PRESCRIBED_FOR'],
    'MedicalCondition': ['TREATED_WITH']
}