from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

router = APIRouter()

class BirthDateRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")


def _reduce_to_single(n):
    while n > 9 and n != 11 and n != 22 and n != 33:
        n = sum(int(d) for d in str(n))
    return n


def _name_to_number(name):
    mapping = {
        'A':1,'B':2,'C':3,'D':4,'E':5,'F':6,'G':7,'H':8,'I':9,
        'J':1,'K':2,'L':3,'M':4,'N':5,'O':6,'P':7,'Q':8,'R':9,
        'S':1,'T':2,'U':3,'V':4,'W':5,'X':6,'Y':7,'Z':8,
    }
    total = sum(mapping.get(c.upper(), 0) for c in name if c.isalpha())
    return _reduce_to_single(total)


_LUCKY_DATA = {
    1: {"color": "Gold, Yellow, Orange", "number": "1, 3, 5, 9", "day": "Sunday", "metal": "Gold", "gem": "Ruby", "element": "Fire"},
    2: {"color": "White, Silver, Cream", "number": "2, 4, 7, 9", "day": "Monday", "metal": "Silver", "gem": "Pearl", "element": "Water"},
    3: {"color": "Yellow, Orange, Red", "number": "1, 3, 5, 9", "day": "Thursday", "metal": "Gold", "gem": "Yellow Sapphire", "element": "Fire"},
    4: {"color": "Blue, Grey, Green", "number": "2, 4, 7, 8", "day": "Saturday", "metal": "Iron/Steel", "gem": "Blue Sapphire", "element": "Air"},
    5: {"color": "Green, Light Green, Aqua", "number": "2, 3, 5, 6", "day": "Wednesday", "metal": "Mercury/Bronze", "gem": "Emerald", "element": "Earth"},
    6: {"color": "Pink, Rose, White", "number": "3, 5, 6, 9", "day": "Friday", "metal": "Copper", "gem": "Diamond", "element": "Water"},
    7: {"color": "White, Grey, Brown", "number": "1, 2, 4, 7", "day": "Monday", "metal": "Silver", "gem": "Cat's Eye", "element": "Water"},
    8: {"color": "Blue, Black, Dark Grey", "number": "1, 4, 5, 8", "day": "Saturday", "metal": "Iron", "gem": "Blue Sapphire", "element": "Earth"},
    9: {"color": "Red, Orange, Saffron", "number": "1, 3, 5, 9", "day": "Tuesday", "metal": "Copper/Gold", "gem": "Red Coral", "element": "Fire"},
    11: {"color": "Silver, White, Light Blue", "number": "2, 4, 7, 11", "day": "Monday", "metal": "Silver", "gem": "Moonstone", "element": "Air"},
    22: {"color": "Blue, Navy, Purple", "number": "4, 6, 7, 22", "day": "Saturday", "metal": "Steel", "gem": "Blue Sapphire", "element": "Air"},
    33: {"color": "Gold, Rose, Lavender", "number": "3, 6, 9, 33", "day": "Thursday", "metal": "Gold", "gem": "Yellow Sapphire", "element": "Fire"},
}


@router.post("/lucky/color")
def lucky_color(body: BirthDateRequest) -> Dict[str, Any]:
    parts = body.dateOfBirth.split('-')
    day = int(parts[2])
    life_path = _reduce_to_single(int(parts[0]) + int(parts[1]) + day)
    root = _LUCKY_DATA.get(life_path, _LUCKY_DATA[1])
    return {
        "success": True,
        "data": {
            "birthDate": body.dateOfBirth,
            "lifePathNumber": life_path,
            "luckyColors": root["color"],
            "description": f"Colors aligned with your life path number {life_path} resonate with {root['element']} energy and enhance your natural strengths.",
            "avoidColors": "Black and dark grey can dampen your energy" if life_path in [1, 3, 9] else "Bright reds and oranges may overstimulate" if life_path in [2, 7] else "Neutral palette works best",
        }
    }


@router.post("/lucky/number")
def lucky_number(body: BirthDateRequest) -> Dict[str, Any]:
    parts = body.dateOfBirth.split('-')
    day = int(parts[2])
    life_path = _reduce_to_single(int(parts[0]) + int(parts[1]) + day)
    root = _LUCKY_DATA.get(life_path, _LUCKY_DATA[1])
    return {
        "success": True,
        "data": {
            "birthDate": body.dateOfBirth,
            "lifePathNumber": life_path,
            "luckyNumbers": root["number"],
            "description": f"Numbers {root['number']} carry vibrations aligned with your life path {life_path}. Use them for important decisions, addresses, and dates.",
            "tip": "Single-digit root number is most powerful. Compound numbers add secondary influences.",
        }
    }


@router.post("/lucky/day")
def lucky_day(body: BirthDateRequest) -> Dict[str, Any]:
    parts = body.dateOfBirth.split('-')
    day = int(parts[2])
    life_path = _reduce_to_single(int(parts[0]) + int(parts[1]) + day)
    root = _LUCKY_DATA.get(life_path, _LUCKY_DATA[1])
    return {
        "success": True,
        "data": {
            "birthDate": body.dateOfBirth,
            "lifePathNumber": life_path,
            "luckyDay": root["day"],
            "description": f"{root['day']} is your most powerful day of the week. Schedule important meetings, interviews, and beginnings on this day for maximum cosmic support.",
            "planetaryRuler": {
                "Sunday": "Sun", "Monday": "Moon", "Tuesday": "Mars", "Wednesday": "Mercury",
                "Thursday": "Jupiter", "Friday": "Venus", "Saturday": "Saturn"
            }.get(root["day"], "Unknown"),
        }
    }


@router.post("/lucky/metal")
def lucky_metal(body: BirthDateRequest) -> Dict[str, Any]:
    parts = body.dateOfBirth.split('-')
    day = int(parts[2])
    life_path = _reduce_to_single(int(parts[0]) + int(parts[1]) + day)
    root = _LUCKY_DATA.get(life_path, _LUCKY_DATA[1])
    return {
        "success": True,
        "data": {
            "birthDate": body.dateOfBirth,
            "lifePathNumber": life_path,
            "luckyMetal": root["metal"],
            "luckyGemstone": root["gem"],
            "element": root["element"],
            "description": f"Wearing {root['metal']} jewelry or carrying {root['metal']} items strengthens your planetary alignment. {root['gem']} is your birth-chart-aligned gemstone.",
            "wearAdvice": f"Wear {root['gem']} on the appropriate finger during {root['day']} {root['metal']} hora for maximum benefit.",
        }
    }
