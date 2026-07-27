from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter()

INTERPRETATIONS = {
    1: {
        "positive_traits": ["Natural-born leader", "Independent and self-reliant", "Pioneering spirit", "Strong willpower", "Original thinker", "Confident and ambitious"],
        "challenges": ["Can be overly dominant", "May struggle with collaboration", "Stubbornness", "Self-centered tendencies", "Impatience with others"],
        "career_suggestions": ["Entrepreneur", "Executive/CEO", "Military officer", "Political leader", "Inventor", "Director", "Founder of startups"],
        "relationships": "You need a partner who respects your independence and ambition. You thrive with someone who supports your leadership without being submissive. Equal partnership with mutual respect is ideal.",
        "overall": "Number 1 represents the energy of new beginnings, independence, and leadership. You are a pioneer who blazes trails and inspires others through your courage and determination."
    },
    2: {
        "positive_traits": ["Diplomatic and tactful", "Cooperative team player", "Sensitive and intuitive", "Peacemaker", "Supportive and encouraging", "Excellent mediator"],
        "challenges": ["Overly sensitive to criticism", "May be indecisive", "Tendency to be codependent", "Avoids confrontation at all costs", "Can be overly passive"],
        "career_suggestions": ["Counselor/Therapist", "Diplomat", "Human Resources", "Mediator", "Teacher", "Social worker", "Artistic collaborator"],
        "relationships": "You flourish in deep, intimate partnerships. Harmony and emotional connection are essential. You need a partner who values cooperation and open communication as much as you do.",
        "overall": "Number 2 is the energy of partnership, balance, and diplomacy. You have a gift for bringing people together and creating harmony in your environment."
    },
    3: {
        "positive_traits": ["Highly creative and imaginative", "Joyful and enthusiastic", "Excellent communicator", "Social and charming", "Optimistic outlook", "Artistic talent"],
        "challenges": ["Scattered energy and focus", "Can be superficial", "Emotional volatility", "Tendency toward exaggeration", "May avoid deep emotions"],
        "career_suggestions": ["Writer/Author", "Artist/Musician/Actor", "Public speaker", "Marketing/Advertising", "Entertainer", "Graphic designer", "Journalist"],
        "relationships": "You need a partner who appreciates your expressive nature and creativity. Variety and intellectual stimulation keep you engaged. Avoid partners who are overly serious or restrictive.",
        "overall": "Number 3 is the vibration of creativity, self-expression, and joy. You have a natural gift for art, communication, and bringing lightness and laughter to those around you."
    },
    4: {
        "positive_traits": ["Extremely reliable and dependable", "Hardworking and disciplined", "Strong sense of order", "Practical and grounded", "Loyal and trustworthy", "Detail-oriented"],
        "challenges": ["Can be rigid and inflexible", "May become a workaholic", "Resistant to change", "Overly cautious", "Difficulty expressing emotions"],
        "career_suggestions": ["Engineer/Architect", "Accountant", "Project manager", "Builder/Contractor", "Banking/Finance", "Organizational roles", "Quality assurance"],
        "relationships": "You are a loyal and committed partner. Stability and routine are important to you. You need someone who values security and shares your dedication to building a solid foundation.",
        "overall": "Number 4 is the energy of structure, stability, and hard work. You are the builder who creates lasting foundations through discipline, practicality, and unwavering dedication."
    },
    5: {
        "positive_traits": ["Adventurous and free-spirited", "Versatile and adaptable", "Loves variety and change", "Charismatic and charming", "Quick learner", "Progressive thinker"],
        "challenges": ["Restlessness and impatience", "Difficulty committing", "Can be irresponsible", "Addictive tendencies", "Overstimulated easily"],
        "career_suggestions": ["Travel agent/Blogger", "Sales and marketing", "Public relations", "Sports/Adventure guide", "Journalist", "Photographer", "Entertainment industry"],
        "relationships": "You need freedom and variety in relationships. A partner who is adventurous, independent, and open-minded will complement you best. Avoid possessive or restrictive relationships.",
        "overall": "Number 5 is the vibration of freedom, adventure, and change. You are a dynamic, versatile soul who thrives on new experiences and the thrill of exploration."
    },
    6: {
        "positive_traits": ["Nurturing and caring", "Strong sense of responsibility", "Family-oriented", "Compassionate and warm", "Artistic appreciation", "Healing presence"],
        "challenges": ["Can be overprotective", "Self-sacrificing to a fault", "Worry and anxiety", "Difficulty saying no", "May become controlling"],
        "career_suggestions": ["Healthcare/Nursing", "Teacher/Educator", "Interior designer", "Chef/Nutritionist", "Veterinarian", "Counselor", "Community service"],
        "relationships": "You are a devoted and loving partner who prioritizes family and home. You need someone who reciprocates your nurturing nature and appreciates your dedication to loved ones.",
        "overall": "Number 6 is the energy of love, responsibility, and service. You are a natural nurturer who creates warmth, beauty, and harmony in your home and community."
    },
    7: {
        "positive_traits": ["Deep analytical mind", "Spiritual and philosophical", "Independent thinker", "Introspective and wise", "Perfectionist in pursuits", "Mysterious and fascinating"],
        "challenges": ["Can be overly secretive", "Emotional isolation", "Skepticism and cynicism", "Perfectionism leads to paralysis", "Difficulty connecting with others"],
        "career_suggestions": ["Scientist/Researcher", "Philosopher/Theologian", "Astrologer/Healer", "IT/Technology specialist", "Writer/Philosopher", "Detective/Analyst", "Spiritual teacher"],
        "relationships": "You need deep, meaningful connections rather than superficial ones. A partner who respects your need for solitude and intellectual/spiritual depth will be your ideal match.",
        "overall": "Number 7 is the vibration of wisdom, introspection, and spiritual seeking. You are a deep thinker who seeks truth, knowledge, and understanding of life's mysteries."
    },
    8: {
        "positive_traits": ["Natural authority and power", "Ambitious and goal-oriented", "Financially savvy", "Good organizational skills", "Determined and persistent", "Executive ability"],
        "challenges": ["Can be materialistic", "Workaholic tendencies", "Power struggles", "Difficulty with vulnerability", "May become domineering"],
        "career_suggestions": ["Business executive", "Financial advisor/Banker", "Real estate developer", "Lawyer/Judge", "Political figure", "Corporate leader", "Investment specialist"],
        "relationships": "You are attracted to successful, ambitious partners. Power dynamics matter in your relationships. You need someone who matches your drive and understands your material ambitions.",
        "overall": "Number 8 is the energy of abundance, authority, and material success. You have a natural gift for manifesting wealth and leading with power and integrity."
    },
    9: {
        "positive_traits": ["Compassionate and humanitarian", "Wise and experienced", "Generous and selfless", "Creative and artistic", "Broad-minded vision", "Spiritual depth"],
        "challenges": ["Can be idealistic to a fault", "May neglect own needs", "Difficulty letting go", "Emotional sensitivity", "Can become bitter or resentful"],
        "career_suggestions": ["Humanitarian/Activist", "Artist/Creative director", "Spiritual teacher/Healer", "Nonprofit leadership", "Environmental advocacy", "International relations", "Philanthropist"],
        "relationships": "You love deeply and selflessly. You need a partner who shares your humanitarian values and understands your need to serve something greater than yourself.",
        "overall": "Number 9 is the vibration of completion, compassion, and universal love. You are an old soul with a mission to heal, inspire, and serve humanity."
    },
    11: {
        "positive_traits": ["Highly intuitive and spiritual", "Inspirational visionary", "Psychic sensitivity", "Creative genius", "Idealistic and ambitious", "Channel for higher wisdom"],
        "challenges": ["Nervous tension and anxiety", "Difficulty grounding", "May seem impractical", "Self-doubt despite great potential", "Overwhelming sensitivity"],
        "career_suggestions": ["Spiritual teacher", "Artistic visionary", "Inventor", "Mystic/Healer", "Inspiring leader", "Creative director", "Pioneer in consciousness"],
        "relationships": "You need a spiritually aligned partner who understands your heightened sensitivity and visionary nature. Deep soul connection is more important than surface compatibility.",
        "overall": "Master Number 11 is the vibration of spiritual awakening, intuition, and illumination. You carry the energy of a spiritual messenger with the power to inspire and uplift humanity."
    },
    22: {
        "positive_traits": ["Master builder of grand visions", "Practical idealist", "Great organizational ability", "Charismatic leadership", "Can manifest large-scale projects", "Disciplined and focused"],
        "challenges": ["Immense pressure to perform", "May become a workaholic", "Difficulty balancing idealism and practicality", "Can be domineering", "Stress-related health issues"],
        "career_suggestions": ["World leader", "Architect of social change", "Large-scale entrepreneur", "Organizational leader", "Humanitarian project director", "Real estate mogul", "Institutional builder"],
        "relationships": "You need a supportive partner who understands the demands of your grand vision. Balance between mission and personal life is your greatest relationship challenge.",
        "overall": "Master Number 22 is the vibration of the Master Builder. You have the rare ability to turn your biggest dreams into tangible reality, building structures that serve humanity."
    },
    33: {
        "positive_traits": ["Master teacher and healer", "Unconditional compassion", "Selfless service", "Spiritual wisdom", "Powerful healing energy", "Elevated consciousness"],
        "challenges": ["Absorbing others' pain", "Self-neglect in service", "Can be martyred or exploited", "Difficulty setting boundaries", "Enormous expectations"],
        "career_suggestions": ["Spiritual healer", "Humanitarian leader", "Master teacher/Educator", "Compassionate counselor", "Artist with healing message", "Religious/spiritual leader", "Philanthropist"],
        "relationships": "You need a partner who supports your mission of service while helping you maintain healthy boundaries. Love is your greatest teacher and your most powerful tool.",
        "overall": "Master Number 33 is the vibration of the Master Teacher. You carry Christ-like compassion and the healing energy to transform lives through unconditional love and service."
    }
}

NATSHATRA_LETTERS = {
    1: {"nakshatra": "Ashwini", "letters": ["A", "Chu", "Che", "Cho", "La", "Li", "Lu", "Le", "Lo"]},
    2: {"nakshatra": "Bharani", "letters": ["Lu", "Le", "Lo", "Li"]},
    3: {"nakshatra": "Krittika", "letters": ["A", "E", "U", "Ea", "O", "Va", "Vi", "Vu"]},
    4: {"nakshatra": "Rohini", "letters": ["O", "Va", "Vi", "Vu", "Ve", "Vo"]},
    5: {"nakshatra": "Mrigashira", "letters": ["We", "Wo", "Ka", "Ki", "Ku", "Ke", "Ko"]},
    6: {"nakshatra": "Ardra", "letters": ["Ku", "Kam", "Ki", "Koo", "Ko", "Ha", "Hi", "Hu"]},
    7: {"nakshatra": "Punarvasu", "letters": ["Ke", "Ko", "Ha", "Hi", "Hu", "He", "Ho"]},
    8: {"nakshatra": "Pushya", "letters": ["Hu", "He", "Ho", "Da", "Di", "Du", "De", "Do"]},
    9: {"nakshatra": "Ashlesha", "letters": ["Di", "Du", "De", "Do", "Di", "Du", "De", "Do"]},
    10: {"nakshatra": "Magha", "letters": ["Ma", "Mi", "Mu", "Me", "Mo", "Ta", "Ti", "Tu", "Te", "To"]},
    11: {"nakshatra": "Purva Phalguni", "letters": ["Mo", "Ta", "Ti", "Tu", "Te", "To", "Pa", "Pi", "Pu", "Pe", "Po"]},
    12: {"nakshatra": "Uttara Phalguni", "letters": ["To", "Pa", "Pi", "Pu", "Pe", "Po", "Ra", "Ri", "Ru", "Re", "Ro"]},
    13: {"nakshatra": "Hasta", "letters": ["Pu", "Pe", "Po", "Ra", "Ri", "Ru", "Re", "Ro", "Ta", "Ti", "Tu", "Te", "To"]},
    14: {"nakshatra": "Chitra", "letters": ["Ra", "Ri", "Ru", "Re", "Ro", "Ta", "Ti", "Tu", "Te", "To"]},
    15: {"nakshatra": "Swati", "letters": ["Re", "Ro", "Ta", "Ti", "Tu", "Te", "To"]},
    16: {"nakshatra": "Vishakha", "letters": ["Ti", "Tu", "Te", "To", "Ta", "Ti", "Tu", "Te", "To"]},
    17: {"nakshatra": "Anuradha", "letters": ["Tu", "Te", "To", "Na", "Ni", "Nu", "Ne", "No"]},
    18: {"nakshatra": "Jyeshtha", "letters": ["To", "Na", "Ni", "Nu", "Ne", "No", "Ya", "Yi", "Yu"]},
    19: {"nakshatra": "Mula", "letters": ["Ya", "Yi", "Yu", "Ye", "Yo", "Bha", "Bhi", "Bhu"]},
    20: {"nakshatra": "Purva Ashadha", "letters": ["Bhu", "Bhi", "Bhu", "Bhe", "Bho", "Dha", "Dhi", "Dhu"]},
    21: {"nakshatra": "Uttara Ashadha", "letters": ["Bhe", "Bho", "Dha", "Dhi", "Dhu", "Dhe", "Dho", "Na", "Ni"]},
    22: {"nakshatra": "Shravana", "letters": ["Dhi", "Dhu", "Dhe", "Dho", "Na", "Ni", "Nu", "Ne", "No"]},
    23: {"nakshatra": "Dhanishta", "letters": ["Na", "Ni", "Nu", "Ne", "No", "Ya", "Yi", "Yu", "Ye", "Yo"]},
    24: {"nakshatra": "Shatabhisha", "letters": ["No", "Ya", "Yi", "Yu", "Ye", "Yo", "Ra", "Ri", "Ru", "Re", "Ro"]},
    25: {"nakshatra": "Purva Bhadrapada", "letters": ["Ya", "Yi", "Yu", "Ye", "Yo", "Bha", "Bhi", "Bhu", "Bhe", "Bho"]},
    26: {"nakshatra": "Uttara Bhadrapada", "letters": ["Bha", "Bhi", "Bhu", "Bhe", "Bho", "Dha", "Dhi", "Dhu", "Dhe", "Dho"]},
    27: {"nakshatra": "Revati", "letters": ["Bhu", "Bhe", "Bho", "Dha", "Dhi", "Dhu", "Dhe", "Dho", "De", "Do"]}
}

BABY_NAME_SUGGESTIONS = {
    1: {
        "male": ["Aarav", "Arjun", "Aadi", "Aditya", "Arin", "Avi", "Ansh", "Aryan", "Akash", "Atharv"],
        "female": ["Anaya", "Aria", "Aanya", "Aditi", "Anika", "Anvi", "Aadhya", "Arushi", "Avni", "Aarohi"]
    },
    2: {
        "male": ["Dhruv", "Bharat", "Dev", "Deepak", "Dinesh", "Darshan", "Daman", "Damir", "Daksh", "Danveer"],
        "female": ["Diya", "Devi", "Deepa", "Damini", "Darshana", "Devika", "Dhriti", "Dilshad", "Dipti", "Disha"]
    },
    3: {
        "male": ["Ganesh", "Gaurav", "Gopal", "Gagan", "Girish", "Govind", "Gyan", "Garv", "Gautam", "Girik"],
        "female": ["Gauri", "Gayatri", "Gita", "Ganga", "Girija", "Gopika", "Grisha", "Gunjan", "Gyatri", "Gulika"]
    },
    4: {
        "male": ["Kabir", "Karan", "Karthik", "Kailash", "Kishore", "Kunal", "Kiran", "Kamal", "Kanishk", "Kush"],
        "female": ["Kavya", "Kamini", "Kavya", "Kishori", "Kirandeep", "Kumari", "Kunti", "Kusum", "Kalpana", "Karishma"]
    },
    5: {
        "male": ["Hrishikesh", "Hrithik", "Harsh", "Hemant", "Hitesh", "Himanshu", "Harish", "Hemant", "Himan", "Hemang"],
        "female": ["Harini", "Harsha", "Hema", "Himani", "Hiteshi", "Humaira", "Hamsa", "Harshita", "Heer", "Hema"]
    },
    6: {
        "male": ["Nishant", "Nikhil", "Naveen", "Nitin", "Nishith", "Neel", "Naman", "Naksh", "Niraj", "Nisarg"],
        "female": ["Nisha", "Nandini", "Naina", "Nandita", "Nirali", "Nishita", "Nimisha", "Nilam", "Namrata", "Nitya"]
    },
    7: {
        "male": ["Yash", "Yuvan", "Yuvraj", "Yaksh", "Yatin", "Yug", "Yashwant", "Yoganand", "Yashpal", "Yogesh"],
        "female": ["Yashvi", "Yamini", "Yashaswini", "Yuvika", "Yashoda", "Yashika", "Yamika", "Yashika", "Yajna", "Yukti"]
    },
    8: {
        "male": ["Rohan", "Rahul", "Rajesh", "Ravi", "Raj", "Rishi", "Ritesh", "Rajat", "Rishabh", "Rudra"],
        "female": ["Riya", "Radha", "Ragini", "Rajni", "Rashmi", "Rekha", "Renuka", "Ritika", "Rohini", "Rubina"]
    },
    9: {
        "male": ["Shivam", "Shubham", "Shreyas", "Shankar", "Sharad", "Shakti", "Shantanu", "Shashank", "Shiva", "Shivansh"],
        "female": ["Shreya", "Shweta", "Shivani", "Shikha", "Shraddha", "Shruti", "Shubhangi", "Shailaja", "Sharmila", "Shobha"]
    }
}

LETTER_MAP = {
    'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8, 'I': 9,
    'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5, 'O': 6, 'P': 7, 'Q': 8, 'R': 9,
    'S': 1, 'T': 2, 'U': 3, 'V': 4, 'W': 5, 'X': 6, 'Y': 7, 'Z': 8
}

VOWELS = set('AEIOU')


def reduce_to_single(n: int) -> int:
    while n > 9 and n not in (11, 22, 33):
        n = sum(int(d) for d in str(n))
    return n


def letter_to_number(letter: str) -> int:
    return LETTER_MAP.get(letter.upper(), 0)


def get_interpretation(number: int) -> dict:
    return INTERPRETATIONS.get(number, INTERPRETATIONS[9])


def get_starting_letter(day: int) -> str:
    nakshatra_index = ((day - 1) % 27) + 1
    info = NATSHATRA_LETTERS.get(nakshatra_index, NATSHATRA_LETTERS[1])
    raw = info["letters"][0]
    letter = ''.join(c for c in raw if c.isalpha())
    return letter.upper() if letter else 'A'


def get_rating(number: int) -> str:
    excellent = {1, 3, 5, 6, 9, 11, 22, 33}
    good = {2, 7, 8}
    if number in excellent:
        return "Excellent"
    elif number in good:
        return "Good"
    return "Average"


def format_interpretation_response(number: int, description: str) -> dict:
    interp = get_interpretation(number)
    return {
        "status": 200,
        "number": number,
        "interpretation": interp,
        "description": description
    }


class LifePathRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")


class DestinyRequest(BaseModel):
    fullName: str = Field(..., example="John Michael Smith")


class SoulRequest(BaseModel):
    fullName: str = Field(..., example="John Michael Smith")


class ExpressionRequest(BaseModel):
    fullName: str = Field(..., example="John Michael Smith")


class MobileRequest(BaseModel):
    mobileNumber: str = Field(..., example="9876543210")


class VehicleRequest(BaseModel):
    vehicleNumber: str = Field(..., example="MH12AB1234")


class BusinessNameRequest(BaseModel):
    businessName: str = Field(..., example="Celestial Solutions")


class BabyNameRequest(BaseModel):
    dateOfBirth: str = Field(..., example="2024-03-15")
    gender: str = Field(..., example="male")
    parentName: Optional[str] = Field(None, example="Rahul Sharma")


@router.post('/numerology/life-path')
def life_path_number(body: LifePathRequest):
    parts = body.dateOfBirth.replace('-', '').replace('/', '').replace('.', '')
    digits = [int(d) for d in parts if d.isdigit()]

    if len(digits) != 8:
        return {"status": 400, "error": "Invalid date format. Use YYYY-MM-DD."}

    year = digits[0] * 1000 + digits[1] * 100 + digits[2] * 10 + digits[3]
    month = digits[4] * 10 + digits[5]
    day = digits[6] * 10 + digits[7]

    year_sum = sum(int(d) for d in str(year))
    month_sum = sum(int(d) for d in str(month))
    day_sum = sum(int(d) for d in str(day))

    total = year_sum + month_sum + day_sum
    life_path = reduce_to_single(total)

    interp = get_interpretation(life_path)
    description = (
        f"Your Life Path Number is {life_path}. "
        f"Calculated from birth date {body.dateOfBirth}: "
        f"Year digits sum = {year_sum}, Month digits sum = {month_sum}, "
        f"Day digits sum = {day_sum}, Total = {total}, Reduced = {life_path}. "
        f"{interp['overall']}"
    )

    return format_interpretation_response(life_path, description)


@router.post('/numerology/destiny')
def destiny_number(body: DestinyRequest):
    name = body.fullName.upper().strip()
    total = sum(letter_to_number(ch) for ch in name if ch.isalpha())
    destiny = reduce_to_single(total)

    interp = get_interpretation(destiny)
    description = (
        f"Your Destiny Number is {destiny}. "
        f"Calculated from name '{body.fullName}': sum of all letter values = {total}, "
        f"reduced to {destiny}. "
        f"{interp['overall']}"
    )

    return format_interpretation_response(destiny, description)


@router.post('/numerology/soul')
def soul_number(body: SoulRequest):
    name = body.fullName.upper().strip()
    vowel_total = sum(letter_to_number(ch) for ch in name if ch in VOWELS)
    soul = reduce_to_single(vowel_total) if vowel_total > 0 else 0

    interp = get_interpretation(soul) if soul > 0 else {"positive_traits": [], "challenges": [], "career_suggestions": [], "relationships": "No vowels found.", "overall": "No soul number could be calculated."}
    description = (
        f"Your Soul Urge (Heart's Desire) Number is {soul}. "
        f"Calculated from vowels in '{body.fullName}': vowel sum = {vowel_total}, "
        f"reduced to {soul}. "
        f"{interp['overall']}"
    )

    return format_interpretation_response(soul, description)


@router.post('/numerology/expression')
def expression_number(body: ExpressionRequest):
    name = body.fullName.upper().strip()
    total = sum(letter_to_number(ch) for ch in name if ch.isalpha())
    expression = reduce_to_single(total)

    interp = get_interpretation(expression)
    description = (
        f"Your Expression Number is {expression}. "
        f"Calculated from all letters in '{body.fullName}': total = {total}, "
        f"reduced to {expression}. "
        f"{interp['overall']}"
    )

    return format_interpretation_response(expression, description)


@router.post('/numerology/mobile')
def mobile_number(body: MobileRequest):
    digits = [int(d) for d in body.mobileNumber if d.isdigit()]
    total = sum(digits)
    mobile_num = reduce_to_single(total)
    rating = get_rating(mobile_num)

    interp = get_interpretation(mobile_num)
    description = (
        f"Your Mobile Number reduces to {mobile_num} (Rating: {rating}). "
        f"Digit sum of '{body.mobileNumber}' = {total}, reduced to {mobile_num}. "
        f"{interp['overall']}"
    )

    return {
        "status": 200,
        "number": mobile_num,
        "rating": rating,
        "interpretation": interp,
        "description": description
    }


@router.post('/numerology/vehicle')
def vehicle_number(body: VehicleRequest):
    digits = [int(d) for d in body.vehicleNumber if d.isdigit()]
    total = sum(digits)
    vehicle_num = reduce_to_single(total)
    rating = get_rating(vehicle_num)

    interp = get_interpretation(vehicle_num)
    description = (
        f"Your Vehicle Number reduces to {vehicle_num} (Rating: {rating}). "
        f"Numeric digits in '{body.vehicleNumber}' are {''.join(str(d) for d in digits)}, "
        f"sum = {total}, reduced to {vehicle_num}. "
        f"{interp['overall']}"
    )

    return {
        "status": 200,
        "number": vehicle_num,
        "rating": rating,
        "interpretation": interp,
        "description": description
    }


@router.post('/numerology/business-name')
def business_name_number(body: BusinessNameRequest):
    name = body.businessName.upper().strip()
    total = sum(letter_to_number(ch) for ch in name if ch.isalpha())
    name_number = reduce_to_single(total)

    vowels_sum = sum(letter_to_number(ch) for ch in name if ch in VOWELS)
    consonants_sum = total - vowels_sum
    destiny = reduce_to_single(total)

    compatibility_score = 100 - abs(name_number - destiny) * 11
    if compatibility_score < 0:
        compatibility_score = 0

    name_interp = get_interpretation(name_number)
    destiny_interp = get_interpretation(destiny)

    if compatibility_score >= 80:
        compat_label = "Excellent"
    elif compatibility_score >= 60:
        compat_label = "Good"
    elif compatibility_score >= 40:
        compat_label = "Average"
    else:
        compat_label = "Challenging"

    description = (
        f"Business Name '{body.businessName}' analysis: "
        f"Name Number = {name_number}, Destiny Number = {destiny}. "
        f"Vowel sum = {vowels_sum}, Consonant sum = {consonants_sum}. "
        f"Name-Destiny Compatibility = {compatibility_score}% ({compat_label}). "
        f"The business energy leans toward {name_interp['overall'].lower()}"
    )

    return {
        "status": 200,
        "name_number": name_number,
        "destiny_number": destiny,
        "compatibility_score": compatibility_score,
        "compatibility_label": compat_label,
        "name_interpretation": name_interp,
        "destiny_interpretation": destiny_interp,
        "description": description
    }


@router.post('/numerology/baby-name')
def baby_name(body: BabyNameRequest):
    parts = body.dateOfBirth.replace('-', '').replace('/', '').replace('.', '')
    digits = [int(d) for d in parts if d.isdigit()]

    year = digits[0] * 1000 + digits[1] * 100 + digits[2] * 10 + digits[3]
    month = digits[4] * 10 + digits[5]
    day = digits[6] * 10 + digits[7]

    year_sum = sum(int(d) for d in str(year))
    month_sum = sum(int(d) for d in str(month))
    day_sum = sum(int(d) for d in str(day))

    total = year_sum + month_sum + day_sum
    life_path = reduce_to_single(total)

    starting_letter = get_starting_letter(day)

    gender = body.gender.lower().strip()
    if gender not in ("male", "female", "m", "f"):
        gender = "male"
    if gender in ("m",):
        gender = "male"
    if gender in ("f",):
        gender = "female"

    suggested_names = BABY_NAME_SUGGESTIONS.get(life_path, BABY_NAME_SUGGESTIONS[9])
    names_list = suggested_names.get(gender, suggested_names["male"])

    nakshatra_index = ((day - 1) % 27) + 1
    nakshatra_info = NATSHATRA_LETTERS.get(nakshatra_index, NATSHATRA_LETTERS[1])

    interp = get_interpretation(life_path)

    description = (
        f"Baby Name Recommendations for a {gender} child born on {body.dateOfBirth}: "
        f"Life Path Number = {life_path}. "
        f"Birth Nakshatra = {nakshatra_info['nakshatra']}, "
        f"Recommended starting letter = '{starting_letter}'. "
        f"Names starting with '{starting_letter}' carry the energy of "
        f"{nakshatra_info['nakshatra']} nakshatra. "
        f"{interp['overall']}"
    )

    result = {
        "status": 200,
        "life_path_number": life_path,
        "starting_letter": starting_letter,
        "birth_nakshatra": nakshatra_info["nakshatra"],
        "nakshatra_letters": nakshatra_info["letters"],
        "suggested_names": names_list,
        "interpretation": interp,
        "description": description
    }

    if body.parentName:
        parent_upper = body.parentName.upper().strip()
        parent_total = sum(letter_to_number(ch) for ch in parent_upper if ch.isalpha())
        parent_number = reduce_to_single(parent_total)
        result["parent_number"] = parent_number
        result["parent_name_analysis"] = get_interpretation(parent_number)

    return result
