from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


router = APIRouter()


class BirthRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    houseSystem: Optional[str] = Field('W', example='W')
    nodeMode: Optional[str] = Field('mean', example='mean')


class BookingRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    poojaName: str = Field(..., example="Mangal Dosh Nivaran Puja")
    preferredDate: Optional[str] = Field(None, example="2026-08-15")
    preferredTime: Optional[str] = Field(None, example="09:00")
    name: str = Field(..., example="Rahul Sharma")
    phone: str = Field(..., example="+919876543210")
    email: Optional[str] = Field(None, example="rahul@example.com")


class AvailabilityRequest(BaseModel):
    poojaName: Optional[str] = Field(None, example="Mangal Dosh Nivaran Puja")
    date: str = Field(..., example="2026-08-15")
    location: Optional[str] = Field(None, example="Varanasi")


PUJA_DATABASE = {
    'Mangal Dosha': {
        'name': 'Mangal Dosh Nivaran Puja',
        'description': 'Special puja to neutralize the malefic effects of Mars in chart. Recommended for marriage harmony.',
        'duration': '2-3 hours',
        'bestDay': 'Tuesday',
        'bestDeity': 'Lord Hanuman',
        'materials': ['Red flowers', 'Red cloth', 'Durva grass', 'Laddu', 'Sindoor'],
        'mantra': 'Om Ang Angarakaya Namaha',
        'cost': '₹5,100 - ₹21,000',
    },
    'Kaal Sarp Dosha': {
        'name': 'Kaal Sarp Dosh Nivaran Puja',
        'description': 'Puja to pacify Rahu-Ketu axis affliction. Performed at Trimbakeshwar or Ujjain.',
        'duration': '4-5 hours',
        'bestDay': 'Any auspicious day',
        'bestDeity': 'Lord Shiva',
        'materials': ['Rudraksha', 'Sacred thread', 'Flowers', 'Bilva leaves'],
        'mantra': 'Om Namah Shivaya',
        'cost': '₹11,000 - ₹51,000',
    },
    'Shani Dosha': {
        'name': 'Shani Dosh Nivaran Puja',
        'description': 'Puja to mitigate Saturn affliction. Helps in reducing delays and obstacles.',
        'duration': '2-3 hours',
        'bestDay': 'Saturday',
        'bestDeity': 'Lord Shani / Lord Hanuman',
        'materials': ['Black sesame', 'Mustard oil', 'Iron nails', 'Black cloth'],
        'mantra': 'Om Sham Shanaishcharaya Namaha',
        'cost': '₹3,100 - ₹11,000',
    },
    'Pitra Dosha': {
        'name': 'Pitra Dosh Nivaran Puja',
        'description': 'Puja to appease ancestors and remove ancestral karma. Important for family peace.',
        'duration': '3-4 hours',
        'bestDay': 'Amavasya or Pitru Paksha',
        'bestDeity': 'Lord Vishnu / Ancestors',
        'materials': ['Til (sesame)', 'Water', 'Flowers', 'Food for Brahmins'],
        'mantra': 'Om Pitrabhyah Swadha Namah',
        'cost': '₹5,100 - ₹21,000',
    },
    'Guru Chandal Dosha': {
        'name': 'Guru Chandal Dosh Nivaran Puja',
        'description': 'Puja to reduce Jupiter-Rahu confusion. Restores wisdom and right judgment.',
        'duration': '2-3 hours',
        'bestDay': 'Thursday',
        'bestDeity': 'Lord Vishnu',
        'materials': ['Yellow flowers', 'Chana dal', 'Turmeric', 'Yellow cloth'],
        'mantra': 'Om Namo Bhagavate Vasudevaya',
        'cost': '₹3,100 - ₹11,000',
    },
    'Kemadruma Dosha': {
        'name': 'Chandra Dosh Nivaran Puja',
        'description': 'Puja to strengthen Moon and reduce emotional instability.',
        'duration': '2 hours',
        'bestDay': 'Monday',
        'bestDeity': 'Lord Shiva',
        'materials': ['White flowers', 'Rice', 'Milk', 'Sugar'],
        'mantra': 'Om Chandraya Namaha',
        'cost': '₹2,100 - ₹7,100',
    },
    'General': {
        'name': 'Graha Shanti Puja',
        'description': 'General peace puja for all planets. Good for overall well-being.',
        'duration': '2-3 hours',
        'bestDay': 'Any auspicious day',
        'bestDeity': 'Lord Vishnu / Navagraha',
        'materials': ['Flowers', 'Fruits', 'Incense', 'Ghee lamp'],
        'mantra': 'Om Navagraha Devatabhyo Namaha',
        'cost': '₹3,100 - ₹11,000',
    },
}

PLANET_TEMPLES = {
    'Sun': {'name': 'Surya Temple, Konark', 'location': 'Odisha, India', 'speciality': 'Sun temple with architectural marvel'},
    'Moon': {'name': 'Somnath Temple', 'location': 'Gujarat, India', 'speciality': 'One of 12 Jyotirlingas'},
    'Mars': {'name': 'Hanuman Temple, Jaipur', 'location': 'Rajasthan, India', 'speciality': 'Powerful Mars remedies'},
    'Mercury': {'name': 'Dashashwamedh Ghat', 'location': 'Varanasi, India', 'speciality': 'Mercury strengthening'},
    'Jupiter': {'name': 'Banke Bihari Temple', 'location': 'Vrindavan, India', 'speciality': 'Jupiter blessings'},
    'Venus': {'name': 'Lakshmi Narayan Temple', 'location': 'Jaipur, India', 'speciality': 'Venus and luxury blessings'},
    'Saturn': {'name': 'Shani Shingnapur', 'location': 'Maharashtra, India', 'speciality': 'Most powerful Saturn temple'},
    'Rahu': {'name': 'Rahu Temple, Tirunageswaram', 'location': 'Tamil Nadu, India', 'speciality': 'Rahu Kala remedies'},
    'Ketu': {'name': 'Ketu Temple, Alangudi', 'location': 'Tamil Nadu, India', 'speciality': 'Ketu dosha nivaran'},
}


@router.post('/pooja/recommendation')
def pooja_recommendation(body: BirthRequest):
    from ..main import to_julian, calc_planets, calc_houses, detect_doshas, planet_status
    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets = calc_planets(jd, None, body.nodeMode or 'mean')
    calc_houses(jd, body.latitude, body.longitude, planets, body.houseSystem or 'W')
    doshas = detect_doshas(planets)
    pmap = {p['name']: p for p in planets}

    active_doshas = [d for d in doshas if d.get('present')]
    recommendations = []

    for d in active_doshas:
        dosha_name = d['name']
        mapped_key = None
        for key in PUJA_DATABASE:
            if key.lower() in dosha_name.lower():
                mapped_key = key
                break
        if not mapped_key:
            mapped_key = 'General'
        pooja = PUJA_DATABASE[mapped_key].copy()
        pooja['forDosha'] = dosha_name
        pooja['severity'] = d.get('severity', 'Medium')
        recommendations.append(pooja)

    if not recommendations:
        recommendations.append({
            **PUJA_DATABASE['General'],
            'forDosha': 'General well-being',
            'severity': 'None',
        })

    afflicted = []
    for pname in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
        p = pmap.get(pname)
        if p and planet_status(pname, p['sign']) in ['Debilitated', 'Enemy']:
            afflicted.append({'planet': pname, 'status': planet_status(pname, p['sign'])})
            pooja = PUJA_DATABASE['General'].copy()
            pooja['forDosha'] = f'{pname} is {planet_status(pname, p["sign"])}'
            pooja['name'] = f'{pname} Graha Shanti Puja'
            recommendations.append(pooja)

    return {
        'status': 200,
        'data': {
            'recommendations': recommendations,
            'activeDoshas': [{'name': d['name'], 'severity': d.get('severity')} for d in active_doshas],
            'afflictedPlanets': afflicted,
        },
    }


@router.post('/pooja/temple')
def temple_recommendation(body: BirthRequest):
    from ..main import to_julian, calc_planets, calc_houses, planet_status
    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets = calc_planets(jd, None, body.nodeMode or 'mean')
    calc_houses(jd, body.latitude, body.longitude, planets, body.houseSystem or 'W')
    pmap = {p['name']: p for p in planets}

    weakest_planet = None
    weakest_status = None
    for pname in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
        p = pmap.get(pname)
        if p:
            st = planet_status(pname, p['sign'])
            if st in ['Debilitated', 'Enemy']:
                weakest_planet = pname
                weakest_status = st
                break

    primary_temple = PLANET_TEMPLES.get(weakest_planet or 'Sun', PLANET_TEMPLES['Sun'])
    all_recommendations = []
    if weakest_planet and weakest_planet in PLANET_TEMPLES:
        all_recommendations.append({
            'planet': weakest_planet, 'status': weakest_status,
            **PLANET_TEMPLES[weakest_planet],
        })

    for pname in ['Sun', 'Jupiter', 'Venus', 'Saturn']:
        p = pmap.get(pname)
        if p and pname in PLANET_TEMPLES:
            st = planet_status(pname, p['sign'])
            if st == 'Exalted':
                all_recommendations.append({'planet': pname, 'status': st, **PLANET_TEMPLES[pname]})

    return {
        'status': 200,
        'data': {
            'primaryTemple': {'planet': weakest_planet, **primary_temple} if weakest_planet else PLANET_TEMPLES['Sun'],
            'allRecommendations': all_recommendations if all_recommendations else [{'planet': 'General', **PLANET_TEMPLES['Sun']}],
        },
    }


@router.post('/pooja/sankalp')
def sankalp_details(body: BirthRequest):
    from ..main import to_julian, calc_planets, calc_houses, get_nakshatra
    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets = calc_planets(jd, None, body.nodeMode or 'mean')
    calc_houses(jd, body.latitude, body.longitude, planets, body.houseSystem or 'W')
    moon = next((p for p in planets if p['name'] == 'Moon'), None)
    nk = get_nakshatra(moon['longitude']) if moon else {'name': 'Unknown', 'pada': 1}

    return {
        'status': 200,
        'data': {
            'sankalp': {
                'birthDate': body.dateOfBirth,
                'birthTime': body.timeOfBirth,
                'birthPlace': f'{body.latitude}, {body.longitude}',
                'moonNakshatra': nk['name'],
                'moonNakshatraPada': nk['pada'],
                'moonSign': moon['sign'] if moon else None,
                'gotra': 'To be filled by pandit',
                'sankalpText': f"Om Shri Ganeshaya Namah. I, [Name], born on {body.dateOfBirth} at {body.timeOfBirth} in nakshatra {nk['name']} pada {nk['pada']}, rashi {moon['sign'] if moon else 'N/A'}, perform this puja for [intention].",
                'instructions': [
                    'Fill in your name and gotra before the puja',
                    'Mention the specific intention (sankalp) for the puja',
                    'Keep a clean and pure environment during the puja',
                    'Face east or north during the puja',
                ],
            },
        },
    }


@router.post('/pooja/booking')
def pooja_booking(body: BookingRequest):
    booking_id = f"PJ-{body.dateOfBirth.replace('-', '')}-{body.name[:3].upper()}"
    return {
        'status': 200,
        'data': {
            'note': 'Booking system integration pending',
            'bookingId': booking_id,
            'status': 'pending_confirmation',
            'poojaName': body.poojaName,
            'preferredDate': body.preferredDate,
            'preferredTime': body.preferredTime,
            'devotee': {
                'name': body.name,
                'phone': body.phone,
                'email': body.email,
            },
            'nextSteps': [
                'Our team will contact you within 24 hours',
                'Confirmation of date and pandit will be sent via SMS/email',
                'Please keep birth details ready for sankalp',
            ],
        },
    }


@router.post('/pooja/availability')
def pooja_availability(body: AvailabilityRequest):
    slots = [
        {'time': '06:00 - 08:00', 'status': 'available', 'pandit': 'Pandit Ramesh Sharma'},
        {'time': '09:00 - 11:00', 'status': 'available', 'pandit': 'Pandit Vijay Mishra'},
        {'time': '12:00 - 14:00', 'status': 'limited', 'pandit': 'Pandit Suresh Upadhyay'},
        {'time': '16:00 - 18:00', 'status': 'available', 'pandit': 'Pandit Anil Joshi'},
    ]

    return {
        'status': 200,
        'data': {
            'note': 'Availability system integration pending',
            'date': body.date,
            'poojaName': body.poojaName or 'General Puja',
            'location': body.location or 'Online',
            'availableSlots': slots,
            'totalAvailable': sum(1 for s in slots if s['status'] == 'available'),
        },
    }
