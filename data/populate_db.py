from services.database_service import SessionLocal, DocumentChecklist

def populate_requirements():
    db = SessionLocal()
    requirements = [
        # Subclass 842: Offshore Humanitarian
        ('842', 'Form 842', True, 'Forms', 'Offshore Humanitarian visa application form'),
        ('842', 'Form 681', True, 'Forms', 'Proposer details from Australian sponsor'),
        ('842', 'Valid Passport', True, 'Identity', 'All pages including blank pages'),
        ('842', 'Birth Certificate', True, 'Identity', 'With English translation if applicable'),
        ('842', 'UNHCR Registration', False, 'Humanitarian', 'UNHCR registration documents if applicable'),
        
        # Subclass 189: Skilled Independent
        ('189', 'Skills Assessment', True, 'Professional', 'Assessment from relevant authority (e.g., Engineers Australia)'),
        ('189', 'English Test Results', True, 'Language', 'IELTS/PTE results less than 3 years old'),
        ('189', 'Employment References', True, 'Experience', 'Detailed letters on company letterhead'),
        ('189', 'Educational Qualifications', True, 'Education', 'Degree certificates and transcripts'),
        
        # Subclass 500: Student
        ('500', 'Confirmation of Enrolment (CoE)', True, 'Education', 'From CRICOS-registered institution'),
        ('500', 'Genuine Student Statement', True, 'Compliance', '300-500 words explaining study intent'),
        ('500', 'Evidence of Funds', True, 'Financial', 'Bank statements showing living costs and tuition'),
        ('500', 'OSHC', True, 'Health', 'Overseas Student Health Cover receipt'),
    ]
    
    for subclass, name, required, category, desc in requirements:
        checklist_item = DocumentChecklist(
            visa_subclass=subclass,
            document_name=name,
            is_required=required,
            category=category,
            description=desc
        )
        db.add(checklist_item)
    
    db.commit()
    print("Database populated with visa requirements.")

if __name__ == "__main__":
    populate_requirements()
