from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

router = APIRouter()

class FestivalRequest(BaseModel):
    year: int = Field(..., example=2025)
    month: Optional[int] = Field(None, example=1)

class EkadashiRequest(BaseModel):
    year: int = Field(..., example=2025)
    month: Optional[int] = Field(None, example=6)

HINDU_FESTIVALS: Dict[int, Dict[str, str]] = {
    2024: {
        "Makar Sankranti": "2024-01-14", "Vasant Panchami": "2024-02-14",
        "Maha Shivaratri": "2024-03-08", "Holi": "2024-03-25",
        "Ugadi": "2024-04-09", "Ram Navami": "2024-04-17",
        "Hanuman Jayanti": "2024-04-23", "Akshaya Tritiya": "2024-05-10",
        "Ganga Dussehra": "2024-06-16", "Jyeshtha Purnima": "2024-06-22",
        "Guru Purnima": "2024-07-21", "Nag Panchami": "2024-08-04",
        "Raksha Bandhan": "2024-08-19", "Krishna Janmashtami": "2024-08-26",
        "Ganesh Chaturthi": "2024-09-07", "Pitru Paksha Start": "2024-09-17",
        "Navratri Start": "2024-10-03", "Dussehra": "2024-10-12",
        "Diwali": "2024-11-01", "Chhath Puja": "2024-11-07",
        "Guru Nanak Jayanti": "2024-11-15"
    },
    2025: {
        "Makar Sankranti": "2025-01-14", "Vasant Panchami": "2025-02-02",
        "Maha Shivaratri": "2025-02-26", "Holi": "2025-03-14",
        "Ugadi": "2025-03-30", "Ram Navami": "2025-04-06",
        "Hanuman Jayanti": "2025-04-12", "Akshaya Tritiya": "2025-04-30",
        "Ganga Dussehra": "2025-06-05", "Jyeshtha Purnima": "2025-06-11",
        "Guru Purnima": "2025-07-10", "Nag Panchami": "2025-07-24",
        "Raksha Bandhan": "2025-08-08", "Krishna Janmashtami": "2025-08-15",
        "Ganesh Chaturthi": "2025-08-27", "Pitru Paksha Start": "2025-09-06",
        "Navratri Start": "2025-09-22", "Dussehra": "2025-10-01",
        "Diwali": "2025-10-20", "Chhath Puja": "2025-10-26",
        "Guru Nanak Jayanti": "2025-11-04"
    },
    2026: {
        "Makar Sankranti": "2026-01-14", "Vasant Panchami": "2026-01-22",
        "Maha Shivaratri": "2026-02-15", "Holi": "2026-03-04",
        "Ugadi": "2026-03-19", "Ram Navami": "2026-03-26",
        "Hanuman Jayanti": "2026-04-01", "Akshaya Tritiya": "2026-04-19",
        "Ganga Dussehra": "2026-05-25", "Jyeshtha Purnima": "2026-05-31",
        "Guru Purnima": "2026-06-29", "Nag Panchami": "2026-07-13",
        "Raksha Bandhan": "2026-07-28", "Krishna Janmashtami": "2026-08-04",
        "Ganesh Chaturthi": "2026-08-16", "Pitru Paksha Start": "2026-08-26",
        "Navratri Start": "2026-09-11", "Dussehra": "2026-09-20",
        "Diwali": "2026-11-08", "Chhath Puja": "2026-11-14",
        "Guru Nanak Jayanti": "2026-11-23"
    },
    2027: {
        "Makar Sankranti": "2027-01-14", "Vasant Panchami": "2027-02-11",
        "Maha Shivaratri": "2027-03-05", "Holi": "2027-03-24",
        "Ugadi": "2027-04-08", "Ram Navami": "2027-04-15",
        "Hanuman Jayanti": "2027-04-21", "Akshaya Tritiya": "2027-05-08",
        "Ganga Dussehra": "2027-06-14", "Jyeshtha Purnima": "2027-06-20",
        "Guru Purnima": "2027-07-19", "Nag Panchami": "2027-08-02",
        "Raksha Bandhan": "2027-08-17", "Krishna Janmashtami": "2027-08-24",
        "Ganesh Chaturthi": "2027-09-05", "Pitru Paksha Start": "2027-09-15",
        "Navratri Start": "2027-10-01", "Dussehra": "2027-10-10",
        "Diwali": "2027-10-29", "Chhath Puja": "2027-11-04",
        "Guru Nanak Jayanti": "2027-11-13"
    },
    2028: {
        "Makar Sankranti": "2028-01-14", "Vasant Panchami": "2028-01-31",
        "Maha Shivaratri": "2028-02-22", "Holi": "2028-03-11",
        "Ugadi": "2028-03-27", "Ram Navami": "2028-04-03",
        "Hanuman Jayanti": "2028-04-09", "Akshaya Tritiya": "2028-04-27",
        "Ganga Dussehra": "2028-06-02", "Jyeshtha Purnima": "2028-06-08",
        "Guru Purnima": "2028-07-07", "Nag Panchami": "2028-07-21",
        "Raksha Bandhan": "2028-08-05", "Krishna Janmashtami": "2028-08-12",
        "Ganesh Chaturthi": "2028-08-24", "Pitru Paksha Start": "2028-09-03",
        "Navratri Start": "2028-09-19", "Dussehra": "2028-09-28",
        "Diwali": "2028-11-16", "Chhath Puja": "2028-11-22",
        "Guru Nanak Jayanti": "2028-12-01"
    },
    2029: {
        "Makar Sankranti": "2029-01-14", "Vasant Panchami": "2029-02-19",
        "Maha Shivaratri": "2029-03-12", "Holi": "2029-03-31",
        "Ugadi": "2029-04-15", "Ram Navami": "2029-04-22",
        "Hanuman Jayanti": "2029-04-28", "Akshaya Tritiya": "2029-05-15",
        "Ganga Dussehra": "2029-06-22", "Jyeshtha Purnima": "2029-06-28",
        "Guru Purnima": "2029-07-27", "Nag Panchami": "2029-08-10",
        "Raksha Bandhan": "2029-08-25", "Krishna Janmashtami": "2029-09-01",
        "Ganesh Chaturthi": "2029-09-13", "Pitru Paksha Start": "2029-09-23",
        "Navratri Start": "2029-10-08", "Dussehra": "2029-10-17",
        "Diwali": "2029-11-05", "Chhath Puja": "2029-11-11",
        "Guru Nanak Jayanti": "2029-11-20"
    },
    2030: {
        "Makar Sankranti": "2030-01-14", "Vasant Panchami": "2030-02-08",
        "Maha Shivaratri": "2030-03-01", "Holi": "2030-03-20",
        "Ugadi": "2030-04-04", "Ram Navami": "2030-04-11",
        "Hanuman Jayanti": "2030-04-17", "Akshaya Tritiya": "2030-05-04",
        "Ganga Dussehra": "2030-06-11", "Jyeshtha Purnima": "2030-06-17",
        "Guru Purnima": "2030-07-16", "Nag Panchami": "2030-07-30",
        "Raksha Bandhan": "2030-08-14", "Krishna Janmashtami": "2030-08-21",
        "Ganesh Chaturthi": "2030-09-02", "Pitru Paksha Start": "2030-09-12",
        "Navratri Start": "2030-09-27", "Dussehra": "2030-10-06",
        "Diwali": "2030-10-25", "Chhath Puja": "2030-10-31",
        "Guru Nanak Jayanti": "2030-11-09"
    },
}

EKADASHI_DATES: Dict[int, Dict[str, str]] = {
    2024: {
        "Shukla": ["2024-01-21","2024-02-19","2024-03-20","2024-04-18","2024-05-18","2024-06-17",
                    "2024-07-17","2024-08-15","2024-09-14","2024-10-13","2024-11-12","2024-12-12"],
        "Krishna": ["2024-01-06","2024-02-05","2024-03-05","2024-04-04","2024-05-03","2024-06-02",
                     "2024-07-02","2024-07-31","2024-08-30","2024-09-28","2024-10-28","2024-11-27","2024-12-27"]
    },
    2025: {
        "Shukla": ["2025-01-10","2025-02-08","2025-03-10","2025-04-08","2025-05-08","2025-06-07",
                    "2025-07-06","2025-08-05","2025-09-03","2025-10-03","2025-11-01","2025-12-01"],
        "Krishna": ["2025-01-25","2025-02-24","2025-03-25","2025-04-24","2025-05-23","2025-06-22",
                     "2025-07-21","2025-08-20","2025-09-18","2025-10-18","2025-11-16","2025-12-16"]
    },
    2026: {
        "Shukla": ["2026-01-10","2026-02-09","2026-03-11","2026-04-09","2026-05-09","2026-06-07",
                    "2026-07-07","2026-08-05","2026-09-04","2026-10-03","2026-11-01","2026-12-01"],
        "Krishna": ["2026-01-25","2026-02-24","2026-03-26","2026-04-24","2026-05-24","2026-06-22",
                     "2026-07-22","2026-08-20","2026-09-18","2026-10-18","2026-11-16","2026-12-16"]
    },
    2027: {
        "Shukla": ["2027-01-10","2027-02-09","2027-03-11","2027-04-09","2027-05-09","2027-06-07",
                    "2027-07-07","2027-08-05","2027-09-04","2027-10-03","2027-11-01","2027-12-01"],
        "Krishna": ["2027-01-25","2027-02-24","2027-03-26","2027-04-24","2027-05-24","2027-06-22",
                     "2027-07-22","2027-08-20","2027-09-18","2027-10-18","2027-11-16","2027-12-16"]
    },
    2028: {
        "Shukla": ["2028-01-09","2028-02-08","2028-03-09","2028-04-08","2028-05-07","2028-06-06",
                    "2028-07-06","2028-08-04","2028-09-03","2028-10-02","2028-10-31","2028-11-30"],
        "Krishna": ["2028-01-24","2028-02-23","2028-03-24","2028-04-23","2028-05-23","2028-06-21",
                     "2028-07-21","2028-08-19","2028-09-17","2028-10-17","2028-11-15","2028-12-15"]
    },
    2029: {
        "Shukla": ["2029-01-08","2029-02-07","2029-03-09","2029-04-07","2029-05-07","2029-06-05",
                    "2029-07-05","2029-08-03","2029-09-02","2029-10-01","2029-10-31","2029-11-29"],
        "Krishna": ["2029-01-23","2029-02-22","2029-03-24","2029-04-22","2029-05-22","2029-06-20",
                     "2029-07-20","2029-08-18","2029-09-16","2029-10-16","2029-11-14","2029-12-14"]
    },
    2030: {
        "Shukla": ["2030-01-08","2030-02-06","2030-03-08","2030-04-06","2030-05-06","2030-06-05",
                    "2030-07-04","2030-08-03","2030-09-01","2030-10-01","2030-10-30","2030-11-29"],
        "Krishna": ["2030-01-23","2030-02-22","2030-03-24","2030-04-22","2030-05-22","2030-06-20",
                     "2030-07-19","2030-08-18","2030-09-16","2030-10-16","2030-11-14","2030-12-13"]
    },
}

SANKRANTI_DATES: Dict[int, List[str]] = {
    2024: ["2024-01-14","2024-02-12","2024-03-14","2024-04-14","2024-05-15","2024-06-15",
           "2024-07-17","2024-08-17","2024-09-17","2024-10-17","2024-11-16","2024-12-16"],
    2025: ["2025-01-14","2025-02-12","2025-03-14","2025-04-14","2025-05-15","2025-06-15",
           "2025-07-17","2025-08-17","2025-09-17","2025-10-17","2025-11-16","2025-12-16"],
    2026: ["2026-01-14","2026-02-12","2026-03-14","2026-04-14","2026-05-15","2026-06-15",
           "2026-07-17","2026-08-17","2026-09-17","2026-10-17","2026-11-16","2026-12-16"],
    2027: ["2027-01-14","2027-02-12","2027-03-14","2027-04-14","2027-05-15","2027-06-15",
           "2027-07-17","2027-08-17","2027-09-17","2027-10-17","2027-11-16","2027-12-16"],
    2028: ["2028-01-14","2028-02-12","2028-03-14","2028-04-14","2028-05-15","2028-06-15",
           "2028-07-17","2028-08-17","2028-09-17","2028-10-17","2028-11-16","2028-12-16"],
    2029: ["2029-01-14","2029-02-12","2029-03-14","2029-04-14","2029-05-15","2029-06-15",
           "2029-07-17","2029-08-17","2029-09-17","2029-10-17","2029-11-16","2029-12-16"],
    2030: ["2030-01-14","2030-02-12","2030-03-14","2030-04-14","2030-05-15","2030-06-15",
           "2030-07-17","2030-08-17","2030-09-17","2030-10-17","2030-11-16","2030-12-16"],
}

PURNIMA_DATES: Dict[int, List[str]] = {
    2024: ["2024-01-25","2024-02-24","2024-03-25","2024-04-23","2024-05-23","2024-06-22",
           "2024-07-21","2024-08-19","2024-09-18","2024-10-17","2024-11-15","2024-12-15"],
    2025: ["2025-01-13","2025-02-12","2025-03-14","2025-04-12","2025-05-12","2025-06-11",
           "2025-07-10","2025-08-09","2025-09-07","2025-10-07","2025-11-05","2025-12-04"],
    2026: ["2026-01-03","2026-02-01","2026-03-03","2026-04-01","2026-05-01","2026-05-30",
           "2026-06-29","2026-07-28","2026-08-27","2026-09-25","2026-10-25","2026-11-23"],
    2027: ["2027-01-22","2027-02-20","2027-03-22","2027-04-21","2027-05-20","2027-06-19",
           "2027-07-18","2027-08-17","2027-09-15","2027-10-14","2027-11-13","2027-12-12"],
    2028: ["2028-01-11","2028-02-10","2028-03-11","2028-04-09","2028-05-09","2028-06-07",
           "2028-07-07","2028-08-05","2028-09-04","2028-10-03","2028-11-02","2028-12-01"],
    2029: ["2029-01-01","2029-01-30","2029-03-01","2029-03-30","2029-04-28","2029-05-27",
           "2029-06-26","2029-07-25","2029-08-24","2029-09-22","2029-10-22","2029-11-20"],
    2030: ["2030-01-20","2030-02-18","2030-03-20","2030-04-19","2030-05-18","2030-06-17",
           "2030-07-16","2030-08-15","2030-09-13","2030-10-13","2030-11-11","2030-12-11"],
}

AMAVASYA_DATES: Dict[int, List[str]] = {
    2024: ["2024-01-11","2024-02-09","2024-03-10","2024-04-08","2024-05-08","2024-06-06",
           "2024-07-05","2024-08-04","2024-09-02","2024-10-02","2024-10-31","2024-11-30","2024-12-30"],
    2025: ["2025-01-29","2025-02-27","2025-03-29","2025-04-27","2025-05-27","2025-06-25",
           "2025-07-24","2025-08-23","2025-09-21","2025-10-21","2025-11-20","2025-12-19"],
    2026: ["2026-01-18","2026-02-17","2026-03-19","2026-04-17","2026-05-16","2026-06-15",
           "2026-07-14","2026-08-13","2026-09-11","2026-10-11","2026-11-09","2026-12-09"],
    2027: ["2027-01-07","2027-02-06","2027-03-08","2027-04-06","2027-05-06","2027-06-04",
           "2027-07-03","2027-08-02","2027-08-31","2027-09-30","2027-10-29","2027-11-28","2027-12-28"],
    2028: ["2028-01-27","2028-02-25","2028-03-26","2028-04-24","2028-05-24","2028-06-22",
           "2028-07-22","2028-08-20","2028-09-19","2028-10-18","2028-11-17","2028-12-16"],
    2029: ["2029-01-15","2029-02-14","2029-03-16","2029-04-14","2029-05-14","2029-06-12",
           "2029-07-12","2029-08-10","2029-09-09","2029-10-08","2029-11-07","2029-12-06"],
    2030: ["2030-01-05","2030-02-04","2030-03-06","2030-04-04","2030-05-04","2030-06-02",
           "2030-07-02","2030-07-31","2030-08-30","2030-09-28","2030-10-28","2030-11-26","2030-12-26"],
}

CHATURTHI_DATES: Dict[int, str] = {
    2024: "2024-09-07", 2025: "2025-08-27", 2026: "2026-08-16",
    2027: "2027-09-05", 2028: "2028-08-24", 2029: "2029-09-13", 2030: "2030-09-02",
}

NAVRATRI_DATES: Dict[int, Dict[str, str]] = {
    2024: {"start": "2024-10-03", "end": "2024-10-12"},
    2025: {"start": "2025-09-22", "end": "2025-10-01"},
    2026: {"start": "2026-09-11", "end": "2026-09-20"},
    2027: {"start": "2027-10-01", "end": "2027-10-10"},
    2028: {"start": "2028-09-19", "end": "2028-09-28"},
    2029: {"start": "2029-10-08", "end": "2029-10-17"},
    2030: {"start": "2030-09-27", "end": "2030-10-06"},
}

DIWALI_DATES: Dict[int, str] = {
    2024: "2024-11-01", 2025: "2025-10-20", 2026: "2026-11-08",
    2027: "2027-10-29", 2028: "2028-11-16", 2029: "2029-11-05", 2030: "2030-10-25",
}

HOLI_DATES: Dict[int, str] = {
    2024: "2024-03-25", 2025: "2025-03-14", 2026: "2026-03-04",
    2027: "2027-03-24", 2028: "2028-03-11", 2029: "2029-03-31", 2030: "2030-03-20",
}

SANKRANTI_NAMES = [
    "Makar Sankranti","Kumbh Sankranti","Meena Sankranti","Mesha Sankranti",
    "Vrishabha Sankranti","Mithuna Sankranti","Karka Sankranti","Simha Sankranti",
    "Kanya Sankranti","Tula Sankranti","Vrischika Sankranti","Dhanu Sankranti"
]

EKADASHI_NAMES = [
    "Shattila Ekadashi","Jaya Ekadashi","Amalaki Ekadashi","Kamada Ekadashi",
    "Varuthini Ekadashi","Moha Ekadashi","Ashadhi Ekadashi","Pavitra Ekadashi",
    "Aja Ekadashi","Indira Ekadashi","Rama Ekadashi","Annapurna Ekadashi"
]


def get_ekadashi_for_month(year: int, month: int) -> List[Dict[str, str]]:
    result = []
    year_data = EKADASHI_DATES.get(year, EKADASHI_DATES.get(2025, {}))
    shukla = year_data.get("Shukla", [])
    krishna = year_data.get("Krishna", [])
    idx = month - 1
    if idx < len(shukla):
        result.append({
            "date": shukla[idx],
            "paksha": "Shukla",
            "name": EKADASHI_NAMES[idx % 12],
            "description": f"Shukla Paksha Ekadashi of Hindu month {month}"
        })
    if idx < len(krishna):
        result.append({
            "date": krishna[idx],
            "paksha": "Krishna",
            "name": f"Krishna {EKADASHI_NAMES[idx % 12]}",
            "description": f"Krishna Paksha Ekadashi of Hindu month {month}"
        })
    return result


@router.post("/festival/hindu-festival")
def hindu_festival(req: FestivalRequest):
    year = req.year
    festivals = HINDU_FESTIVALS.get(year, {})
    if req.month:
        festivals = {k: v for k, v in festivals.items() if v.startswith(f"{year}-{req.month:02d}")}
    return {"status": 200, "data": {"year": year, "festivals": festivals, "total": len(festivals)}}


@router.post("/festival/ekadashi")
def ekadashi_dates(req: EkadashiRequest):
    year = req.year
    if req.month:
        dates = get_ekadashi_for_month(year, req.month)
    else:
        dates = []
        for m in range(1, 13):
            dates.extend(get_ekadashi_for_month(year, m))
    return {"status": 200, "data": {"year": year, "month": req.month, "ekadashi": dates, "total": len(dates)}}


@router.post("/festival/sankranti")
def sankranti_dates(req: FestivalRequest):
    year = req.year
    dates = SANKRANTI_DATES.get(year, SANKRANTI_DATES.get(2025, []))
    result = []
    for i, d in enumerate(dates):
        month = i + 1
        if req.month and month != req.month:
            continue
        result.append({"date": d, "name": SANKRANTI_NAMES[i], "month": month})
    return {"status": 200, "data": {"year": year, "sankranti": result, "total": len(result)}}


@router.post("/festival/purnima")
def purnima_dates(req: FestivalRequest):
    year = req.year
    dates = PURNIMA_DATES.get(year, PURNIMA_DATES.get(2025, []))
    if req.month:
        dates = [d for d in dates if d.startswith(f"{year}-{req.month:02d}")]
    return {"status": 200, "data": {"year": year, "month": req.month, "purnima": dates, "total": len(dates)}}


@router.post("/festival/amavasya")
def amavasya_dates(req: FestivalRequest):
    year = req.year
    dates = AMAVASYA_DATES.get(year, AMAVASYA_DATES.get(2025, []))
    if req.month:
        dates = [d for d in dates if d.startswith(f"{year}-{req.month:02d}")]
    return {"status": 200, "data": {"year": year, "month": req.month, "amavasya": dates, "total": len(dates)}}


@router.post("/festival/chaturthi")
def chaturthi_dates(req: FestivalRequest):
    year = req.year
    date = CHATURTHI_DATES.get(year, CHATURTHI_DATES.get(2025))
    return {
        "status": 200,
        "data": {
            "year": year,
            "ganesh_chaturthi": {
                "date": date,
                "name": "Ganesh Chaturthi",
                "tithi": "Chaturthi, Shukla Paksha, Bhadrapada",
                "description": "Birthday of Lord Ganesha, celebrated on the 4th day of Shukla Paksha in Bhadrapada month"
            }
        }
    }


@router.post("/festival/navratri")
def navratri_dates(req: FestivalRequest):
    year = req.year
    dates = NAVRATRI_DATES.get(year, NAVRATRI_DATES.get(2025, {}))
    if req.month:
        start_month = int(dates.get("start", "2025-09-22").split("-")[1])
        if req.month != start_month:
            return {"status": 200, "data": {"year": year, "month": req.month, "navratri": None, "message": "Navratri not in this month"}}
    return {
        "status": 200,
        "data": {
            "year": year,
            "navratri": {
                "start": dates.get("start"),
                "end": dates.get("end"),
                "name": "Shardiya Navratri",
                "description": "Nine nights of Goddess Durga worship, Shukla Paksha, Ashwin month"
            }
        }
    }


@router.post("/festival/diwali")
def diwali_date(req: FestivalRequest):
    year = req.year
    date = DIWALI_DATES.get(year, DIWALI_DATES.get(2025))
    return {
        "status": 200,
        "data": {
            "year": year,
            "diwali": {
                "date": date,
                "name": "Diwali",
                "tithi": "Krishna Amavasya, Kartik month",
                "description": "Festival of lights, celebrating the return of Lord Rama and victory of light over darkness"
            }
        }
    }


@router.post("/festival/holi")
def holi_date(req: FestivalRequest):
    year = req.year
    date = HOLI_DATES.get(year, HOLI_DATES.get(2025))
    return {
        "status": 200,
        "data": {
            "year": year,
            "holi": {
                "date": date,
                "name": "Holi",
                "tithi": "Full Moon (Purnima), Phalguna month",
                "description": "Festival of colors celebrating the burning of demoness Holika and victory of good over evil"
            }
        }
    }
