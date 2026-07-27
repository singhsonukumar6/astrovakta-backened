from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import re

router = APIRouter()

# ── Pythagorean letter-number mapping ──────────────────────────────────────────
PYTHAGOREAN = {
    'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5,
    'F': 6, 'G': 7, 'H': 8, 'I': 9,
    'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5,
    'O': 6, 'P': 7, 'Q': 8, 'R': 9,
    'S': 1, 'T': 2, 'U': 3, 'V': 4, 'W': 5,
    'X': 6, 'Y': 7, 'Z': 8,
}

# ── Chaldean letter-number mapping ─────────────────────────────────────────────
CHALDEAN = {
    'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5,
    'F': 8, 'G': 3, 'H': 5, 'I': 1,
    'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5,
    'O': 7, 'P': 8, 'Q': 1, 'R': 2,
    'S': 3, 'T': 4, 'U': 6, 'V': 6, 'W': 6,
    'X': 5, 'Y': 1, 'Z': 7,
}

MASTER_NUMBERS = {11, 22, 33}

# ── Number interpretations ─────────────────────────────────────────────────────
PYTHAGOREAN_INTERPRETATIONS = {
    1: "The Leader – Independent, ambitious, pioneering. Strong willpower and originality.",
    2: "The Peacemaker – Cooperative, diplomatic, sensitive. Natural mediator and partner.",
    3: "The Communicator – Creative, expressive, social. Artistic talent and optimism.",
    4: "The Builder – Practical, disciplined, stable. Strong foundation and work ethic.",
    5: "The Adventurer – Versatile, freedom-loving, dynamic. Curious and adaptable.",
    6: "The Nurturer – Responsible, loving, harmonious. Family-oriented and caring.",
    7: "The Seeker – Analytical, introspective, spiritual. Deep thinker and researcher.",
    8: "The Achiever – Authoritative, successful, material-focused. Strong business sense.",
    9: "The Humanitarian – Compassionate, idealistic, generous. Broad-minded and artistic.",
    11: "The Master Intuitive – Spiritual insight, inspiration, heightened sensitivity. A master number of illumination.",
    22: "The Master Builder – Visionary power, practical idealism. A master number of manifesting dreams into reality.",
    33: "The Master Teacher – Compassion, healing, spiritual teaching. A master number of selfless service.",
}

COMPATIBILITY_MATRIX = {
    (1, 1): {"percentage": 60, "dynamics": "Two strong wills may clash. Powerful when aligned on shared goals."},
    (1, 2): {"percentage": 85, "dynamics": "Leader and Peacemaker complement each other beautifully."},
    (1, 3): {"percentage": 75, "dynamics": "Dynamic and fun. Both are energetic but may compete for attention."},
    (1, 4): {"percentage": 70, "dynamics": "Strong foundation. The Builder grounds the Leader's ambition."},
    (1, 5): {"percentage": 80, "dynamics": "Exciting and adventurous. Both love change and new experiences."},
    (1, 6): {"percentage": 65, "dynamics": "The Nurturer may feel overshadowed by the Leader's drive."},
    (1, 7): {"percentage": 55, "dynamics": "The Seeker's introspection may frustrate the action-oriented Leader."},
    (1, 8): {"percentage": 90, "dynamics": "Power couple! Both driven toward success and achievement."},
    (1, 9): {"percentage": 70, "dynamics": "The Leader's focus on self may clash with the Humanitarian's universal vision."},
    (2, 2): {"percentage": 70, "dynamics": "Deeply sensitive bond. May become overly dependent on each other."},
    (2, 3): {"percentage": 80, "dynamics": "Warm and expressive relationship. Both are social and affectionate."},
    (2, 4): {"percentage": 85, "dynamics": "Stable and nurturing. Both value security and home life."},
    (2, 5): {"percentage": 60, "dynamics": "The Adventurer's restlessness may unsettle the Peacemaker."},
    (2, 6): {"percentage": 90, "dynamics": "Natural harmony. Both value love, family, and emotional connection."},
    (2, 7): {"percentage": 65, "dynamics": "The Seeker's need for solitude may hurt the sensitive Peacemaker."},
    (2, 8): {"percentage": 75, "dynamics": "The Achiever's ambition provides security the Peacemaker craves."},
    (2, 9): {"percentage": 80, "dynamics": "Compassionate connection. Both serve others selflessly."},
    (3, 3): {"percentage": 75, "dynamics": "Creative explosion! May lack discipline without grounding energy."},
    (3, 4): {"percentage": 60, "dynamics": "The Builder's rigidity may stifle the Communicator's free spirit."},
    (3, 5): {"percentage": 85, "dynamics": "Fun, adventurous, and expressive. Never a dull moment."},
    (3, 6): {"percentage": 75, "dynamics": "Warm and loving. The Communicator brings joy to the Nurturer's home."},
    (3, 7): {"percentage": 55, "dynamics": "The Seeker may find the Communicator too superficial."},
    (3, 8): {"percentage": 70, "dynamics": "The Achiever can help channel the Communicator's ideas into profit."},
    (3, 9): {"percentage": 80, "dynamics": "Artistic and humanitarian. Both inspire and uplift others."},
    (4, 4): {"percentage": 65, "dynamics": "Extremely stable but may become rigid. Both need to loosen up."},
    (4, 5): {"percentage": 55, "dynamics": "The Adventurer's chaos disrupts the Builder's ordered world."},
    (4, 6): {"percentage": 85, "dynamics": "Domestic bliss. Both create a stable, loving home environment."},
    (4, 7): {"percentage": 70, "dynamics": "Respectful and intellectual. Both value depth and substance."},
    (4, 8): {"percentage": 90, "dynamics": "Business powerhouse. Both are driven toward material success."},
    (4, 9): {"percentage": 65, "dynamics": "The Humanitarian's idealism may seem impractical to the Builder."},
    (5, 5): {"percentage": 70, "dynamics": "Electrifying but unstable. Both crave freedom which may prevent settling down."},
    (5, 6): {"percentage": 60, "dynamics": "The Adventurer's wanderlust clashes with the Nurturer's need for home."},
    (5, 7): {"percentage": 75, "dynamics": "Unusual but intriguing. Both value freedom in different ways."},
    (5, 8): {"percentage": 80, "dynamics": "The Achiever's resources fuel the Adventurer's experiences."},
    (5, 9): {"percentage": 85, "dynamics": "Worldly and adventurous. Both love travel, culture, and humanity."},
    (6, 6): {"percentage": 70, "dynamics": "Deeply loving but may create a sheltered, insular world together."},
    (6, 7): {"percentage": 65, "dynamics": "The Seeker's detachment may wound the Nurturer's emotional nature."},
    (6, 8): {"percentage": 80, "dynamics": "Prosperous and harmonious. The Achiever provides what the Nurturer needs."},
    (6, 9): {"percentage": 85, "dynamics": "Compassionate union. Both give selflessly to others."},
    (7, 7): {"percentage": 60, "dynamics": "Spiritually deep but may lack practical connection. Both retreat inward."},
    (7, 8): {"percentage": 65, "dynamics": "The Seeker's spiritual focus may clash with the Achiever's materialism."},
    (7, 9): {"percentage": 75, "dynamics": "Philosophical and spiritual bond. Both seek higher truth."},
    (8, 8): {"percentage": 75, "dynamics": "Powerful but competitive. Both are ambitious which may create rivalry."},
    (8, 9): {"percentage": 70, "dynamics": "The Achiever's materialism may conflict with the Humanitarian's ideals."},
    (9, 9): {"percentage": 70, "dynamics": "Deeply humanitarian. May neglect practical matters in pursuit of ideals."},
}

BUSINESS_SUCCESS_FACTORS = {
    1: {"traits": "Innovation, leadership, entrepreneurship", "best_industries": ["Startups", "Technology", "Consulting", "Sports"], "lucky_colors": ["Gold", "Red"], "lucky_days": ["Sunday", "Monday"]},
    2: {"traits": "Partnership, diplomacy, cooperation", "best_industries": ["Interior Design", "Diplomacy", "Art", "Counseling"], "lucky_colors": ["White", "Silver"], "lucky_days": ["Monday", "Friday"]},
    3: {"traits": "Creativity, communication, entertainment", "best_industries": ["Media", "Entertainment", "Writing", "Marketing"], "lucky_colors": ["Yellow", "Orange"], "lucky_days": ["Thursday", "Friday"]},
    4: {"traits": "Organization, reliability, construction", "best_industries": ["Real Estate", "Manufacturing", "Banking", "Agriculture"], "lucky_colors": ["Blue", "Green"], "lucky_days": ["Saturday", "Sunday"]},
    5: {"traits": "Adaptability, travel, communication", "best_industries": ["Tourism", "Transport", "Communications", "Sales"], "lucky_colors": ["Green", "Light Blue"], "lucky_days": ["Wednesday", "Friday"]},
    6: {"traits": "Service, beauty, nurturing", "best_industries": ["Healthcare", "Hospitality", "Beauty", "Education"], "lucky_colors": ["Pink", "Light Blue"], "lucky_days": ["Friday", "Thursday"]},
    7: {"traits": "Analysis, research, spirituality", "best_industries": ["Research", "Spirituality", "Technology", "Pharmaceuticals"], "lucky_colors": ["White", "Grey"], "lucky_days": ["Monday", "Saturday"]},
    8: {"traits": "Authority, finance, power", "best_industries": ["Finance", "Mining", "Politics", "Law"], "lucky_colors": ["Purple", "Dark Blue"], "lucky_days": ["Friday", "Saturday"]},
    9: {"traits": "Humanitarianism, art, compassion", "best_industries": ["Charities", "Art", "Social Work", "International Trade"], "lucky_colors": ["Red", "Orange"], "lucky_days": ["Tuesday", "Friday"]},
    11: {"traits": "Inspiration, intuition, spirituality", "best_industries": ["Spiritual Healing", "Art", "Psychology", "Innovation"], "lucky_colors": ["Silver", "White"], "lucky_days": ["Tuesday", "Wednesday"]},
    22: {"traits": "Master building, large-scale projects", "best_industries": ["Architecture", "Government", "Philanthropy", "Global Business"], "lucky_colors": ["Purple", "Gold"], "lucky_days": ["Saturday", "Sunday"]},
    33: {"traits": "Teaching, healing, compassion", "best_industries": ["Education", "Healthcare", "Spiritual Teaching", "Non-Profit"], "lucky_colors": ["Pink", "White"], "lucky_days": ["Thursday", "Friday"]},
}

# ── Baby names database (100+ names) ──────────────────────────────────────────
BABY_NAMES = {
    1: [
        {"name": "Aarav", "meaning": "Peaceful; rays of light", "gender": "male"},
        {"name": "Aditya", "meaning": "Sun; descendant of Aditi", "gender": "male"},
        {"name": "Aiden", "meaning": "Little fire; fiery", "gender": "male"},
        {"name": "Arjun", "meaning": "Bright; shining; white", "gender": "male"},
        {"name": "Akira", "meaning": "Bright; clear; ideal", "gender": "unisex"},
        {"name": "Amara", "meaning": "Immortal; eternal", "gender": "female"},
        {"name": "Anaya", "meaning": "Caring; compassionate", "gender": "female"},
        {"name": "Avani", "meaning": "The earth", "gender": "female"},
        {"name": "Ahana", "meaning": "First ray of sunlight", "gender": "female"},
        {"name": "Alice", "meaning": "Noble; of a noble kind", "gender": "female"},
    ],
    2: [
        {"name": "Ananya", "meaning": "Unique; matchless", "gender": "female"},
        {"name": "Bhavana", "meaning": "Feeling; emotion", "gender": "female"},
        {"name": "Dhara", "meaning": "Flow; the earth", "gender": "female"},
        {"name": "Eva", "meaning": "Life; living one", "gender": "female"},
        {"name": "Ethan", "meaning": "Strong; firm", "gender": "male"},
        {"name": "Diya", "meaning": "Lamp; light", "gender": "female"},
        {"name": "Hana", "meaning": "Flower; happiness", "gender": "female"},
        {"name": "Ira", "meaning": "Earth; goddess Saraswati", "gender": "female"},
        {"name": "Kabir", "meaning": "Great; noble", "gender": "male"},
        {"name": "Neha", "meaning": "Love; affection", "gender": "female"},
    ],
    3: [
        {"name": "Aarohi", "meaning": "A musical tune; ascending", "gender": "female"},
        {"name": "Caleb", "meaning": "Whole hearted; faithful", "gender": "male"},
        {"name": "Dhruv", "meaning": "Pole star; constant", "gender": "male"},
        {"name": "Esha", "meaning": "Desire; wish", "gender": "female"},
        {"name": "Gia", "meaning": "God is gracious", "gender": "female"},
        {"name": "Krish", "meaning": "Black; dark; Lord Krishna", "gender": "male"},
        {"name": "Liam", "meaning": "Determined protector", "gender": "male"},
        {"name": "Meera", "meaning": "Devotee of Lord Krishna", "gender": "female"},
        {"name": "Riya", "meaning": "Singer; graceful", "gender": "female"},
        {"name": "Zara", "meaning": "Blooming flower; princess", "gender": "female"},
    ],
    4: [
        {"name": "Bodhi", "meaning": "Awakening; enlightenment", "gender": "male"},
        {"name": "Cian", "meaning": "Ancient; enduring", "gender": "male"},
        {"name": "Dev", "meaning": "God; divine one", "gender": "male"},
        {"name": "Emily", "meaning": "Industrious; striving", "gender": "female"},
        {"name": "Kira", "meaning": "Sun; ray of light", "gender": "female"},
        {"name": "Mira", "meaning": "Ocean; profound", "gender": "female"},
        {"name": "Nikhil", "meaning": "Complete; whole", "gender": "male"},
        {"name": "Sara", "meaning": "Princess; pure", "gender": "female"},
        {"name": "Vihaan", "meaning": "Dawn; new beginning", "gender": "male"},
        {"name": "Yash", "meaning": "Glory; fame", "gender": "male"},
    ],
    5: [
        {"name": "Aaliyah", "meaning": "Exalted; sublime", "gender": "female"},
        {"name": "Arnav", "meaning": "Ocean; vast", "gender": "male"},
        {"name": "Dhwanil", "meaning": "Sound; vibration", "gender": "male"},
        {"name": "Isha", "meaning": "Goddess; ruler", "gender": "female"},
        {"name": "Kai", "meaning": "Sea; open water", "gender": "unisex"},
        {"name": "Maya", "meaning": "Illusion; magic", "gender": "female"},
        {"name": "Neil", "meaning": "Champion; cloud", "gender": "male"},
        {"name": "Rhea", "meaning": "Flowing; ease", "gender": "female"},
        {"name": "Vivaan", "meaning": "First rays of the sun", "gender": "male"},
        {"name": "Zoya", "meaning": "Alive; loving; caring", "gender": "female"},
    ],
    6: [
        {"name": "Aaradhya", "meaning": "Worthy of worship", "gender": "female"},
        {"name": "Anvi", "meaning": "One who deserves love", "gender": "female"},
        {"name": "Deepa", "meaning": "Lamp; light", "gender": "female"},
        {"name": "Kavya", "meaning": "Poetry; wise", "gender": "female"},
        {"name": "Liam", "meaning": "Determined protector", "gender": "male"},
        {"name": "Nisha", "meaning": "Night; eternal", "gender": "female"},
        {"name": "Priya", "meaning": "Beloved; dear one", "gender": "female"},
        {"name": "Rohan", "meaning": "Ascending; fragrant", "gender": "male"},
        {"name": "Siya", "meaning": "Goddess Sita; white", "gender": "female"},
        {"name": "Veda", "meaning": "Sacred knowledge", "gender": "female"},
    ],
    7: [
        {"name": "Aarav", "meaning": "Peaceful; wise", "gender": "male"},
        {"name": "Aanya", "meaning": "Grace; limitless", "gender": "female"},
        {"name": "Guru", "meaning": "Teacher; master", "gender": "male"},
        {"name": "Kiara", "meaning": "Dark-haired; bright", "gender": "female"},
        {"name": "Neel", "meaning": "Blue; sapphire", "gender": "male"},
        {"name": "Ojas", "meaning": "Vigor; vitality; essence", "gender": "male"},
        {"name": "Rishabh", "meaning": "Morality; excellent", "gender": "male"},
        {"name": "Saanvi", "meaning": "Goddess Lakshmi", "gender": "female"},
        {"name": "Trish", "meaning": "Noble; strong", "gender": "female"},
        {"name": "Ved", "meaning": "Sacred knowledge; wise", "gender": "male"},
    ],
    8: [
        {"name": "Aarush", "meaning": "First ray of the sun", "gender": "male"},
        {"name": "Akanksha", "meaning": "Desire; aspiration", "gender": "female"},
        {"name": "Darsh", "meaning": "Sight; vision", "gender": "male"},
        {"name": "Harsha", "meaning": "Happiness; joy", "gender": "male"},
        {"name": "Ishika", "meaning": "Arrow; deer", "gender": "female"},
        {"name": "Kashvi", "meaning": "Shining; bright", "gender": "female"},
        {"name": "Manya", "meaning": "Desired; respected", "gender": "female"},
        {"name": "Ovi", "meaning": "Poetry; divine energy", "gender": "unisex"},
        {"name": "Reyansh", "meaning": "Part of the sun god", "gender": "male"},
        {"name": "Tara", "meaning": "Star; hill", "gender": "female"},
    ],
    9: [
        {"name": "Aarohi", "meaning": "Musical note; ascending", "gender": "female"},
        {"name": "Anshul", "meaning": "Radiant; bright", "gender": "male"},
        {"name": "Chhavi", "meaning": "Reflection; image", "gender": "female"},
        {"name": "Dhriti", "meaning": "Courage; patience", "gender": "female"},
        {"name": "Kriti", "meaning": "Work of art", "gender": "female"},
        {"name": "Naman", "meaning": "Salutation; respect", "gender": "male"},
        {"name": "Prisha", "meaning": "Beloved; God's gift", "gender": "female"},
        {"name": "Rudra", "meaning": "Fierce; Lord Shiva", "gender": "male"},
        {"name": "Samar", "meaning": "War; battle", "gender": "male"},
        {"name": "Tanvi", "meaning": "Delicate; slender", "gender": "female"},
    ],
    11: [
        {"name": "Aadhya", "meaning": "The first; beginning", "gender": "female"},
        {"name": "Arin", "meaning": "Mountain of strength", "gender": "unisex"},
        {"name": "Drishti", "meaning": "Vision; sight", "gender": "female"},
        {"name": "Ekiel", "meaning": "God will strengthen", "gender": "male"},
        {"name": "Kiaan", "meaning": "Ancient; king", "gender": "male"},
        {"name": "Myra", "meaning": "Beloved; admirable", "gender": "female"},
        {"name": "Nirvi", "meaning": "Peaceful; blissful", "gender": "female"},
        {"name": "Rayan", "meaning": "Heavenly fragrance", "gender": "male"},
        {"name": "Siddhi", "meaning": "Perfection; achievement", "gender": "female"},
        {"name": "Vedaant", "meaning": "Ultimate knowledge", "gender": "male"},
    ],
    22: [
        {"name": "Aarush", "meaning": "Bright; first ray of sun", "gender": "male"},
        {"name": "Dhritiman", "meaning": "Patient and steadfast", "gender": "male"},
        {"name": "Himanshi", "meaning": "Part of snow; moon", "gender": "female"},
        {"name": "Kabir", "meaning": "The great one", "gender": "male"},
        {"name": "Nishka", "meaning": "Pure; honest", "gender": "female"},
        {"name": "Pranav", "meaning": "Sacred syllable Om", "gender": "male"},
        {"name": "Ritambhara", "meaning": "Bearer of cosmic truth", "gender": "female"},
        {"name": "Shlok", "meaning": "Verse; hymn", "gender": "male"},
        {"name": "Tejasvi", "meaning": "Brilliant; lustrous", "gender": "unisex"},
        {"name": "Vedant", "meaning": "End of the Vedas; wisdom", "gender": "male"},
    ],
    33: [
        {"name": "Aashi", "meaning": "Hope; blessing", "gender": "female"},
        {"name": "Bodhi", "meaning": "Enlightenment; awakening", "gender": "male"},
        {"name": "Daya", "meaning": "Compassion; mercy", "gender": "female"},
        {"name": "Gopal", "meaning": "One who nourishes all", "gender": "male"},
        {"name": "Kripa", "meaning": "Grace; compassion", "gender": "female"},
        {"name": "Lakshya", "meaning": "Aim; goal; destination", "gender": "male"},
        {"name": "Meenakshi", "meaning": "Fish-eyed; Goddess Parvati", "gender": "female"},
        {"name": "Prema", "meaning": "Divine love", "gender": "female"},
        {"name": "Shanti", "meaning": "Peace; tranquility", "gender": "female"},
        {"name": "Vishwa", "meaning": "Universe; world", "gender": "male"},
    ],
}


# ── Helper functions ───────────────────────────────────────────────────────────

def _clean_name(name: str) -> str:
    return re.sub(r'[^a-zA-Z]', '', name).upper()


def _sum_digits(n: int) -> int:
    while n > 9 and n not in MASTER_NUMBERS:
        n = sum(int(d) for d in str(n))
    return n


def calculate_name_number(name: str, system: str = "pythagorean") -> int:
    mapping = PYTHAGOREAN if system == "pythagorean" else CHALDEAN
    cleaned = _clean_name(name)
    total = sum(mapping[ch] for ch in cleaned if ch in mapping)
    return _sum_digits(total)


def _get_compatibility(a: int, b: int) -> dict:
    key = (min(a, b), max(a, b))
    if key in COMPATIBILITY_MATRIX:
        return COMPATIBILITY_MATRIX[key]
    a_single = a if a < 10 else a % 9 or 9
    b_single = b if b < 10 else b % 9 or 9
    key = (min(a_single, b_single), max(a_single, b_single))
    return COMPATIBILITY_MATRIX.get(key, {"percentage": 60, "dynamics": "Unique pairing with untapped potential."})


def _life_path_from_dob(dob: str) -> Optional[int]:
    digits = re.sub(r'[^0-9]', '', dob)
    if not digits:
        return None
    return _sum_digits(sum(int(d) for d in digits))


def _get_lucky_elements(num: int) -> dict:
    factors = BUSINESS_SUCCESS_FACTORS.get(num, BUSINESS_SUCCESS_FACTORS[num % 9 or 9])
    return factors


# ── Request / Response models ─────────────────────────────────────────────────

class NameRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Full name to analyse")


class NameNumberResponse(BaseModel):
    name: str
    name_number: int
    system: str
    interpretation: str
    compatible_numbers: list[int]
    letter_breakdown: dict[str, int]


class NameCompatRequest(BaseModel):
    name1: str = Field(..., min_length=1)
    name2: str = Field(..., min_length=1)


class NameCompatResponse(BaseModel):
    name1: str
    name2: str
    name1_number: int
    name2_number: int
    compatibility_percentage: int
    dynamics: str
    advice: str


class BusinessNameRequest(BaseModel):
    name: str = Field(..., min_length=1)
    dateOfBirth: Optional[str] = None


class BusinessNameResponse(BaseModel):
    business_name: str
    business_number: int
    interpretation: str
    owner_life_path: Optional[int]
    life_path_compatibility: Optional[int]
    success_factors: dict
    lucky_elements: dict
    recommendation: str


class BabyNameSuggestionRequest(BaseModel):
    targetNumber: int = Field(..., ge=1, le=33)
    gender: Optional[str] = None
    startingLetter: Optional[str] = None


class BabyNameItem(BaseModel):
    name: str
    meaning: str
    gender: str
    number: int


class BabyNameResponse(BaseModel):
    target_number: int
    names: list[BabyNameItem]
    total_count: int


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/api/numerology/name-number", response_model=NameNumberResponse)
async def calculate_name_vibration(req: NameRequest):
    cleaned = _clean_name(req.name)
    if not cleaned:
        raise HTTPException(status_code=400, detail="Name must contain at least one letter.")

    number = calculate_name_number(req.name, "pythagorean")
    interpretation = PYTHAGOREAN_INTERPRETATIONS.get(number, "A unique and complex vibration.")

    # Compatibles: numbers whose root sums harmonise
    root = number if number < 10 else number % 9 or 9
    compatible = [
        n for n in range(1, 10)
        if n == root or (n + root) % 9 in (0, 3, 5, 6)
    ]
    for mn in MASTER_NUMBERS:
        if mn in (number, 11, 22, 33):
            compatible.append(mn)
    compatible = sorted(set(compatible))

    breakdown = {}
    for ch in cleaned:
        breakdown[ch] = PYTHAGOREAN.get(ch, 0)

    return NameNumberResponse(
        name=req.name,
        name_number=number,
        system="Pythagorean",
        interpretation=interpretation,
        compatible_numbers=compatible,
        letter_breakdown=breakdown,
    )


@router.post("/api/numerology/name-compatibility", response_model=NameCompatResponse)
async def name_compatibility(req: NameCompatRequest):
    for n in (req.name1, req.name2):
        if not _clean_name(n):
            raise HTTPException(status_code=400, detail=f"Name must contain at least one letter: {n}")

    n1 = calculate_name_number(req.name1, "pythagorean")
    n2 = calculate_name_number(req.name2, "pythagorean")

    comp = _get_compatibility(n1, n2)

    advice_parts = []
    pct = comp["percentage"]
    if pct >= 85:
        advice_parts.append("This is a highly harmonious pairing. Nurture the natural connection.")
    elif pct >= 70:
        advice_parts.append("Good compatibility with room to grow. Focus on open communication.")
    elif pct >= 60:
        advice_parts.append("Moderate compatibility. Mutual respect and compromise will strengthen the bond.")
    else:
        advice_parts.append("Challenging pairing. Conscious effort and understanding are required for success.")

    if 11 in (n1, n2) or 22 in (n1, n2) or 33 in (n1, n2):
        advice_parts.append("Master numbers present – this relationship carries spiritual significance.")

    return NameCompatResponse(
        name1=req.name1,
        name2=req.name2,
        name1_number=n1,
        name2_number=n2,
        compatibility_percentage=comp["percentage"],
        dynamics=comp["dynamics"],
        advice=" ".join(advice_parts),
    )


@router.post("/api/numerology/business-name", response_model=BusinessNameResponse)
async def business_name_analysis(req: BusinessNameRequest):
    cleaned = _clean_name(req.name)
    if not cleaned:
        raise HTTPException(status_code=400, detail="Business name must contain at least one letter.")

    biz_number = calculate_name_number(req.name, "pythagorean")
    interpretation = PYTHAGOREAN_INTERPRETATIONS.get(biz_number, "A unique business vibration.")
    success = BUSINESS_SUCCESS_FACTORS.get(biz_number, BUSINESS_SUCCESS_FACTORS[biz_number % 9 or 9])

    life_path = None
    lp_compat = None
    if req.dateOfBirth:
        life_path = _life_path_from_dob(req.dateOfBirth)
        if life_path:
            lp_comp = _get_compatibility(biz_number, life_path)
            lp_compat = lp_comp["percentage"]

    lucky = _get_lucky_elements(biz_number)

    rec_parts = [f"Business name '{req.name}' resonates with number {biz_number}."]
    if lp_compat is not None:
        if lp_compat >= 75:
            rec_parts.append(f"Strong alignment ({lp_compat}%) with the owner's Life Path {life_path}. This business is well-suited.")
        elif lp_compat >= 55:
            rec_parts.append(f"Moderate alignment ({lp_compat}%) with the owner's Life Path {life_path}. Consider adjustments for better harmony.")
        else:
            rec_parts.append(f"Low alignment ({lp_compat}%) with the owner's Life Path {life_path}. Renaming or adding a partner with complementary energy is advised.")
    rec_parts.append(f"Best industries: {', '.join(success['best_industries'])}.")

    return BusinessNameResponse(
        business_name=req.name,
        business_number=biz_number,
        interpretation=interpretation,
        owner_life_path=life_path,
        life_path_compatibility=lp_compat,
        success_factors=success,
        lucky_elements=lucky,
        recommendation=" ".join(rec_parts),
    )


@router.post("/api/numerology/baby-name", response_model=BabyNameResponse)
async def baby_name_suggestions(req: BabyNameSuggestionRequest):
    target = req.targetNumber
    candidates = BABY_NAMES.get(target, [])

    filtered = candidates
    if req.gender:
        g = req.gender.lower()
        filtered = [c for c in filtered if c["gender"] == g or c["gender"] == "unisex"]
    if req.startingLetter:
        letter = req.startingLetter.upper()
        filtered = [c for c in filtered if c["name"].upper().startswith(letter)]

    if not filtered:
        filtered = candidates[:]

    names_out = [
        BabyNameItem(
            name=c["name"],
            meaning=c["meaning"],
            gender=c["gender"],
            number=target,
        )
        for c in filtered
    ]

    return BabyNameResponse(
        target_number=target,
        names=names_out,
        total_count=len(names_out),
    )
