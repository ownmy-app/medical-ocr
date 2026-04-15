"""
Synthetic medical document generator for benchmarking.
Creates text-based PDFs with known medical content so extraction accuracy
can be measured with known ground truth.
"""
import os
import tempfile
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from fpdf import FPDF


@dataclass
class GroundTruth:
    """Known entities embedded in a synthetic document."""
    icd_codes: List[str] = field(default_factory=list)
    cpt_codes: List[str] = field(default_factory=list)
    medications: List[Dict[str, str]] = field(default_factory=list)
    body_parts: List[str] = field(default_factory=list)
    provider: Optional[str] = None
    facility: Optional[str] = None
    restrictions: List[str] = field(default_factory=list)
    mmi: Optional[bool] = None
    impairment: Optional[str] = None
    doc_type: str = "General Medical Record"
    future_needs: List[str] = field(default_factory=list)
    causation: Optional[str] = None


def _make_pdf(text: str, output_path: str) -> str:
    """Create a simple text-based PDF from a string."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    for line in text.split("\n"):
        pdf.cell(0, 6, line.strip(), new_x="LMARGIN", new_y="NEXT")
    pdf.output(output_path)
    return output_path


def soap_note():
    text = """Clinic: Main Street Medical Center
Provider: Dr. Sarah Johnson
Date: 03/15/2024

SUBJECTIVE:
Patient is a 45-year-old male presenting with persistent low back pain
following a motor vehicle accident on 01/10/2024. He complains of radiating
pain down the left leg. He reports numbness and tingling in the left foot.
History of hypertension controlled with Lisinopril 20 mg daily.

OBJECTIVE:
Vital signs stable. Lumbar spine tenderness to palpation at L4-L5.
Straight leg raise positive on left at 40 degrees.
Range of motion limited in lumbar flexion.
No neurological deficits noted in upper extremities.

ASSESSMENT:
M54.5 - Low back pain
M54.16 - Radiculopathy, lumbar region
G89.29 - Other chronic pain
S33.100A - Subluxation of lumbar vertebra

CPT Codes: 99214, 97140, 97110

PLAN:
Continue Gabapentin 300 mg three times daily for neuropathic pain.
Start Meloxicam 15 mg daily for inflammation.
Referral for lumbar MRI.
Physical therapy 2-3 times per week for 6 weeks.
Follow-up in 4 weeks.
Restrictions: No lifting over 15 pounds. No prolonged standing.
Light duty recommended."""

    gt = GroundTruth(
        icd_codes=["M54.5", "M54.16", "G89.29", "S33.100A"],
        cpt_codes=["99214", "97140", "97110"],
        medications=[
            {"name": "Gabapentin", "dosage": "300 mg"},
            {"name": "Meloxicam", "dosage": "15 mg"},
            {"name": "Lisinopril", "dosage": "20 mg"},
        ],
        body_parts=["lumbar", "back", "leg", "foot", "spine"],
        provider="Sarah Johnson",
        facility="Main Street Medical Center",
        restrictions=["no lifting over 15 pounds", "no prolonged standing"],
        doc_type="Clinic/Progress Note (SOAP)",
        future_needs=["lumbar MRI", "physical therapy 2-3 times per week for 6 weeks"],
    )
    return text, gt


def radiology_report():
    text = """RADIOLOGY REPORT

Facility: Regional Imaging Center
Provider: Dr. Michael Chen
Date: 03/22/2024

Exam: MRI Lumbar Spine without contrast

INDICATION:
Low back pain with left lower extremity radiculopathy.

TECHNIQUE:
Sagittal T1, T2, and STIR sequences. Axial T2 sequences through L3-S1.

FINDINGS:
L4-L5: Broad-based disc herniation measuring 5mm, causing moderate central
canal stenosis and compression of the traversing left L5 nerve root.
L5-S1: Mild disc bulge without significant neural compression.
No fracture or subluxation identified.
Conus medullaris terminates at the L1 level, normal.

IMPRESSION:
1. L4-L5 disc herniation with left L5 nerve root compression.
2. Mild degenerative changes at L5-S1.
3. No acute fracture.

ICD-10: M51.16, M51.06
CPT: 72148"""

    gt = GroundTruth(
        icd_codes=["M51.16", "M51.06"],
        cpt_codes=["72148"],
        medications=[],
        body_parts=["lumbar", "spine"],
        provider="Michael Chen",
        facility="Regional Imaging Center",
        doc_type="Radiology Report",
    )
    return text, gt


def operative_note():
    text = """OPERATIVE NOTE

Facility: St. Mary Hospital
Date: 04/15/2024
Surgeon: Dr. Robert Williams

Pre-operative Diagnosis: L4-L5 disc herniation with left L5 radiculopathy
Post-operative Diagnosis: L4-L5 disc herniation with left L5 radiculopathy

Procedure: L4-L5 microdiscectomy, left

Anesthesia: General endotracheal anesthesia
Blood Loss: Estimated 50 mL
Complications: None

Findings: Large extruded disc fragment compressing left L5 nerve root.

Plan: Patient to be discharged home with Oxycodone 5 mg every 6 hours
as needed for pain. Follow-up in 2 weeks. No bending or twisting for
6 weeks. Restrictions: No lifting over 10 pounds for 8 weeks.

ICD-10: M51.16, M51.06
CPT: 63030, 63035"""

    gt = GroundTruth(
        icd_codes=["M51.16", "M51.06"],
        cpt_codes=["63030", "63035"],
        medications=[{"name": "Oxycodone", "dosage": "5 mg"}],
        body_parts=["lumbar", "spine"],
        provider="Robert Williams",
        facility="St. Mary Hospital",
        restrictions=["no lifting over 10 pounds for 8 weeks", "no bending or twisting for 6 weeks"],
        doc_type="Operative/Procedure Note",
    )
    return text, gt


def ime_report():
    text = """INDEPENDENT MEDICAL EXAMINATION

Facility: Pacific Medical Associates
Provider: Dr. James Thompson
Date: 06/10/2024

HISTORY:
The patient was involved in a rear-end motor vehicle accident on 01/10/2024.
He reports immediate onset of neck and low back pain. He underwent
L4-L5 microdiscectomy on 04/15/2024.

DIAGNOSES:
M54.5 - Low back pain
M54.2 - Cervicalgia
M51.16 - Intervertebral disc disorder with radiculopathy, lumbar region
S13.4XXA - Sprain of ligaments of cervical spine

CURRENT MEDICATIONS:
Gabapentin 300 mg three times daily
Cyclobenzaprine 10 mg at bedtime
Ibuprofen 800 mg three times daily

MAXIMUM MEDICAL IMPROVEMENT:
The patient has reached maximum medical improvement as of 06/10/2024.

IMPAIRMENT RATING:
Based on the AMA Guides 6th Edition, the patient has a 12% whole person
impairment rating.

CAUSATION:
The injuries described are causally related to the motor vehicle accident
of 01/10/2024, based on reasonable medical probability.

FUTURE MEDICAL NEEDS:
Recommendations: continued medication management, annual follow-up with
orthopedic surgeon, possible future epidural steroid injections.

RESTRICTIONS:
No lifting over 25 pounds. No prolonged sitting beyond 45 minutes.
Avoid repetitive bending.

CPT: 99456"""

    gt = GroundTruth(
        icd_codes=["M54.5", "M54.2", "M51.16", "S13.4XXA"],
        cpt_codes=["99456"],
        medications=[
            {"name": "Gabapentin", "dosage": "300 mg"},
            {"name": "Cyclobenzaprine", "dosage": "10 mg"},
            {"name": "Ibuprofen", "dosage": "800 mg"},
        ],
        body_parts=["lumbar", "cervical", "back", "neck", "spine"],
        provider="James Thompson",
        facility="Pacific Medical Associates",
        mmi=True,
        impairment="12%",
        restrictions=["no lifting over 25 pounds", "no prolonged sitting beyond 45 minutes"],
        doc_type="General Medical Record",
        future_needs=["continued medication management", "annual follow-up with orthopedic surgeon"],
        causation="motor vehicle accident of 01/10/2024",
    )
    return text, gt


def lab_report():
    text = """LABORATORY REPORT

Facility: Quest Diagnostics
Provider: Dr. Lisa Park
Date: 02/28/2024

Patient: Jane Doe   DOB: 05/15/1978

Results:
CBC with Differential:
  WBC: 12.5 (H) - Reference Range: 4.5-11.0
  RBC: 4.2 - Reference Range: 3.8-5.2
  Hemoglobin: 11.2 (L) - Reference Range: 12.0-16.0
  Hematocrit: 33.5 (L) - Reference Range: 36.0-46.0
  Platelets: 250 - Reference Range: 150-400

Basic Metabolic Panel:
  Glucose: 142 (H) - Reference Range: 70-100
  BUN: 18 - Reference Range: 7-20
  Creatinine: 0.9 - Reference Range: 0.6-1.2
  Sodium: 140 - Reference Range: 136-145

ESR: 35 (H) - Reference Range: 0-20
CRP: 2.8 (H) - Reference Range: 0.0-1.0

ICD-10: R79.89"""

    gt = GroundTruth(
        icd_codes=["R79.89"],
        cpt_codes=[],
        medications=[],
        body_parts=[],
        provider="Lisa Park",
        facility="Quest Diagnostics",
        doc_type="Laboratory Report",
    )
    return text, gt


def physician_letter():
    text = """To: Attorney Mark Davidson
Re: Patient John Smith, DOB 03/22/1979, DOI 01/10/2024

Dear Mr. Davidson,

On behalf of my patient John Smith, I am writing to provide a summary
of his treatment following the motor vehicle accident of January 10, 2024.

Mr. Smith presented to my office on January 15, 2024 with complaints of
severe neck and lower back pain. Examination revealed limited cervical
range of motion and lumbar tenderness.

He was prescribed Naproxen 500 mg twice daily and referred for physical
therapy. An MRI of the lumbar spine revealed an L4-L5 disc herniation.
He subsequently underwent L4-L5 microdiscectomy on April 15, 2024.

The injuries are causally related to the motor vehicle accident based
on reasonable medical probability.

Sincerely,
Dr. Sarah Johnson
Main Street Medical Center"""

    gt = GroundTruth(
        icd_codes=[],
        cpt_codes=[],
        medications=[{"name": "Naproxen", "dosage": "500 mg"}],
        body_parts=["cervical", "lumbar", "neck", "back", "spine"],
        provider="Sarah Johnson",
        facility="Main Street Medical Center",
        doc_type="Physician Letter",
        causation="motor vehicle accident",
    )
    return text, gt


def workers_comp_note():
    text = """WORKERS COMPENSATION PROGRESS NOTE

Facility: Occupational Health Clinic
Provider: Dr. Amanda Torres
Date: 05/01/2024

Patient: Robert Garcia
Employer: ABC Construction
Date of Injury: 03/01/2024

SUBJECTIVE:
Patient reports ongoing right shoulder pain since falling from a scaffold
at work on 03/01/2024. Pain is 6/10 at rest and 8/10 with overhead
activities. He has been on modified duty.

OBJECTIVE:
Right shoulder: Positive Neer and Hawkins signs.
Range of motion: Forward flexion 120 degrees, abduction 100 degrees.

ASSESSMENT:
M75.110 - Incomplete rotator cuff tear, right shoulder
S42.201A - Fracture of upper end of right humerus

CPT: 99213, 97110

PLAN:
Continue Tramadol 50 mg every 8 hours as needed.
Physical therapy 3 times weekly.
Recommend: orthopedic consultation for possible surgical repair.
Restrictions: No overhead reaching. No lifting over 5 pounds with
the right arm. Light duty only."""

    gt = GroundTruth(
        icd_codes=["M75.110", "S42.201A"],
        cpt_codes=["99213", "97110"],
        medications=[{"name": "Tramadol", "dosage": "50 mg"}],
        body_parts=["shoulder", "arm"],
        provider="Amanda Torres",
        facility="Occupational Health Clinic",
        restrictions=["no overhead reaching", "no lifting over 5 pounds with the right arm"],
        doc_type="Clinic/Progress Note (SOAP)",
        future_needs=["orthopedic consultation for possible surgical repair"],
    )
    return text, gt


def emergency_dept_note():
    text = """EMERGENCY DEPARTMENT NOTE

Facility: Memorial Hospital Emergency Department
Provider: Dr. Kevin O Brien
Date: 01/10/2024

Triage Time: 14:35
Chief Complaint: Neck and back pain after motor vehicle accident

ED Course:
45-year-old male arrives via ambulance after rear-end motor vehicle collision.
Patient was the restrained driver. Airbags deployed. GCS 15.

Physical Exam:
Cervical spine: midline tenderness, paraspinal muscle spasm
Thoracic spine: non-tender
Lumbar spine: tenderness over L4-L5 region

Imaging:
CT Cervical Spine: No fracture or subluxation
X-ray Lumbar Spine: Mild degenerative changes, no acute findings

Assessment:
S13.4XXA - Cervical sprain
M54.5 - Low back pain

Medications Given:
Morphine 4 mg IV
Ondansetron 4 mg IV
Diazepam 5 mg PO

Disposition: Discharge home with:
Hydrocodone 5 mg every 6 hours as needed
Cyclobenzaprine 10 mg three times daily
Follow-up with primary care in 3 days.

CPT: 99283"""

    gt = GroundTruth(
        icd_codes=["S13.4XXA", "M54.5"],
        cpt_codes=["99283"],
        medications=[
            {"name": "Morphine", "dosage": "4 mg"},
            {"name": "Ondansetron", "dosage": "4 mg"},
            {"name": "Diazepam", "dosage": "5 mg"},
            {"name": "Hydrocodone", "dosage": "5 mg"},
            {"name": "Cyclobenzaprine", "dosage": "10 mg"},
        ],
        body_parts=["cervical", "thoracic", "lumbar", "neck", "back", "spine"],
        provider="Kevin O Brien",
        facility="Memorial Hospital Emergency Department",
        doc_type="Emergency Dept Note",
    )
    return text, gt


def therapy_note():
    text = """PHYSICAL THERAPY PROGRESS NOTE

Facility: ProMotion Physical Therapy
Provider: Dr. Emily Watson, DPT
Date: 04/01/2024

Patient: John Smith
Diagnosis: M54.5 Low back pain, M51.16 Lumbar radiculopathy

Treatment Session: 8 of 18

SUBJECTIVE:
Patient reports 5/10 pain in lower back today, improved from 7/10
at initial evaluation. Tolerated exercises well last session.

OBJECTIVE:
Lumbar ROM: Flexion 50 degrees, Extension 15 degrees
Hip flexor flexibility improved bilaterally.
Straight leg raise: positive left at 55 degrees.

TREATMENT PROVIDED:
Manual therapy - soft tissue mobilization lumbar paraspinals (15 min)
Therapeutic exercise - core stabilization program (20 min)
Neuromuscular re-education (10 min)

CPT: 97140, 97110, 97112

PLAN:
Continue physical therapy 2x/week. Progress core strengthening.
Goals on track for discharge in 5 weeks."""

    gt = GroundTruth(
        icd_codes=["M54.5", "M51.16"],
        cpt_codes=["97140", "97110", "97112"],
        medications=[],
        body_parts=["lumbar", "back", "hip"],
        provider="Emily Watson",
        facility="ProMotion Physical Therapy",
        doc_type="Therapy Note",
    )
    return text, gt


ALL_DOCUMENTS = {
    "soap_note": soap_note,
    "radiology_report": radiology_report,
    "operative_note": operative_note,
    "ime_report": ime_report,
    "lab_report": lab_report,
    "physician_letter": physician_letter,
    "workers_comp_note": workers_comp_note,
    "emergency_dept_note": emergency_dept_note,
    "therapy_note": therapy_note,
}


def generate_all_pdfs(output_dir=None):
    """Generate all synthetic PDFs and return paths with ground truth."""
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="medical_ocr_bench_")
    os.makedirs(output_dir, exist_ok=True)

    results = {}
    for name, generator in ALL_DOCUMENTS.items():
        text, gt = generator()
        pdf_path = os.path.join(output_dir, f"{name}.pdf")
        _make_pdf(text, pdf_path)
        results[name] = {
            "pdf_path": pdf_path,
            "text": text,
            "ground_truth": gt,
        }
    return results
