"""
Advanced medical text refinement system for improving OCR text quality.
Specialized for medical records with multiple correction strategies.
"""

import re
import difflib
from typing import Dict, List, Tuple, Optional, Any, Set
from collections import Counter
import logging
from dataclasses import dataclass
from medical_ocr.injury_medical_vocabulary import ALL_INJURY_TERMS, INJURY_ABBREVIATIONS
from medical_ocr.legal_medical_vocabulary import (
    get_legal_medical_vocabulary, 
    get_legal_medical_abbreviations,
    get_legal_medical_corrections,
    calculate_legal_medical_relevance
)

logger = logging.getLogger(__name__)

# Comprehensive medical dictionary for spell checking (enhanced with legal medical terms)
MEDICAL_DICTIONARY = {
    # Common medical terms
    'patient', 'diagnosis', 'treatment', 'medication', 'prescription', 'dosage',
    'symptoms', 'examination', 'history', 'allergies', 'procedure', 'surgery',
    'consultation', 'referral', 'follow-up', 'appointment', 'evaluation',
    
    # Anatomy terms
    'head', 'neck', 'chest', 'abdomen', 'pelvis', 'spine', 'vertebrae',
    'cervical', 'thoracic', 'lumbar', 'sacral', 'coccyx', 'skull', 'brain',
    'heart', 'lungs', 'liver', 'kidneys', 'stomach', 'intestines',
    'shoulder', 'elbow', 'wrist', 'hand', 'fingers', 'hip', 'knee', 'ankle', 'foot',
    'muscle', 'bone', 'joint', 'ligament', 'tendon', 'cartilage', 'nerve',
    
    # Medical specialties
    'cardiology', 'neurology', 'orthopedics', 'dermatology', 'oncology',
    'psychiatry', 'pediatrics', 'geriatrics', 'emergency', 'radiology',
    'pathology', 'anesthesiology', 'surgery', 'medicine', 'nursing',
    
    # Common medications
    'aspirin', 'ibuprofen', 'acetaminophen', 'morphine', 'codeine', 'insulin',
    'antibiotics', 'penicillin', 'amoxicillin', 'prednisone', 'metformin',
    'lisinopril', 'atorvastatin', 'omeprazole', 'albuterol', 'warfarin',
    
    # Medical conditions
    'hypertension', 'diabetes', 'asthma', 'pneumonia', 'influenza',
    'arthritis', 'osteoporosis', 'depression', 'anxiety', 'migraine',
    'epilepsy', 'cancer', 'tumor', 'infection', 'inflammation',
    
    # Measurements and units
    'milligram', 'gram', 'kilogram', 'milliliter', 'liter', 'celsius',
    'fahrenheit', 'systolic', 'diastolic', 'beats', 'minute', 'hour',
    'daily', 'weekly', 'monthly', 'twice', 'three', 'times',
    
    # Medical procedures
    'ultrasound', 'electrocardiogram', 'echocardiogram', 'endoscopy',
    'colonoscopy', 'biopsy', 'catheter', 'intubation', 'ventilator',
    'dialysis', 'chemotherapy', 'radiation', 'immunization', 'vaccination'
}

# Add injury terms and legal medical terms to dictionary
MEDICAL_DICTIONARY.update(ALL_INJURY_TERMS)
MEDICAL_DICTIONARY.update(get_legal_medical_vocabulary())

# Common OCR character confusions in medical context
MEDICAL_CHAR_CORRECTIONS = {
    # Number/letter confusions
    '0': {'O', 'o', 'Q'},
    'O': {'0', 'Q', 'D'},
    '1': {'l', 'I', '|'},
    'l': {'1', 'I', '|'},
    'I': {'1', 'l', '|'},
    '5': {'S', 's'},
    'S': {'5', 's'},
    '8': {'B'},
    'B': {'8', 'b'},
    '6': {'G', 'b'},
    'G': {'6', 'g'},
    
    # Common medical term confusions
    'rn': {'m'},
    'cl': {'d'},
    'ri': {'n'},
    'vv': {'w'},
    'nn': {'m'},
    'u': {'n'},
    'n': {'u'},
    'c': {'e', 'o'},
    'e': {'c', 'o'},
    'a': {'o', 'e'},
    'o': {'a', 'e', '0'},
}

# Medical word patterns and their corrections
MEDICAL_WORD_PATTERNS = {
    # Common medical abbreviations that get OCR'd wrong
    r'\brnq\b': 'mg',  # milligram
    r'\brnl\b': 'ml',  # milliliter  
    r'\bkq\b': 'kg',   # kilogram
    r'\bbp\b': 'BP',   # blood pressure
    r'\bhr\b': 'HR',   # heart rate
    r'\brr\b': 'RR',   # respiratory rate
    r'\btemp\b': 'Temp',  # temperature
    
    # Common medical term OCR errors
    r'\bpatienf\b': 'patient',
    r'\bdiagnosis\b': 'diagnosis',
    r'\btreatrnent\b': 'treatment',
    r'\brnedication\b': 'medication',
    r'\bprescripfion\b': 'prescription',
    r'\bexarnination\b': 'examination',
    r'\bhistorv\b': 'history',
    r'\bsymptorns\b': 'symptoms',
    r'\bprocedure\b': 'procedure',
    r'\bconsultafion\b': 'consultation',
    r'\bevaluafion\b': 'evaluation',
    
    # Anatomy terms
    r'\bcervicai\b': 'cervical',
    r'\bthoracic\b': 'thoracic', 
    r'\blurnbar\b': 'lumbar',
    r'\bshoulder\b': 'shoulder',
    r'\brnuscle\b': 'muscle',
    r'\bligarnent\b': 'ligament',
    
    # Units and measurements  
    r'\brng\b': 'mg',
    r'\brnl\b': 'ml',
    r'\bkq\b': 'kg',
    r'\blbs\b': 'lbs',
    r'\bbrn\b': 'bpm',  # beats per minute
}

@dataclass
class TextRefinementResult:
    original_text: str
    refined_text: str
    corrections_made: List[str]
    confidence_improvement: float
    word_corrections: int
    character_corrections: int

class MedicalTextRefiner:
    """Advanced text refinement system for medical OCR results."""
    
    def __init__(self):
        self.medical_dict = MEDICAL_DICTIONARY
        self.char_corrections = MEDICAL_CHAR_CORRECTIONS
        self.word_patterns = MEDICAL_WORD_PATTERNS
        
        # Add legal medical corrections
        self.legal_medical_corrections = get_legal_medical_corrections()
        self.legal_medical_abbreviations = get_legal_medical_abbreviations()
        
        # Build word similarity cache for performance
        self._similarity_cache = {}
        
    def refine_multiple_ocr_results(self, ocr_results: List[Dict[str, Any]]) -> str:
        """
        Fuse multiple OCR results to create the best possible text.
        Uses advanced ensemble techniques and cross-validation.
        """
        if not ocr_results:
            return ""
        
        if len(ocr_results) == 1:
            return self.refine_single_text(ocr_results[0]['text'])
        
        # Step 1: Extract texts and confidences
        texts = [result['text'] for result in ocr_results]
        confidences = [result.get('confidence', 0.5) for result in ocr_results]
        
        # Step 2: Perform word-level fusion
        fused_text = self._perform_word_level_fusion(texts, confidences)
        
        # Step 3: Apply medical refinements
        refined_text = self.refine_single_text(fused_text)
        
        return refined_text
    
    def _perform_word_level_fusion(self, texts: List[str], confidences: List[float]) -> str:
        """Perform intelligent word-level fusion of multiple OCR results."""
        
        # Tokenize all texts into words
        word_lists = [text.split() for text in texts]
        
        # Find the longest sequence as base
        base_words = max(word_lists, key=len)
        fused_words = []
        
        for i in range(len(base_words)):
            candidates = []
            
            # Collect word candidates from all OCR results
            for j, words in enumerate(word_lists):
                if i < len(words):
                    candidates.append({
                        'word': words[i],
                        'confidence': confidences[j],
                        'source': j
                    })
            
            if candidates:
                # Choose best word using multiple criteria
                best_word = self._select_best_word_candidate(candidates)
                fused_words.append(best_word)
            else:
                fused_words.append(base_words[i])
        
        return ' '.join(fused_words)
    
    def _select_best_word_candidate(self, candidates: List[Dict]) -> str:
        """Select the best word from multiple candidates."""
        
        # Score each candidate
        scored_candidates = []
        
        for candidate in candidates:
            word = candidate['word']
            confidence = candidate['confidence']
            
            score = confidence * 0.4  # Base confidence score
            
            # Medical dictionary bonus
            if word.lower() in self.medical_dict:
                score += 0.3
            
            # Word quality bonus (length, alphanumeric ratio)
            if len(word) >= 3 and word.isalpha():
                score += 0.2
            
            # Injury vocabulary bonus
            if word.lower() in ALL_INJURY_TERMS:
                score += 0.1
            
            # Legal medical vocabulary bonus
            legal_medical_vocab = get_legal_medical_vocabulary()
            if word.lower() in legal_medical_vocab:
                score += 0.1
            
            scored_candidates.append({
                'word': word,
                'score': score
            })
        
        # Return highest scoring candidate
        best_candidate = max(scored_candidates, key=lambda x: x['score'])
        return best_candidate['word']
    
    def refine_single_text(self, text: str) -> str:
        """Comprehensively refine a single OCR text result."""
        
        if not text or not text.strip():
            return text
        
        refined_text = text
        corrections = []
        
        # Step 1: Fix common OCR character patterns
        refined_text, char_corrections = self._fix_character_patterns(refined_text)
        corrections.extend(char_corrections)
        
        # Step 2: Fix medical word patterns
        refined_text, word_corrections = self._fix_medical_word_patterns(refined_text)
        corrections.extend(word_corrections)
        
        # Step 3: Medical spell checking
        refined_text, spell_corrections = self._medical_spell_check(refined_text)
        corrections.extend(spell_corrections)
        
        # Step 4: Context-aware corrections
        refined_text, context_corrections = self._context_aware_corrections(refined_text)
        corrections.extend(context_corrections)
        
        # Step 5: Medical term completion
        refined_text, completion_corrections = self._complete_medical_terms(refined_text)
        corrections.extend(completion_corrections)
        
        # Step 6: Final cleanup
        refined_text = self._final_cleanup(refined_text)
        
        logger.info(f"Text refinement completed: {len(corrections)} corrections made")
        
        return refined_text
    
    def _fix_character_patterns(self, text: str) -> Tuple[str, List[str]]:
        """Fix common OCR character recognition errors."""
        corrections = []
        refined_text = text
        
        # Fix common character confusions in medical context
        char_fixes = {
            # Common OCR errors in medical text
            r'(\d+)\s*rng\b': r'\1 mg',  # milligram
            r'(\d+)\s*rnl\b': r'\1 ml',  # milliliter
            r'(\d+)\s*kq\b': r'\1 kg',   # kilogram
            r'\bpatienf\b': 'patient',
            r'\brnedical\b': 'medical',
            r'\bdiaqnosis\b': 'diagnosis',
            r'\btreatrnent\b': 'treatment',
            r'\brnedication\b': 'medication',
            r'\bexarnination\b': 'examination',
            r'\bhistorv\b': 'history',
            r'\bprocedure\b': 'procedure',
            r'\bcervicai\b': 'cervical',
            r'\blurnbar\b': 'lumbar',
            r'\bthoracic\b': 'thoracic',
        }
        
        for pattern, replacement in char_fixes.items():
            if re.search(pattern, refined_text, re.IGNORECASE):
                old_text = refined_text
                refined_text = re.sub(pattern, replacement, refined_text, flags=re.IGNORECASE)
                if refined_text != old_text:
                    corrections.append(f"Character pattern: {pattern} → {replacement}")
        
        return refined_text, corrections
    
    def _fix_medical_word_patterns(self, text: str) -> Tuple[str, List[str]]:
        """Fix known medical word OCR error patterns including legal medical terms."""
        corrections = []
        refined_text = text
        
        # Apply standard medical word patterns
        for pattern, replacement in self.word_patterns.items():
            if re.search(pattern, refined_text, re.IGNORECASE):
                old_text = refined_text
                refined_text = re.sub(pattern, replacement, refined_text, flags=re.IGNORECASE)
                if refined_text != old_text:
                    corrections.append(f"Medical pattern: {pattern} → {replacement}")
        
        # Apply legal medical word patterns
        for pattern, replacement in self.legal_medical_corrections.items():
            if re.search(pattern, refined_text, re.IGNORECASE):
                old_text = refined_text
                refined_text = re.sub(pattern, replacement, refined_text, flags=re.IGNORECASE)
                if refined_text != old_text:
                    corrections.append(f"Legal medical pattern: {pattern} → {replacement}")
        
        return refined_text, corrections
    
    def _medical_spell_check(self, text: str) -> Tuple[str, List[str]]:
        """Perform medical dictionary-based spell checking."""
        corrections = []
        words = text.split()
        corrected_words = []
        
        for word in words:
            # Clean word for checking
            clean_word = re.sub(r'[^\w]', '', word).lower()
            
            if len(clean_word) < 3:  # Skip very short words
                corrected_words.append(word)
                continue
            
            # Check if word is in medical dictionary
            if clean_word in self.medical_dict:
                corrected_words.append(word)
                continue
            
            # Find closest medical term
            closest_match = self._find_closest_medical_term(clean_word)
            
            if closest_match and self._should_correct_word(clean_word, closest_match):
                # Preserve original case and punctuation
                corrected_word = self._preserve_word_format(word, closest_match)
                corrected_words.append(corrected_word)
                corrections.append(f"Spell check: {word} → {corrected_word}")
            else:
                corrected_words.append(word)
        
        refined_text = ' '.join(corrected_words)
        return refined_text, corrections
    
    def _find_closest_medical_term(self, word: str) -> Optional[str]:
        """Find the closest matching medical term."""
        if word in self._similarity_cache:
            return self._similarity_cache[word]
        
        # Find closest matches using difflib
        close_matches = difflib.get_close_matches(
            word, self.medical_dict, n=3, cutoff=0.6
        )
        
        if close_matches:
            best_match = close_matches[0]
            self._similarity_cache[word] = best_match
            return best_match
        
        self._similarity_cache[word] = None
        return None
    
    def _should_correct_word(self, original: str, suggested: str) -> bool:
        """Determine if a word should be corrected based on similarity and context."""
        
        # Don't correct if words are too different
        similarity = difflib.SequenceMatcher(None, original, suggested).ratio()
        if similarity < 0.7:
            return False
        
        # Don't correct proper nouns (likely patient names)
        if original[0].isupper() and suggested[0].islower():
            return False
        
        # Don't correct numbers or codes
        if any(char.isdigit() for char in original):
            return False
        
        return True
    
    def _preserve_word_format(self, original: str, corrected: str) -> str:
        """Preserve the case and punctuation of the original word."""
        
        # Extract leading/trailing punctuation
        leading_punct = re.match(r'^[^\w]*', original).group()
        trailing_punct = re.search(r'[^\w]*$', original).group()
        
        # Get the core word
        core_original = re.sub(r'[^\w]', '', original)
        
        # Apply case pattern from original to corrected
        if core_original.isupper():
            corrected_core = corrected.upper()
        elif core_original.istitle():
            corrected_core = corrected.title()
        elif core_original.islower():
            corrected_core = corrected.lower()
        else:
            # Mixed case - try to preserve pattern
            corrected_core = corrected.lower()
            for i, char in enumerate(core_original):
                if i < len(corrected_core) and char.isupper():
                    corrected_core = corrected_core[:i] + corrected_core[i].upper() + corrected_core[i+1:]
        
        return leading_punct + corrected_core + trailing_punct
    
    def _context_aware_corrections(self, text: str) -> Tuple[str, List[str]]:
        """Apply context-aware corrections based on surrounding text."""
        corrections = []
        refined_text = text
        
        # Medical context patterns
        context_patterns = [
            # Medication dosages
            (r'(\d+)\s*(?:rng|rnq|mq)\b', r'\1 mg', 'dosage units'),
            (r'(\d+)\s*(?:rnl|ml)\b', r'\1 ml', 'volume units'),
            
            # Vital signs context
            (r'(?:BP|Blood Pressure)[:\s]*(\d+)[/\\](\d+)', r'BP: \1/\2', 'blood pressure'),
            (r'(?:HR|Heart Rate)[:\s]*(\d+)', r'HR: \1', 'heart rate'),
            (r'(?:Temp|Temperature)[:\s]*(\d+(?:\.\d+)?)', r'Temp: \1', 'temperature'),
            
            # Pain scale context
            (r'(?:Pain|pain)[:\s]*(\d+)[/\\]10', r'Pain: \1/10', 'pain scale'),
            (r'(?:Pain|pain)[:\s]*(\d+)[/\\](\d+)', r'Pain: \1/\2', 'pain scale'),
            
            # Date patterns
            (r'(?:DOI|Date of Injury)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', r'DOI: \1', 'injury date'),
        ]
        
        for pattern, replacement, context in context_patterns:
            if re.search(pattern, refined_text, re.IGNORECASE):
                old_text = refined_text
                refined_text = re.sub(pattern, replacement, refined_text, flags=re.IGNORECASE)
                if refined_text != old_text:
                    corrections.append(f"Context correction ({context})")
        
        return refined_text, corrections
    
    def _complete_medical_terms(self, text: str) -> Tuple[str, List[str]]:
        """Complete partial medical terms based on context."""
        corrections = []
        refined_text = text
        
        # Common partial medical terms and their completions
        partial_completions = {
            r'\bfractu\b': 'fracture',
            r'\blacerat\b': 'laceration',
            r'\bcontus\b': 'contusion',
            r'\bdiagno\b': 'diagnosis',
            r'\btreatme\b': 'treatment',
            r'\bmedicat\b': 'medication',
            r'\bprescrip\b': 'prescription',
            r'\bexaminat\b': 'examination',
            r'\bconsultat\b': 'consultation',
            r'\bevaluat\b': 'evaluation',
            r'\bphysical therap\b': 'physical therapy',
            r'\brehabilit\b': 'rehabilitation',
        }
        
        for pattern, completion in partial_completions.items():
            if re.search(pattern, refined_text, re.IGNORECASE):
                old_text = refined_text
                refined_text = re.sub(pattern, completion, refined_text, flags=re.IGNORECASE)
                if refined_text != old_text:
                    corrections.append(f"Term completion: {pattern} → {completion}")
        
        return refined_text, corrections
    
    def _final_cleanup(self, text: str) -> str:
        """Perform final text cleanup and formatting."""
        
        # Fix spacing issues
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single
        text = re.sub(r'\n+', '\n', text)  # Multiple newlines to single
        
        # Fix punctuation spacing
        text = re.sub(r'\s+([,.;:!?])', r'\1', text)  # Remove space before punctuation
        text = re.sub(r'([,.;:!?])([^\s])', r'\1 \2', text)  # Add space after punctuation
        
        # Fix number formatting
        text = re.sub(r'(\d+)\s*([mg|ml|kg|lbs])\b', r'\1 \2', text)  # Proper unit spacing
        
        # Fix medical abbreviation formatting
        text = re.sub(r'\b([A-Z]{2,})\s*:', r'\1:', text)  # Remove space before colon in abbreviations
        
        return text.strip()
    
    def analyze_text_quality(self, original: str, refined: str) -> Dict[str, Any]:
        """Analyze the quality improvement from refinement."""
        
        # Count medical terms
        original_medical_terms = sum(1 for word in original.lower().split() if word in self.medical_dict)
        refined_medical_terms = sum(1 for word in refined.lower().split() if word in self.medical_dict)
        
        # Count injury terms
        original_injury_terms = sum(1 for word in original.lower().split() if word in ALL_INJURY_TERMS)
        refined_injury_terms = sum(1 for word in refined.lower().split() if word in ALL_INJURY_TERMS)
        
        # Count legal medical terms
        legal_medical_vocab = get_legal_medical_vocabulary()
        original_legal_terms = sum(1 for word in original.lower().split() if word in legal_medical_vocab)
        refined_legal_terms = sum(1 for word in refined.lower().split() if word in legal_medical_vocab)
        
        # Calculate improvements
        medical_term_improvement = refined_medical_terms - original_medical_terms
        injury_term_improvement = refined_injury_terms - original_injury_terms
        legal_term_improvement = refined_legal_terms - original_legal_terms
        character_changes = len(refined) - len(original)
        word_changes = len(refined.split()) - len(original.split())
        
        # Calculate comprehensive quality improvement
        total_term_improvement = medical_term_improvement + injury_term_improvement + legal_term_improvement
        quality_improvement_score = total_term_improvement / max(len(original.split()), 1)
        
        return {
            'original_length': len(original),
            'refined_length': len(refined),
            'character_changes': character_changes,
            'word_changes': word_changes,
            'medical_term_improvement': medical_term_improvement,
            'injury_term_improvement': injury_term_improvement,
            'legal_term_improvement': legal_term_improvement,
            'original_medical_terms': original_medical_terms,
            'refined_medical_terms': refined_medical_terms,
            'original_legal_terms': original_legal_terms,
            'refined_legal_terms': refined_legal_terms,
            'quality_improvement_score': quality_improvement_score,
            'legal_medical_relevance': calculate_legal_medical_relevance(refined)
        }

# Global instance
medical_text_refiner = MedicalTextRefiner()

def refine_medical_ocr_text(text: str) -> str:
    """Main function to refine medical OCR text."""
    return medical_text_refiner.refine_single_text(text)

def refine_multiple_medical_ocr_results(ocr_results: List[Dict[str, Any]]) -> str:
    """Main function to fuse and refine multiple OCR results."""
    return medical_text_refiner.refine_multiple_ocr_results(ocr_results)
