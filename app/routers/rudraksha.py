from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import swisseph as swe

from ..utils import to_julian, ZODIAC_SIGNS, SIGN_LORDS

router = APIRouter()


class RudrakshaRecommendRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    nodeMode: Optional[str] = Field("mean", example="mean")


class MukhiIdentificationRequest(BaseModel):
    description: str = Field(..., example="Round shaped rudraksha with 5 lines visible on surface")
    visualFeatures: Optional[str] = Field(None, example="Natural five faces visible, smooth surface")


class WearingMethodRequest(BaseModel):
    mukhiCount: int = Field(..., ge=1, le=14, example=5)
    gender: Optional[str] = Field("male", example="male")


class MantraRequest(BaseModel):
    mukhiCount: int = Field(..., ge=1, le=14, example=5)


class BenefitsRequest(BaseModel):
    mukhiCount: int = Field(..., ge=1, le=14, example=5)


RUDRAKSHA_DATA: Dict[int, Dict[str, Any]] = {
    1: {
        "name": "1-Mukhi Rudraksha",
        "deity": "Lord Shiva",
        "planet": "Sun",
        "rulingGod": "Shiva",
        "description": "The most powerful and rare rudraksha, representing pure consciousness and Lord Shiva himself",
        "benefits": [
            "Brings spiritual enlightenment and liberation (Moksha)",
            "Enhances concentration and meditation",
            "Cures diseases related to heart and mind",
            "Brings supreme knowledge and self-realization",
            "Removes sins and past karma"
        ],
        "color": "Light brown to dark brown",
        "shape": "Round with single line",
        "origin": "Nepal, Java",
        "rarity": "Extremely Rare"
    },
    2: {
        "name": "2-Mukhi Rudraksha",
        "deity": "Ardhanarishvara (Shiva-Parvati)",
        "planet": "Moon",
        "rulingGod": "Shiva and Parvati",
        "description": "Represents the unified form of Lord Shiva and Goddess Parvati, symbolizing unity and harmony",
        "benefits": [
            "Strengthens relationships and marriage",
            "Brings emotional balance and harmony",
            "Cures mental disorders and depression",
            "Enhances love and compassion",
            "Bestows family happiness and unity"
        ],
        "color": "Light brown",
        "shape": "Two natural lines visible",
        "origin": "Nepal, Indonesia",
        "rarity": "Rare"
    },
    3: {
        "name": "3-Mukhi Rudraksha",
        "deity": "Agni (Fire God)",
        "planet": "Mars",
        "rulingGod": "Agni Deva",
        "description": "Represents the fire god Agni, providing purification and courage",
        "benefits": [
            "Burns past sins and karmic debts",
            "Enhances courage and confidence",
            "Cures blood-related disorders",
            "Improves digestive health",
            "Brings purity of mind and body"
        ],
        "color": "Light brown to reddish brown",
        "shape": "Three natural lines visible",
        "origin": "Nepal, India",
        "rarity": "Moderate"
    },
    4: {
        "name": "4-Mukhi Rudraksha",
        "deity": "Brahma",
        "planet": "Mercury",
        "rulingGod": "Lord Brahma",
        "description": "Represents Lord Brahma, the creator, enhancing knowledge and creativity",
        "benefits": [
            "Enhances knowledge and learning",
            "Improves memory and concentration",
            "Bestows creative intelligence",
            "Cures speech disorders",
            "Brings success in education and research"
        ],
        "color": "Brown",
        "shape": "Four natural lines visible",
        "origin": "Nepal, Java",
        "rarity": "Moderate"
    },
    5: {
        "name": "5-Mukhi Rudraksha",
        "deity": "Kalagni Rudra (Shiva)",
        "planet": "Jupiter",
        "rulingGod": "Lord Shiva",
        "description": "Most common and widely worn rudraksha, representing the five forms of Lord Shiva",
        "benefits": [
            "Brings peace of mind and spiritual growth",
            "Enhances wisdom and self-awareness",
            "Cures high blood pressure and stress",
            "Protects from untimely death",
            "Bestows the wearer with health and tranquility"
        ],
        "color": "Light brown to dark brown",
        "shape": "Five natural lines visible",
        "origin": "Nepal, Indonesia, India",
        "rarity": "Common"
    },
    6: {
        "name": "6-Mukhi Rudraksha",
        "deity": "Kartikeya (Murugan)",
        "planet": "Venus",
        "rulingGod": "Lord Kartikeya",
        "description": "Represents Lord Kartikeya, the warrior god, enhancing willpower and determination",
        "benefits": [
            "Enhances willpower and determination",
            "Brings victory over enemies",
            "Improves sexual vitality and reproductive health",
            "Bestows courage and leadership qualities",
            "Cures bone and joint disorders"
        ],
        "color": "Brown",
        "shape": "Six natural lines visible",
        "origin": "Nepal, Indonesia",
        "rarity": "Moderate"
    },
    7: {
        "name": "7-Mukhi Rudraksha",
        "deity": "Mahalakshmi",
        "planet": "Saturn",
        "rulingGod": "Goddess Lakshmi",
        "description": "Represents Goddess Lakshmi, bringing wealth, prosperity and good fortune",
        "benefits": [
            "Attracts wealth and prosperity",
            "Brings good luck and fortune",
            "Cures financial problems and debts",
            "Enhances business success",
            "Bestows luxury and material comforts"
        ],
        "color": "Light brown",
        "shape": "Seven natural lines visible",
        "origin": "Nepal, Java",
        "rarity": "Moderate"
    },
    8: {
        "name": "8-Mukhi Rudraksha",
        "deity": "Ganesha",
        "planet": "Rahu",
        "rulingGod": "Lord Ganesha",
        "description": "Represents Lord Ganesha, the remover of obstacles, bringing success and wisdom",
        "benefits": [
            "Removes obstacles from life path",
            "Brings success in new ventures",
            "Enhances analytical and logical thinking",
            "Cures nervous system disorders",
            "Bestows wisdom and prosperity"
        ],
        "color": "Brown to dark brown",
        "shape": "Eight natural lines visible",
        "origin": "Nepal, Indonesia",
        "rarity": "Moderate"
    },
    9: {
        "name": "9-Mukhi Rudraksha",
        "deity": "Durga (Navadurga)",
        "planet": "Ketu",
        "rulingGod": "Goddess Durga",
        "description": "Represents the nine forms of Goddess Durga, providing divine protection and energy",
        "benefits": [
            "Provides divine protection and security",
            "Enhances physical and mental strength",
            "Cures fear and phobias",
            "Brings energy and vitality",
            "Bestows the blessings of Goddess Durga"
        ],
        "color": "Brown",
        "shape": "Nine natural lines visible",
        "origin": "Nepal",
        "rarity": "Rare"
    },
    10: {
        "name": "10-Mukhi Rudraksha",
        "deity": "Vishnu (Dashavatara)",
        "planet": "All Planets",
        "rulingGod": "Lord Vishnu",
        "description": "Represents the ten incarnations of Lord Vishnu, providing complete protection and peace",
        "benefits": [
            "Provides complete protection from evil forces",
            "Brings peace and harmony in all aspects",
            "Cures black magic and negative energies",
            "Enhances spiritual growth and devotion",
            "Bestows all types of blessings from Lord Vishnu"
        ],
        "color": "Light brown",
        "shape": "Ten natural lines visible",
        "origin": "Nepal, Java",
        "rarity": "Very Rare"
    },
    11: {
        "name": "11-Mukhi Rudraksha",
        "deity": "Eleven Rudras (Shiva forms)",
        "planet": "Jupiter",
        "rulingGod": "Eleven Rudras",
        "description": "Represents the eleven forms of Rudra (Shiva), bringing immense spiritual power",
        "benefits": [
            "Bestows immense spiritual power",
            "Enhances meditation and contemplation",
            "Cures all types of fears and anxieties",
            "Brings success in spiritual practices",
            "Protects from accidents and untoward incidents"
        ],
        "color": "Brown",
        "shape": "Eleven natural lines visible",
        "origin": "Nepal",
        "rarity": "Very Rare"
    },
    12: {
        "name": "12-Mukhi Rudraksha",
        "deity": "Surya (Sun God)",
        "planet": "Sun",
        "rulingGod": "Lord Surya",
        "description": "Represents the twelve forms of Sun God, radiating divine light and energy",
        "benefits": [
            "Enhances leadership and administrative qualities",
            "Brings radiance and charm to personality",
            "Cures eye diseases and skin disorders",
            "Bestows political power and authority",
            "Provides protection from diseases and misfortunes"
        ],
        "color": "Reddish brown",
        "shape": "Twelve natural lines visible",
        "origin": "Nepal",
        "rarity": "Extremely Rare"
    },
    13: {
        "name": "13-Mukhi Rudraksha",
        "deity": "Kamadeva (God of Love)",
        "planet": "Venus",
        "rulingGod": "Lord Kamadeva",
        "description": "Represents Lord Kamadeva, bringing attraction, charm and success in love matters",
        "benefits": [
            "Enhances attraction and charm",
            "Brings success in love and marriage",
            "Bestows all worldly pleasures and comforts",
            "Enhances artistic and creative abilities",
            "Cures impotency and reproductive disorders"
        ],
        "color": "Brown",
        "shape": "Thirteen natural lines visible",
        "origin": "Nepal",
        "rarity": "Extremely Rare"
    },
    14: {
        "name": "14-Mukhi Rudraksha",
        "deity": "Hanuman",
        "planet": "Saturn",
        "rulingGod": "Lord Hanuman",
        "description": "Represents Lord Hanuman, providing immense courage, strength and protection",
        "benefits": [
            "Bestows immense courage and strength",
            "Protects from all types of dangers and evils",
            "Cures diseases related to Saturn",
            "Brings success in court cases and legal matters",
            "Enhances spiritual and physical strength"
        ],
        "color": "Dark brown",
        "shape": "Fourteen natural lines visible",
        "origin": "Nepal",
        "rarity": "Extremely Rare"
    },
}

MOON_SIGN_RUDRAKSHA: Dict[str, List[int]] = {
    "Aries": [3, 9],
    "Taurus": [6, 13],
    "Gemini": [4, 10],
    "Cancer": [2, 5],
    "Leo": [1, 12],
    "Virgo": [4, 10],
    "Libra": [6, 13],
    "Scorpio": [3, 9],
    "Sagittarius": [5, 8],
    "Capricorn": [7, 14],
    "Aquarius": [7, 14],
    "Pisces": [5, 8],
}


def get_mukhi_from_description(description: str) -> Dict[str, Any]:
    desc_lower = description.lower()
    lines = 0
    if "one" in desc_lower or "single" in desc_lower or "1" in desc_lower:
        lines = 1
    elif "two" in desc_lower or "double" in desc_lower or "2" in desc_lower:
        lines = 2
    elif "three" in desc_lower or "tri" in desc_lower or "3" in desc_lower:
        lines = 3
    elif "four" in desc_lower or "quadr" in desc_lower or "4" in desc_lower:
        lines = 4
    elif "five" in desc_lower or "penta" in desc_lower or "5" in desc_lower:
        lines = 5
    elif "six" in desc_lower or "hexa" in desc_lower or "6" in desc_lower:
        lines = 6
    elif "seven" in desc_lower or "hepta" in desc_lower or "7" in desc_lower:
        lines = 7
    elif "eight" in desc_lower or "octa" in desc_lower or "8" in desc_lower:
        lines = 8
    elif "nine" in desc_lower or "enna" in desc_lower or "9" in desc_lower:
        lines = 9
    elif "ten" in desc_lower or "deca" in desc_lower or "10" in desc_lower:
        lines = 10
    elif "eleven" in desc_lower or "hendeca" in desc_lower or "11" in desc_lower:
        lines = 11
    elif "twelve" in desc_lower or "dodeca" in desc_lower or "12" in desc_lower:
        lines = 12
    elif "thirteen" in desc_lower or "trideca" in desc_lower or "13" in desc_lower:
        lines = 13
    elif "fourteen" in desc_lower or "tetradeca" in desc_lower or "14" in desc_lower:
        lines = 14

    if lines == 0:
        features = description.lower()
        if "round" in features and ("single" in features or "one line" in features):
            lines = 1
        elif "two" in features and "line" in features:
            lines = 2
        elif "five" in features and "face" in features:
            lines = 5

    data = RUDRAKSHA_DATA.get(lines, RUDRAKSHA_DATA[5])
    confidence = "High" if lines > 0 else "Low - using default 5-mukhi identification"
    return {
        "identifiedMukhi": lines if lines > 0 else 5,
        "confidence": confidence,
        "data": data,
        "note": "Please verify the identification by counting the natural lines (mukhi) on the rudraksha"
    }


@router.post("/rudraksha/recommendation")
def recommend_rudraksha(req: RudrakshaRecommendRequest):
    jd = to_julian(req.dateOfBirth, req.timeOfBirth, req.timezone)
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    xx, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
    moon_lon = xx[0]
    moon_sign = ZODIAC_SIGNS[int(moon_lon // 30) % 10]

    primary_mukhis = MOON_SIGN_RUDRAKSHA.get(moon_sign, [5])
    primary = RUDRAKSHA_DATA.get(primary_mukhis[0], RUDRAKSHA_DATA[5])
    secondary = RUDRAKSHA_DATA.get(primary_mukhis[1] if len(primary_mukhis) > 1 else 5, RUDRAKSHA_DATA[5])

    all_recommended = []
    for mk in primary_mukhis:
        all_recommended.append(RUDRAKSHA_DATA.get(mk, RUDRAKSHA_DATA[5]))

    return {
        "status": 200,
        "data": {
            "moonSign": moon_sign,
            "primaryRecommendation": primary,
            "secondaryRecommendation": secondary,
            "allRecommended": all_recommended,
            "note": "Rudraksha recommendation based on Moon sign (Rashi) position. Consult a pandit for personalized guidance."
        }
    }


@router.post("/rudraksha/mukhi-identification")
def identify_mukhi(req: MukhiIdentificationRequest):
    full_desc = req.description
    if req.visualFeatures:
        full_desc += " " + req.visualFeatures

    result = get_mukhi_from_description(full_desc)

    return {
        "status": 200,
        "data": {
            "inputDescription": req.description,
            "identification": result,
            "availableMukhis": list(RUDRAKSHA_DATA.keys()),
            "note": "This is an automated identification. For accurate identification, please consult an expert or count the natural lines manually."
        }
    }


@router.post("/rudraksha/wearing-method")
def wearing_method(req: WearingMethodRequest):
    mukhi = req.mukhiCount
    data = RUDRAKSHA_DATA.get(mukhi, RUDRAKSHA_DATA[5])

    day_map = {
        "Sun": "Sunday", "Moon": "Monday", "Mars": "Tuesday", "Mercury": "Wednesday",
        "Jupiter": "Thursday", "Venus": "Friday", "Saturn": "Saturday",
        "Rahu": "Saturday", "Ketu": "Tuesday", "All Planets": "Any day"
    }
    ruling_day = day_map.get(data["planet"], "Any day")

    wearing_guide = {
        "mukhi": mukhi,
        "name": data["name"],
        "deity": data["deity"],
        "planet": data["planet"],
        "wearingDay": ruling_day,
        "neckOrHand": "Neck (around heart level) or right hand" if mukhi <= 7 else "Neck only (around heart level)",
        "stringMaterial": "Red thread, silk thread, or gold/silver chain",
        "mantra": f"Om {data['rulingGod']} Namaha" if data["rulingGod"] != "Lord Shiva" else "Om Namah Shivaya",
        "purificationProcess": [
            "Soak in raw milk (unboiled) overnight before wearing",
            "Wake up early, take bath, and wear on " + ruling_day,
            "Chant the mantra 108 times while wearing",
            "Avoid alcohol and non-vegetarian food while wearing",
            "Remove before sleeping and keep in clean place"
        ],
        "dosAndDonts": {
            "dos": [
                "Wear with faith and devotion",
                "Chant mantra daily",
                "Keep clean and pure",
                "Share positive energy with others"
            ],
            "donts": [
                "Don't share with others",
                "Don't wear during intimacy",
                "Don't wear during funeral visits",
                "Don't use chemical cleaners"
            ]
        },
        "genderNote": "Both men and women can wear rudraksha. " + ("Men can wear on neck or right hand. Women can wear on neck or left hand." if req.gender.lower() == "male" else "Men can wear on neck or right hand. Women can wear on neck or left hand.")
    }

    return {"status": 200, "data": wearing_guide}


@router.post("/rudraksha/mantra")
def rudraksha_mantra(req: MantraRequest):
    mukhi = req.mukhiCount
    data = RUDRAKSHA_DATA.get(mukhi, RUDRAKSHA_DATA[5])

    mantras = {
        1: {"main": "Om Hreem Namah", "alternate": "Om Namah Shivaya", "purpose": "Moksha and spiritual enlightenment"},
        2: {"main": "Om Namaha", "alternate": "Om Shreem Namah", "purpose": "Marital harmony and unity"},
        3: {"main": "Om Kleem Namah", "alternate": "Om Ang Namah", "purpose": "Purification and courage"},
        4: {"main": "Om Hreem Namah", "alternate": "Om Brahma Devaya Namah", "purpose": "Knowledge and wisdom"},
        5: {"main": "Om Namah Shivaya", "alternate": "Om Hreem Namah", "purpose": "Peace and spiritual growth"},
        6: {"main": "Om Hreem Hum Namah", "alternate": "Om Saravanabhavaya Namah", "purpose": "Victory and willpower"},
        7: {"main": "Om Shreem Namah", "alternate": "Om Mahalakshmyai Namah", "purpose": "Wealth and prosperity"},
        8: {"main": "Om Gam Ganapataye Namah", "alternate": "Om Namah Shivaya", "purpose": "Obstacle removal and success"},
        9: {"main": "Om Hreem Hum Namah", "alternate": "Om Durgaye Namah", "purpose": "Protection and strength"},
        10: {"main": "Om Namah Narayanaya", "alternate": "Om Namah Shivaya", "purpose": "Complete protection and peace"},
        11: {"main": "Om Hreem Hum Namah", "alternate": "Om Rudraya Namah", "purpose": "Spiritual power and protection"},
        12: {"main": "Om Suryaya Namaha", "alternate": "Om Hreem Namah", "purpose": "Leadership and authority"},
        13: {"main": "Om Kleem Shreem Namah", "alternate": "Om Kamadevaya Namah", "purpose": "Attraction and love success"},
        14: {"main": "Om Hum Namah", "alternate": "Om Hanumate Namah", "purpose": "Courage and protection"},
    }

    mantra_data = mantras.get(mukhi, mantras[5])

    return {
        "status": 200,
        "data": {
            "mukhi": mukhi,
            "name": data["name"],
            "deity": data["deity"],
            "planet": data["planet"],
            "mainMantra": mantra_data["main"],
            "alternateMantra": mantra_data["alternate"],
            "purpose": mantra_data["purpose"],
            "japaCount": "108 times (one mala) daily",
            "bestTime": "Brahma Muhurta (4:00 AM - 5:30 AM)",
            "instructions": [
                "Sit in clean, quiet place facing East",
                "Hold rudraksha in right hand",
                "Close eyes and focus on deity",
                "Chant mantra with faith and devotion",
                "Complete 108 repetitions (one mala)",
                "Meditate silently for a few minutes after completion"
            ]
        }
    }


@router.post("/rudraksha/benefits")
def rudraksha_benefits(req: BenefitsRequest):
    mukhi = req.mukhiCount
    data = RUDRAKSHA_DATA.get(mukhi, RUDRAKSHA_DATA[5])

    health_benefits = {
        1: ["Heart health", "Mental clarity", "Spiritual awakening"],
        2: ["Emotional balance", "Relationship harmony", "Mental peace"],
        3: ["Blood purification", "Digestive health", "Courage enhancement"],
        4: ["Memory improvement", "Speech disorders", "Educational success"],
        5: ["Blood pressure control", "Stress relief", "Mental peace"],
        6: ["Reproductive health", "Joint strength", "Vitality boost"],
        7: ["Financial healing", "Debt relief", "Business success"],
        8: ["Nervous system", "Obstacle removal", "Analytical power"],
        9: ["Physical strength", "Fear removal", "Energy boost"],
        10: ["Complete protection", "Evil eye removal", "Spiritual peace"],
        11: ["Spiritual power", "Fear removal", "Mental strength"],
        12: ["Eye health", "Skin health", "Leadership aura"],
        13: ["Reproductive health", "Artistic ability", "Charm enhancement"],
        14: ["Saturn disease cure", "Court case victory", "Courage boost"],
    }

    return {
        "status": 200,
        "data": {
            "mukhi": mukhi,
            "name": data["name"],
            "deity": data["deity"],
            "planet": data["planet"],
            "description": data["description"],
            "spiritualBenefits": data["benefits"],
            "healthBenefits": health_benefits.get(mukhi, ["General well-being"]),
            "materialBenefits": data["benefits"][:3],
            "color": data["color"],
            "shape": data["shape"],
            "origin": data["origin"],
            "rarity": data["rarity"],
            "overallRating": {
                "spiritual": min(10, 3 + mukhi) if mukhi <= 7 else min(10, 14 - mukhi + 3),
                "material": min(10, mukhi) if mukhi <= 7 else min(10, 14 - mukhi + 2),
                "healing": min(10, 2 + mukhi) if mukhi <= 7 else min(10, 14 - mukhi + 4)
            }
        }
    }
