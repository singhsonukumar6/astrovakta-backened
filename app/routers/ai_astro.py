from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import json
import swisseph as swe
import pytz
from ..utils import (to_julian, calc_planets, calc_houses, get_sign, get_nakshatra,
                     ZODIAC_SIGNS, SIGN_LORDS, PLANET_PROPS, planet_status)

router = APIRouter()

class BirthRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    houseSystem: Optional[str] = Field('W', example='W')
    nodeMode: Optional[str] = Field('mean', example='mean')

class ChatRequest(BaseModel):
    question: str = Field(..., example="When will I get married?")
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    houseSystem: Optional[str] = Field('W', example='W')
    nodeMode: Optional[str] = Field('mean', example='mean')
    useAI: Optional[bool] = Field(True, description="Use real AI provider for predictions")

class CompatRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    partnerDateOfBirth: str = Field(..., example="1992-08-20")
    partnerTimeOfBirth: str = Field(..., example="09:15")
    partnerLatitude: float = Field(..., example=19.0760)
    partnerLongitude: float = Field(..., example=72.8777)
    partnerTimezone: str = Field(..., example="Asia/Kolkata")
    houseSystem: Optional[str] = Field('W', example='W')
    nodeMode: Optional[str] = Field('mean', example='mean')

# ── Data ──────────────────────────────────────────────────────────────────
GEMS = {'Sun':('Ruby','authority and vitality'),'Moon':('Pearl','emotional balance'),
        'Mars':('Red Coral','courage and energy'),'Mercury':('Emerald','intelligence'),
        'Jupiter':('Yellow Sapphire','wisdom and fortune'),'Venus':('Diamond','love and luxury'),
        'Saturn':('Blue Sapphire','discipline and stability'),
        'Rahu':('Hessonite','foreign connections'),'Ketu':("Cat's Eye",'spirituality')}

_DE = {'Sun':('authority and recognition','promotions and leadership','vitality improves; bone/heart watch','respect; ego clashes','steady growth'),
       'Moon':('emotional growth and travel','nurturing and counseling roles','mental health improves; cold watch','family harmony','fluctuating but improving'),
       'Mars':('energy and property','engineering, sports, real estate','high energy; injury risk','passion; argument risk','gains through property'),
       'Rahu':('unconventional gains','tech, foreign companies','mysterious ailments possible','unconventional partnerships','sudden gains; speculation risk'),
       'Jupiter':('wisdom and wealth','teaching, law, banking','weight/liver watch','family harmony, children','strong wealth accumulation'),
       'Saturn':('discipline and karma','slow steady progress','chronic issues; joint care','maturity; possible delays','steady earnings growth'),
       'Mercury':('business and communication','trade, writing, consulting','nervous system watch','intellectual bonding','business and commission gains'),
       'Ketu':('spiritual awakening','research, healing','meditation needed','detachment themes','spiritual practice gains'),
       'Venus':('love and luxury','arts, fashion, hospitality','kidney/reproductive health','romantic fulfillment','creative venture gains')}
DASHA_EFFECTS = {k:{'theme':v[0],'career':v[1],'health':v[2],'relationships':v[3],'finance':v[4]} for k,v in _DE.items()}

INDUSTRY_MAP = {'Aries':'military, sports, engineering, entrepreneurship',
    'Taurus':'banking, music, hospitality, real estate','Gemini':'media, writing, IT, sales',
    'Cancer':'healthcare, hospitality, real estate','Leo':'entertainment, politics, fashion',
    'Virgo':'analytics, accounting, service industries','Libra':'law, art, consulting',
    'Scorpio':'research, psychology, surgery','Sagittarius':'teaching, law, travel, publishing',
    'Capricorn':'management, government, construction','Aquarius':'technology, science, social work',
    'Pisces':'healing, arts, film, pharmacy'}

# ── Helpers ───────────────────────────────────────────────────────────────
def _base(body):
    from ..main import detect_yogas, detect_doshas
    jd=to_julian(body.dateOfBirth,body.timeOfBirth,body.timezone)
    planets=calc_planets(jd,None,body.nodeMode or 'mean')
    for p in planets: p['houseStatus']=planet_status(p['name'],p['sign'])
    hd=calc_houses(jd,body.latitude,body.longitude,planets,body.houseSystem or 'W')
    return jd,planets,hd,detect_yogas(planets,hd['houses'],hd['ascendant']['sign']),detect_doshas(planets),{p['name']:p for p in planets}

def _dasha(body):
    from ..main import vimshottari_full, parse_local_datetime
    jd=to_julian(body.dateOfBirth,body.timeOfBirth,body.timezone)
    bl=parse_local_datetime(body.dateOfBirth,body.timeOfBirth,body.timezone)
    d=vimshottari_full(jd,bl)
    try:
        tz=pytz.timezone(body.timezone); today=datetime.now(tz).date().isoformat()
        cm=next((m for m in d.get('mahadashas',[]) if m['startDate']<=today<m['endDate']),None)
        if not cm: return None
        ca=next((a for a in cm.get('antardasha',[]) if a['startDate']<=today<a['endDate']),None)
        cp=next((p for p in ca.get('pratyantar',[]) if p['startDate']<=today<p['endDate']),None) if ca else None
        return {'mahadasha':cm['planet'],'mdStart':cm['startDate'],'mdEnd':cm['endDate'],
                'antardasha':ca['planet'] if ca else None,'adStart':ca['startDate'] if ca else None,
                'adEnd':ca['endDate'] if ca else None,'pratyantar':cp['planet'] if cp else None,
                'pdStart':cp['startDate'] if cp else None,'pdEnd':cp['endDate'] if cp else None}
    except: return None

def _ps(pm,n):
    p=pm.get(n)
    if not p: return f"{n} is not prominently placed."
    s=planet_status(n,p['sign']); r=" (retrograde)" if p.get('isRetrograde') else ""
    cb=" and combust" if p.get('isCombust') else ""
    return f"{n} at {p['degree']:.1f}\u00b0 in {p['sign']}{r}{cb}, House {p.get('house','?')}, dignity '{s}', {p['nakshatra']} Nakshatra (pada {p['nakshatraPada']}, lord {p['nakshatraLord']})."

def _dt(d):
    if not d: return "Current Dasha could not be determined."
    md,ad,pd=d['mahadasha'],d.get('antardasha'),d.get('pratyantar')
    eff=DASHA_EFFECTS.get(md,{'theme':'mixed results'})
    return (f"Running {md} Mahadasha ({d['mdStart']} to {d['mdEnd']})"
            +f" within {ad} Antardasha" if ad else "")+f". Theme: {eff['theme']}."

def _yb(yogas):
    if not yogas: return "No major yogas present."
    return "Yogas:\n"+"\n".join(f"  - {y['name']}: {y.get('description','')} ({y.get('strength','Active')})" for y in yogas[:6])

def _db(doshas):
    a=[d for d in doshas if d.get('present')]
    if not a: return "No significant doshas present."
    return "Doshas:\n"+"\n".join(f"  - {d['name']} ({d.get('severity','Medium')}): {d.get('description','')}" for d in a[:5])

def _transits():
    swe.set_sid_mode(swe.SIDM_LAHIRI,0,0); tz=pytz.timezone('Asia/Kolkata'); now=datetime.now(tz)
    jd=swe.julday(now.year,now.month,now.day,now.hour+now.minute/60)
    ids={'Sun':swe.SUN,'Moon':swe.MOON,'Mars':swe.MARS,'Mercury':swe.MERCURY,'Jupiter':swe.JUPITER,'Venus':swe.VENUS,'Saturn':swe.SATURN}
    parts=[]
    for n,pid in ids.items():
        xx,_=swe.calc_ut(jd,pid,swe.FLG_SIDEREAL|swe.FLG_SWIEPH|swe.FLG_SPEED)
        sg=get_sign(xx[0]); dg=xx[0]%30; rt=xx[3]<0 and n not in ('Sun','Moon')
        parts.append(f"{n}:{sg} {dg:.1f}\u00b0{'(R)' if rt else ''}")
    return "Current transits: "+", ".join(parts)+"."

def hi(pm,hs,num):
    i=num-1
    if i<0 or i>=len(hs): return None,None
    h=hs[i]; ln=SIGN_LORDS.get(h['sign']); lp=pm.get(ln) if ln else None
    return h,lp

def _snap(planets):
    return [{'name':p['name'],'sign':p['sign'],'house':p['house'],'degree':p['degree'],
             'status':planet_status(p['name'],p['sign']),'retro':p.get('isRetrograde',False)}
            for p in planets if p['name'] in ('Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu')]


def _build_chart_context(planets, hd, yogas, doshas, cur, pm):
    """Build a rich context string for AI prompts from chart data."""
    parts = []
    asc = hd['ascendant']
    parts.append(f"Ascendant: {asc['sign']} ({asc['nakshatra']}, lord {asc['nakshatraLord']})")
    parts.append(f"Moon Sign: {pm.get('Moon',{}).get('sign','?')}")
    parts.append(f"Sun Sign: {pm.get('Sun',{}).get('sign','?')}")

    parts.append("\nPlanetary Positions:")
    for p in planets:
        retro = " (R)" if p.get('isRetrograde') else ""
        combust = " (combust)" if p.get('isCombust') else ""
        status = planet_status(p['name'], p['sign'])
        parts.append(f"  {p['name']}: {p['sign']} {p['degree']:.1f}° House {p.get('house','?')} [{status}]{retro}{combust} | Nakshatra: {p.get('nakshatra','')} (pada {p.get('nakshatraPada','')}, lord {p.get('nakshatraLord','')})")

    parts.append("\nHouses:")
    for h in hd['houses']:
        parts.append(f"  House {h['number']}: {h['sign']} (lord {SIGN_LORDS.get(h['sign'],'?')}) Planets: {', '.join(h['planets']) or 'empty'}")

    if yogas:
        parts.append("\nYogas: " + ", ".join(f"{y['name']} ({y.get('strength','Active')})" for y in yogas[:10]))
    if doshas:
        active_d = [d for d in doshas if d.get('present')]
        if active_d:
            parts.append("\nActive Doshas: " + ", ".join(f"{d['name']} ({d.get('severity','Medium')})" for d in active_d))

    if cur:
        md = cur.get('mahadasha','')
        ad = cur.get('antardasha','')
        parts.append(f"\nCurrent Dasha: {md}" + (f" / {ad}" if ad else ""))

    return "\n".join(parts)


def _call_ai_provider(user_id, system_prompt, user_prompt, preferred_provider=None):
    """Call a real AI provider using the user's configured key."""
    from ..auth import get_active_ai_provider
    from ..crypto import decrypt_api_key
    import httpx

    provider_config = get_active_ai_provider(user_id, preferred_provider)
    if not provider_config:
        return None, "No AI provider configured. Add one in Dashboard \u2192 AI Providers."

    api_key = decrypt_api_key(provider_config["api_key_encrypted"])
    provider = provider_config["provider"]
    model = provider_config.get("model") or {
        "openai": "gpt-4o-mini", "anthropic": "claude-3-haiku-20240307",
        "groq": "llama-3.3-70b-versatile",
        "together": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
    }.get(provider, "gpt-4o-mini")

    endpoints = {
        "openai": "https://api.openai.com/v1/chat/completions",
        "anthropic": "https://api.anthropic.com/v1/messages",
        "groq": "https://api.groq.com/openai/v1/chat/completions",
        "together": "https://api.together.xyz/v1/chat/completions",
    }
    headers_fn = {
        "openai": lambda k: {"Authorization": f"Bearer {k}", "Content-Type": "application/json"},
        "anthropic": lambda k: {"x-api-key": k, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
        "groq": lambda k: {"Authorization": f"Bearer {k}", "Content-Type": "application/json"},
        "together": lambda k: {"Authorization": f"Bearer {k}", "Content-Type": "application/json"},
    }

    endpoint = endpoints.get(provider)
    if not endpoint:
        return None, f"Unsupported provider: {provider}"

    headers = headers_fn[provider](api_key)
    if provider == "anthropic":
        payload = {"model": model, "max_tokens": 4096, "system": system_prompt,
                   "messages": [{"role": "user", "content": user_prompt}]}
    else:
        payload = {"model": model, "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}],
            "max_tokens": 4096, "temperature": 0.7}

    with httpx.Client(timeout=90.0) as client:
        resp = client.post(endpoint, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    if provider == "anthropic":
        text = data["content"][0]["text"]
    else:
        text = data["choices"][0]["message"]["content"]

    return text, None


def _get_user_id(request):
    """Extract user_id from request state (set by middleware)."""
    if not request:
        return None
    key_info = getattr(getattr(request, 'state', None), 'api_key_info', None)
    return key_info.get('user_id') if key_info else None


AI_SYSTEM_PROMPT = (
    "You are an expert Vedic astrologer with deep knowledge of Jyotish Shastra. "
    "Provide detailed, insightful, and personalized readings based on the birth chart data. "
    "Be specific: mention planetary positions, houses, nakshatras, dasha periods, yogas, and doshas. "
    "Provide practical remedies when relevant. Use clear, accessible language. "
    "Structure your response with clear paragraphs and bullet points where appropriate."
)

# ═══════════════════════════════════════════════════════════════════════════
# 1. POST /ai/chat
# ═══════════════════════════════════════════════════════════════════════════
@router.post('/ai/chat')
def ai_chat(body: ChatRequest, request: Request = None):
    jd,planets,hd,yogas,doshas,pm=_base(body); cur=_dasha(body)
    user_id = _get_user_id(request)

    if body.useAI and user_id:
        ctx = _build_chart_context(planets, hd, yogas, doshas, cur, pm)
        user_prompt = f"Birth Chart Data:\n{ctx}\n\nQuestion: {body.question}"
        ai_text, err = _call_ai_provider(user_id, AI_SYSTEM_PROMPT, user_prompt)
        if ai_text:
            return {'status':200,'response':{'answer':ai_text,'topic':'general',
                    'source':'ai','provider':None,'question':body.question,
                    'planetsSummary':_snap(planets)}}

    q=body.question.lower(); asc=hd['ascendant']; hs=hd['houses']; P:List[str]=[]

    if any(k in q for k in ['marriage','married','spouse','wedding','partner','love']):
        h7,_=hi(pm,hs,7); ven=pm.get('Venus'); jup=pm.get('Jupiter')
        mg=next((d for d in doshas if d['name']=='Mangal Dosha' and d.get('present')),None)
        p1="Marriage is governed by the 7th house, Venus, and Jupiter."
        if h7: p1+=f" Your 7th house is {h7['sign']} (lord: {SIGN_LORDS.get(h7['sign'],'?')})"
        if h7 and h7['planets']: p1+=f" with {', '.join(h7['planets'])} influencing partnership dynamics."
        if ven: p1+=f" {_ps(pm,'Venus')}"
        P.append(p1)
        p2=""
        if jup:
            js=planet_status('Jupiter',jup['sign'])
            p2=f"Jupiter in {jup['sign']} (House {jup.get('house','?')}, {js}). "
            p2+="Strong support for timely marriage." if js in ('Exalted','Own Sign','Friendly') else "Some delays but eventual fulfillment."
        if mg:
            sv=mg.get('severity','Medium')
            p2+=f" Mangal Dosha ({sv}) present. "
            p2+="Kumbh Vivah and Hanuman Chalisa strongly recommended." if sv=='High' else "Matching with Manglik partner or remedial puja advised."
        P.append(p2 or "No significant marriage afflictions found.")
        if cur:
            md=cur['mahadasha']; eff=DASHA_EFFECTS.get(md,{}); p3=f"During {md} Mahadasha"
            if cur.get('antardasha'): p3+=f" / {cur['antardasha']} Antardasha"
            p3+=f", themes: {eff.get('theme','')}. "
            p3+="Favorable window for marriage." if md in ('Venus','Jupiter','Moon','Rahu') else "Marriage may be delayed; patience needed."
            P.append(p3)
        return {'status':200,'response':{'answer':"\n\n".join(P),'topic':'marriage',
                'planetsSummary':[{'name':p['name'],'sign':p['sign'],'house':p['house']} for p in planets if p['name'] in ('Venus','Jupiter','Mars','Saturn')]}}

    if any(k in q for k in ['career','job','work','profession','business','promotion']):
        h10,_=hi(pm,hs,10)
        P.append("Career is governed by the 10th house, Saturn, and Mercury.")
        if h10: P.append(f"Your 10th house: {h10['sign']} (lord: {SIGN_LORDS.get(h10['sign'],'?')})"
                         +f" with {', '.join(h10['planets'])}." if h10['planets'] else "")
        P.append(_ps(pm,'Saturn')); P.append(_ps(pm,'Mercury'))
        if cur: P.append(f"During {cur['mahadasha']}: {DASHA_EFFECTS.get(cur['mahadasha'],{}).get('career','')}.")
        cy=[y for y in yogas if any(k in y['name'].lower() for k in ('raja','dhana','mahapurusha','amala','bhadra','hamsa','saraswati'))]
        if cy: P.append("Career yogas: "+"; ".join(y['name'] for y in cy[:4])+".")
        return {'status':200,'response':{'answer':"\n\n".join(P),'topic':'career',
                'planetsSummary':[{'name':p['name'],'sign':p['sign'],'house':p['house']} for p in planets if p['name'] in ('Saturn','Mercury','Sun','Jupiter')]}}

    if any(k in q for k in ['health','disease','illness','wellness']):
        P.append("Health is read from the 1st house (body), 6th house (disease), and Mars.")
        P.append(_ps(pm,'Mars'))
        if cur: P.append(f"During {cur['mahadasha']}: {DASHA_EFFECTS.get(cur['mahadasha'],{}).get('health','general wellness')}.")
        return {'status':200,'response':{'answer':"\n\n".join(P),'topic':'health',
                'planetsSummary':[{'name':p['name'],'sign':p['sign'],'house':p['house']} for p in planets if p['name'] in ('Mars','Saturn','Sun','Moon')]}}

    if any(k in q for k in ['wealth','money','finance','income','rich','profit']):
        h2,_=hi(pm,hs,2); h11,_=hi(pm,hs,11)
        P.append("Wealth from 2nd (accumulation), 11th (gains), and Jupiter.")
        if h2: P.append(f"2nd house: {h2['sign']}.")
        if h11:
            P.append(f"11th house: {h11['sign']}"+f" with {', '.join(h11['planets'])}." if h11['planets'] else ".")
        P.append(_ps(pm,'Jupiter'))
        if cur: P.append(f"During {cur['mahadasha']}: {DASHA_EFFECTS.get(cur['mahadasha'],{}).get('finance','mixed')}.")
        wy=[y for y in yogas if 'dhana' in y['name'].lower() or 'lakshmi' in y['name'].lower()]
        if wy: P.append("Wealth yogas: "+"; ".join(y['name'] for y in wy)+".")
        return {'status':200,'response':{'answer':"\n\n".join(P),'topic':'wealth',
                'planetsSummary':[{'name':p['name'],'sign':p['sign'],'house':p['house']} for p in planets if p['name'] in ('Jupiter','Venus','Saturn')]}}

    P.append(f"Ascendant: {asc['sign']} ({asc['nakshatra']}, lord {asc['nakshatraLord']}).")
    P.append(_ps(pm,'Sun')); P.append(_ps(pm,'Moon'))
    if cur: P.append(_dt(cur))
    P.append(_yb(yogas)); P.append(_db(doshas))
    return {'status':200,'response':{'answer':"\n\n".join(P),'topic':'general','question':body.question,'planetsSummary':_snap(planets)}}

# ═══════════════════════════════════════════════════════════════════════════
# 2. POST /ai/kundli-interpretation
# ═══════════════════════════════════════════════════════════════════════════
@router.post('/ai/kundli-interpretation')
def ai_kundli_interpretation(body: BirthRequest, request: Request = None):
    jd,planets,hd,yogas,doshas,pm=_base(body); cur=_dasha(body)
    user_id = _get_user_id(request)
    asc=hd['ascendant']; hs=hd['houses']

    ps=[{'name':p['name'],'sign':p['sign'],'house':p['house'],'degree':round(p['degree'],2),
         'status':planet_status(p['name'],p['sign']),'retro':p.get('isRetrograde',False)}
        for p in planets if p['name'] in ('Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu')]
    hs2=[{'house':h['number'],'sign':h['sign'],'lord':SIGN_LORDS.get(h['sign']),'planets':h['planets']} for h in hs]

    if user_id:
        ctx = _build_chart_context(planets, hd, yogas, doshas, cur, pm)
        system_prompt = AI_SYSTEM_PROMPT + (
            "\nProvide a comprehensive kundli interpretation covering: "
            "1) Personality & Character, 2) Career & Professional Life, "
            "3) Relationships & Marriage, 4) Wealth & Finances, "
            "5) Health & Wellness, 6) Spiritual Inclinations. "
            "Be detailed and specific to this chart."
        )
        user_prompt = f"Full Birth Chart Data:\n{ctx}\n\nProvide a complete kundli interpretation."
        ai_text, err = _call_ai_provider(user_id, system_prompt, user_prompt)
        if ai_text:
            return {'status':200,'response':{'interpretation':ai_text,'source':'ai',
                    'ascendant':asc,'moonSign':pm.get('Moon',{}).get('sign'),
                    'sunSign':pm.get('Sun',{}).get('sign'),
                    'planets':ps,'houses':hs2,
                    'yogas':[{'name':y['name'],'description':y.get('description','')} for y in yogas],
                    'doshas':[{'name':d['name'],'present':d.get('present'),'severity':d.get('severity')} for d in doshas],
                    'currentDasha':cur}}

    P:List[str]=[]
    h1,_=hi(pm,hs,1)
    p=f"PERSONALITY: Ascendant {asc['sign']} ({asc['nakshatra']}, lord {asc['nakshatraLord']})."
    if h1 and h1['planets']: p+=f" Planets {', '.join(h1['planets'])} in 1st house shape self-expression."
    p+=f" {_ps(pm,'Sun')} {_ps(pm,'Moon')}"
    P.append(p)

    h10,_=hi(pm,hs,10); tl_name=SIGN_LORDS.get(h10['sign']) if h10 else None; tl=pm.get(tl_name) if tl_name else None
    c="CAREER: "
    if h10: c+=f"10th house in {h10['sign']} (lord: {tl_name})"
    if h10 and h10['planets']: c+=f" with {', '.join(h10['planets'])}."
    c+=f" {_ps(pm,'Saturn')}"
    if tl:
        ts=planet_status(tl_name,tl['sign'])
        c+=f" 10th lord {tl_name} in {tl['sign']} ({ts}). "
        c+="Excellent for career success." if ts in ('Exalted','Own Sign','Mooltrikona') else "Steady career growth through effort."
    P.append(c)

    h7,_=hi(pm,hs,7); r="RELATIONSHIPS: "
    if h7: r+=f"7th house: {h7['sign']}"
    if h7 and h7['planets']: r+=f" with {', '.join(h7['planets'])}."
    r+=f" {_ps(pm,'Venus')}"
    vs=planet_status('Venus',pm.get('Venus',{}).get('sign',''))
    r+=" Harmonious relationships indicated." if vs in ('Exalted','Own Sign') else " Conscious effort in relationships needed." if vs=='Debilitated' else " Generally positive."
    P.append(r)

    h2,_=hi(pm,hs,2); h11,_=hi(pm,hs,11); w="WEALTH: "
    if h2: w+=f"2nd house: {h2['sign']}."
    if h11: w+=f" 11th house: {h11['sign']}"
    if h11 and h11['planets']: w+=f" with {', '.join(h11['planets'])} indicating income sources."
    w+=f" {_ps(pm,'Jupiter')}"
    js=planet_status('Jupiter',pm.get('Jupiter',{}).get('sign',''))
    w+=" Strong wealth support." if js in ('Exalted','Own Sign','Friendly') else " Wealth through wisdom."
    P.append(w)

    h6,_=hi(pm,hs,6); he="HEALTH: "
    if h1: he+=f"1st house: {h1['sign']}."
    if h6: he+=f" 6th house: {h6['sign']}."
    he+=f" {_ps(pm,'Mars')}"
    ms=planet_status('Mars',pm.get('Mars',{}).get('sign',''))
    he+=" Strong vitality." if ms=='Exalted' else " Vulnerability to inflammation." if ms=='Debilitated' else " Moderate energy."
    P.append(he)

    h9,_=hi(pm,hs,9); h12,_=hi(pm,hs,12); s="SPIRITUALITY: "
    if h9: s+=f"9th house: {h9['sign']}"
    if h9 and h9['planets']: s+=f" with {', '.join(h9['planets'])}."
    if h12: s+=f" 12th house: {h12['sign']}"
    if h12 and h12['planets']: s+=f" with {', '.join(h12['planets'])}."
    s+=f" {_ps(pm,'Ketu')}"
    P.append(s)
    P.append(_yb(yogas)); P.append(_db(doshas))
    if cur: P.append(_dt(cur))

    return {'status':200,'response':{'interpretation':"\n\n".join(P),'source':'rule-based',
            'ascendant':asc,'moonSign':pm.get('Moon',{}).get('sign'),'sunSign':pm.get('Sun',{}).get('sign'),
            'planets':ps,'houses':hs2,
            'yogas':[{'name':y['name'],'description':y.get('description','')} for y in yogas],
            'doshas':[{'name':d['name'],'present':d.get('present'),'severity':d.get('severity')} for d in doshas],
            'currentDasha':cur}}

# ═══════════════════════════════════════════════════════════════════════════
# 3. POST /ai/horoscope-generation
# ═══════════════════════════════════════════════════════════════════════════
@router.post('/ai/horoscope-generation')
def ai_horoscope_generation(body: BirthRequest, request: Request = None):
    jd,planets,hd,yogas,doshas,pm=_base(body); cur=_dasha(body)
    user_id = _get_user_id(request)
    ms=pm.get('Moon',{}).get('sign','?'); asc=hd['ascendant']; hs=hd['houses']

    if user_id:
        ctx = _build_chart_context(planets, hd, yogas, doshas, cur, pm)
        transits = _transits()
        system_prompt = AI_SYSTEM_PROMPT + (
            "\nGenerate a detailed current horoscope prediction based on natal chart and transits. "
            "Cover career, finance, health, relationships, and spiritual outlook."
        )
        user_prompt = f"Natal Chart:\n{ctx}\n\nCurrent Transits: {transits}\n\nGenerate a detailed horoscope prediction."
        ai_text, err = _call_ai_provider(user_id, system_prompt, user_prompt)
        if ai_text:
            return {'status':200,'response':{'horoscope':ai_text,'source':'ai','moonSign':ms,'ascendant':asc,
                    'currentDasha':cur,'currentTransits':transits}}

    P:List[str]=[]
    P.append(f"Moon sign: {ms}. Ascendant: {asc['sign']}. Generated from natal chart + current transits.")
    P.append(_transits())
    if cur:
        md=cur['mahadasha']; ad=cur.get('antardasha'); eff=DASHA_EFFECTS.get(md,{})
        P.append(f"Vimshottari: {md} Mahadasha"+(f" / {ad} Antardasha" if ad else "")+f". Theme: {eff.get('theme','')}.")

    themes=[]
    for num in (1,2,5,7,10):
        h,_=hi(pm,hs,num)
        if h and h['planets']:
            themes.append(f"House {num} activated ({', '.join(h['planets'])}).")
    if themes: P.append("Key areas: "+" ".join(themes))

    ven=pm.get('Venus'); jup=pm.get('Jupiter')
    adv=""
    if ven: adv+=f"Venus in {ven['sign']} favors arts and social connections. "
    if jup: adv+=f"Jupiter in {jup['sign']} supports learning and spiritual practices."
    if adv: P.append(adv)
    P.append(_yb(yogas))

    return {'status':200,'response':{'horoscope':"\n\n".join(P),'source':'rule-based','moonSign':ms,'ascendant':asc,
            'currentDasha':cur,
            'planetsInHouses':{str(h['number']):h['planets'] for h in hs if h['planets']},
            'yogasPresent':[y['name'] for y in yogas],
            'doshasPresent':[d['name'] for d in doshas if d.get('present')],
            'currentTransits':_transits()}}

# ═══════════════════════════════════════════════════════════════════════════
# 4. POST /ai/remedies
# ═══════════════════════════════════════════════════════════════════════════
@router.post('/ai/remedies')
def ai_remedies(body: BirthRequest, request: Request = None):
    jd,planets,hd,yogas,doshas,pm=_base(body); hs=hd['houses']
    user_id = _get_user_id(request)

    if user_id:
        ctx = _build_chart_context(planets, hd, yogas, doshas, _dasha(body), pm)
        system_prompt = AI_SYSTEM_PROMPT + (
            "\nProvide detailed, personalized remedies for this birth chart. "
            "Include: 1) Dosha-specific remedies, 2) Planet strengthening mantras and rituals, "
            "3) Gemstone recommendations with wearing instructions, 4) Charity and donation suggestions, "
            "5) Spiritual practices and meditation guidance. Be specific to this chart's afflictions."
        )
        user_prompt = f"Birth Chart Data:\n{ctx}\n\nProvide comprehensive remedies and guidance."
        ai_text, err = _call_ai_provider(user_id, system_prompt, user_prompt)
        if ai_text:
            aff=[]
            for pn in ('Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'):
                pd=pm.get(pn)
                if pd and planet_status(pn,pd['sign']) in ('Debilitated','Enemy'):
                    aff.append({'name':pn,'sign':pd['sign'],'status':planet_status(pn,pd['sign']),'house':pd.get('house')})
            return {'status':200,'response':{'remedies':ai_text,'source':'ai',
                    'doshaRemedies':[{'dosha':d['name'],'severity':d.get('severity'),'remedies':d.get('remedies',[])}
                                     for d in doshas if d.get('present') and d.get('remedies')],
                    'afflictedPlanets':aff}}

    P:List[str]=[]
    P.append("Tailored remedies based on your birth chart analysis.")
    for d in [d for d in doshas if d.get('present') and d.get('remedies')]:
        P.append(f"{d['name']} ({d.get('severity','Medium')}): {', '.join(d.get('remedies',[])[:3])}.")
    aff=[]
    for pn in ('Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'):
        pd=pm.get(pn)
        if pd and planet_status(pn,pd['sign']) in ('Debilitated','Enemy'):
            gn,gp=GEMS.get(pn,('Unknown',''))
            P.append(f"{pn} debilitated in {pd['sign']} (House {pd.get('house','?')}). "
                     f"Wear {gn}, chant {pn} mantra 108x daily, donate {pn}-related items on {pn}-ruled days.")
            aff.append({'name':pn,'sign':pd['sign'],'status':planet_status(pn,pd['sign']),'house':pd.get('house')})
    for num in (1,4,7,10):
        h,_=hi(pm,hs,num)
        if h and h['planets']:
            mf=[pn for pn in h['planets'] if pn in ('Saturn','Mars','Rahu','Ketu')]
            if mf: P.append(f"Malefic {', '.join(mf)} in {num}th house: propitiate through regular prayers.")
    neg=[y for y in yogas if y.get('strength')=='Malefic']
    for y in neg: P.append(f"Mitigate {y['name']}: regular spiritual practice advised.")
    P.append("General: Mahamrityunjaya Mantra, Shiva temple Mondays, feed animals, donate on auspicious days, meditate daily.")
    return {'status':200,'response':{'remedies':"\n\n".join(P),'source':'rule-based',
            'doshaRemedies':[{'dosha':d['name'],'severity':d.get('severity'),'remedies':d.get('remedies',[])}
                             for d in doshas if d.get('present') and d.get('remedies')],
            'afflictedPlanets':aff}}

# ═══════════════════════════════════════════════════════════════════════════
# 5. POST /ai/prediction
# ═══════════════════════════════════════════════════════════════════════════
@router.post('/ai/prediction')
def ai_prediction(body: BirthRequest, request: Request = None):
    jd,planets,hd,yogas,doshas,pm=_base(body); cur=_dasha(body); hs=hd['houses']
    user_id = _get_user_id(request)

    if user_id and cur:
        ctx = _build_chart_context(planets, hd, yogas, doshas, cur, pm)
        system_prompt = AI_SYSTEM_PROMPT + (
            "\nProvide detailed dasha-based predictions. For each area (career, health, relationships, finance), "
            "give specific timing of events, favorable periods, and challenges. "
            "Include antardasha and pratyantar dasha analysis where possible."
        )
        user_prompt = f"Birth Chart Data:\n{ctx}\n\nProvide detailed dasha-based predictions for all life areas."
        ai_text, err = _call_ai_provider(user_id, system_prompt, user_prompt)
        if ai_text:
            return {'status':200,'response':{'prediction':ai_text,'source':'ai','currentDasha':cur,
                    'planetsInKeyHouses':{'1st':hs[0]['planets'] if hs else [],'7th':hs[6]['planets'] if len(hs)>6 else [],'10th':hs[9]['planets'] if len(hs)>9 else []}}}

    if not cur:
        return {'status':200,'response':{'prediction':"Current Dasha could not be determined.",
                'currentDasha':None,'planetsInKeyHouses':{}}}

    md,ad,pd=cur['mahadasha'],cur.get('antardasha'),cur.get('pratyantar')
    eff=DASHA_EFFECTS.get(md,{})
    P:List[str]=[]
    P.append(f"PREDICTIONS FOR {md} MAHADASHA ({cur['mdStart']} to {cur['mdEnd']})"
             +(f" | {ad} Antardasha ({cur['adStart']} to {cur['adEnd']})" if ad else "")
             +(" | {pd} Pratyantar" if pd else "")+".")
    P.append(f"Overall theme: {eff.get('theme','mixed results')}.")
    h10,_=hi(pm,hs,10)
    cp=f"CAREER: {eff.get('career','')}. "
    if h10 and h10['planets']: cp+=f"10th house planets {', '.join(h10['planets'])} influence professional outcomes."
    P.append(cp)
    P.append(f"HEALTH: {eff.get('health','')}.")
    h7,_=hi(pm,hs,7)
    rp=f"RELATIONSHIPS: {eff.get('relationships','')}. "
    if h7 and h7['planets']: rp+=f"7th house planets {', '.join(h7['planets'])} shape partnership themes."
    P.append(rp)
    h2,_=hi(pm,hs,2); h11,_=hi(pm,hs,11)
    fp=f"FINANCE: {eff.get('finance','')}. "
    if h11 and h11['planets']: fp+=f"11th house planets {', '.join(h11['planets'])} indicate income channels."
    P.append(fp)
    pos_y=[y for y in yogas if y.get('strength') in ('Strong','Very Strong')]
    if pos_y: P.append("Supporting yogas: "+"; ".join(y['name'] for y in pos_y[:3])+".")
    if ad:
        ae=DASHA_EFFECTS.get(ad,{})
        P.append(f"Antardasha ({ad}) adds: {ae.get('theme','')}. Career: {ae.get('career','')}. Health: {ae.get('health','')}.")
    return {'status':200,'response':{'prediction':"\n\n".join(P),'source':'rule-based','currentDasha':cur,
            'planetsInKeyHouses':{'1st':hs[0]['planets'] if hs else [],'7th':hs[6]['planets'] if len(hs)>6 else [],'10th':hs[9]['planets'] if len(hs)>9 else []}}}

# ═══════════════════════════════════════════════════════════════════════════
# 6. POST /ai/gemstone-advisor
# ═══════════════════════════════════════════════════════════════════════════
@router.post('/ai/gemstone-advisor')
def ai_gemstone_advisor(body: BirthRequest, request: Request = None):
    jd,planets,hd,yogas,doshas,pm=_base(body)
    user_id = _get_user_id(request)
    asc=hd['ascendant']; al=SIGN_LORDS.get(asc['sign'],'Sun')
    ml=SIGN_LORDS.get(pm.get('Moon',{}).get('sign',''),'')

    if user_id:
        ctx = _build_chart_context(planets, hd, yogas, doshas, _dasha(body), pm)
        system_prompt = AI_SYSTEM_PROMPT + (
            "\nProvide detailed gemstone recommendations based on this birth chart. "
            "Include: primary gemstone, secondary gemstone, remedial gemstones, "
            "wearing instructions (metal, finger, weight, day, time), and benefits of each. "
            "Also mention alternatives if natural stones are not available."
        )
        user_prompt = f"Birth Chart Data:\n{ctx}\n\nProvide comprehensive gemstone recommendations."
        ai_text, err = _call_ai_provider(user_id, system_prompt, user_prompt)
        if ai_text:
            pg,pp=GEMS.get(al,('Unknown','general well-being'))
            return {'status':200,'response':{'recommendations':ai_text,'source':'ai',
                    'primaryRecommendation':{'planet':al,'gemstone':pg,'reason':f'Ascendant lord ({asc["sign"]})'},
                    'secondaryRecommendation':{'planet':ml,'gemstone':GEMS.get(ml,(None,None))[0]} if ml and ml!=al and GEMS.get(ml) else None,
                    'allGemstones':[{'planet':p,'gemstone':g[0]} for p,g in GEMS.items()]}}

    P:List[str]=[]
    P.append(f"GEMSTONE RECOMMENDATIONS\nAscendant: {asc['sign']} (lord: {al}). Moon sign: {pm.get('Moon',{}).get('sign','?')} (lord: {ml}).")
    pg,pp=GEMS.get(al,('Unknown','general well-being'))
    p=f"PRIMARY: {pg} (for {al}). "
    p+=f"As lord of {asc['sign']}, {al} strengthens your life force, enhancing {pp}. "
    ast=planet_status(al,asc['sign'])
    p+=f"Current dignity: {ast}. "
    p+="Amplifies existing strength." if ast in ('Exalted','Own Sign','Mooltrikona') else "Especially important to counteract weakness." if ast=='Debilitated' else "Optimizes its influence."
    P.append(p)
    if ml and ml!=al:
        sg,sp=GEMS.get(ml,(None,None))
        if sg: P.append(f"SECONDARY: {sg} (for {ml}). Supports emotional well-being, {sp}. Dignity: {planet_status(ml,pm.get('Moon',{}).get('sign',''))}.")
    for pn in ('Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'):
        pd=pm.get(pn)
        if pd and planet_status(pn,pd['sign']) in ('Debilitated','Enemy'):
            gn,_=GEMS.get(pn,(None,None))
            if gn: P.append(f"REMEDIAL: {gn} (for {pn}) \u2014 {pn} in {pd['sign']} ({planet_status(pn,pd['sign'])}); mitigates negative effects.")
    return {'status':200,'response':{'recommendations':"\n\n".join(P),'source':'rule-based',
            'primaryRecommendation':{'planet':al,'gemstone':pg,'reason':f'Ascendant lord ({asc["sign"]})'},
            'secondaryRecommendation':{'planet':ml,'gemstone':GEMS.get(ml,(None,None))[0]} if ml and ml!=al and GEMS.get(ml) else None,
            'allGemstones':[{'planet':p,'gemstone':g[0]} for p,g in GEMS.items()]}}

# ═══════════════════════════════════════════════════════════════════════════
# 7. POST /ai/career-analysis
# ═══════════════════════════════════════════════════════════════════════════
@router.post('/ai/career-analysis')
def ai_career_analysis(body: BirthRequest, request: Request = None):
    jd,planets,hd,yogas,doshas,pm=_base(body); cur=_dasha(body); hs=hd['houses']; asc=hd['ascendant']
    user_id = _get_user_id(request)

    h10,_=hi(pm,hs,10); tl_name=SIGN_LORDS.get(h10['sign']) if h10 else None; tl=pm.get(tl_name) if tl_name else None
    sat=pm.get('Saturn')

    if user_id:
        ctx = _build_chart_context(planets, hd, yogas, doshas, cur, pm)
        system_prompt = AI_SYSTEM_PROMPT + (
            "\nProvide a detailed career analysis based on this birth chart. Cover: "
            "1) Natural career aptitudes based on 10th house, its lord, and strong planets, "
            "2) Best industries and professions for this person, "
            "3) Leadership style and management approach, "
            "4) Timing of career breakthroughs and challenges based on dasha periods, "
            "5) Business vs job potential, "
            "6) Specific years for promotions or job changes."
        )
        user_prompt = f"Birth Chart Data:\n{ctx}\n\nProvide a comprehensive career analysis."
        ai_text, err = _call_ai_provider(user_id, system_prompt, user_prompt)
        if ai_text:
            cy=[y for y in yogas if any(k in y['name'].lower() for k in ('raja','dhana','mahapurusha','amala','bhadra','hamsa','saraswati','lakshmi'))]
            return {'status':200,'response':{'careerAnalysis':ai_text,'source':'ai','tenthHouse':h10,
                    'tenthLord':{'planet':tl_name,'sign':tl['sign'],'house':tl.get('house'),'status':planet_status(tl_name,tl['sign'])} if tl else None,
                    'saturnPosition':{'sign':sat['sign'],'house':sat.get('house'),'status':planet_status('Saturn',sat['sign'])} if sat else None,
                    'careerYogas':[{'name':y['name'],'description':y.get('description','')} for y in cy],'currentDasha':cur}}

    P:List[str]=[]
    P.append(f"CAREER ANALYSIS\nAscendant: {asc['sign']}. Focus: 10th house, its lord, Saturn, Mercury.")
    if h10:
        P.append(f"10th house: {h10['sign']} (lord: {tl_name})"
                 +f" with {', '.join(h10['planets'])}." if h10['planets'] else ".")
    if tl:
        ts=planet_status(tl_name,tl['sign'])
        tl_p=f"10th lord {tl_name} in {tl['sign']} (House {tl.get('house','?')}, {ts}). "
        tl_p+="Excellent for career recognition." if ts in ('Exalted','Own Sign','Mooltrikona') else "Career challenges require persistence." if ts=='Debilitated' else "Cooperative career growth."
        P.append(tl_p)
    if h10: P.append(f"Suitable industries: {INDUSTRY_MAP.get(h10['sign'],'various fields')}.")
    if sat:
        sh=sat.get('house','?'); ss=planet_status('Saturn',sat['sign'])
        ls=f"Leadership: Saturn in {sat['sign']} (House {sh}, {ss}). "
        if sh in (1,10): ls+="Authoritative leadership with responsibility."
        elif sh in (4,7): ls+="Patient leadership building stable foundations."
        elif sh in (3,6,11): ls+="Leading through persistence and empowering others."
        else: ls+="Structured yet adaptable style."
        P.append(ls)
    cy=[y for y in yogas if any(k in y['name'].lower() for k in ('raja','dhana','mahapurusha','amala','bhadra','hamsa','saraswati','lakshmi'))]
    if cy: P.append("Career yogas: "+"; ".join(f"{y['name']} ({y.get('strength','Active')})" for y in cy[:5])+".")
    if cur: P.append(_dt(cur))
    return {'status':200,'response':{'careerAnalysis':"\n\n".join(P),'source':'rule-based','tenthHouse':h10,
            'tenthLord':{'planet':tl_name,'sign':tl['sign'],'house':tl.get('house'),'status':planet_status(tl_name,tl['sign'])} if tl else None,
            'saturnPosition':{'sign':sat['sign'],'house':sat.get('house'),'status':planet_status('Saturn',sat['sign'])} if sat else None,
            'careerYogas':[{'name':y['name'],'description':y.get('description','')} for y in cy],'currentDasha':cur}}

# ═══════════════════════════════════════════════════════════════════════════
# 8. POST /ai/marriage-analysis
# ═══════════════════════════════════════════════════════════════════════════
@router.post('/ai/marriage-analysis')
def ai_marriage_analysis(body: CompatRequest, request: Request = None):
    from ..main import detect_doshas
    user_id = _get_user_id(request)

    jd1=to_julian(body.dateOfBirth,body.timeOfBirth,body.timezone)
    p1=calc_planets(jd1,None,body.nodeMode or 'mean')
    for p in p1: p['houseStatus']=planet_status(p['name'],p['sign'])
    hd1=calc_houses(jd1,body.latitude,body.longitude,p1,body.houseSystem or 'W')
    d1=detect_doshas(p1); pm1={p['name']:p for p in p1}
    jd2=to_julian(body.partnerDateOfBirth,body.partnerTimeOfBirth,body.partnerTimezone)
    p2=calc_planets(jd2,None,body.nodeMode or 'mean')
    for p in p2: p['houseStatus']=planet_status(p['name'],p['sign'])
    hd2=calc_houses(jd2,body.partnerLatitude,body.partnerLongitude,p2,body.houseSystem or 'W')
    d2=detect_doshas(p2); pm2={p['name']:p for p in p2}
    a1,a2=hd1['ascendant'],hd2['ascendant']
    m1,m2=pm1.get('Moon',{}).get('sign','?'),pm2.get('Moon',{}).get('sign','?')
    v1,v2=pm1.get('Venus'),pm2.get('Venus')
    mg1=next((d for d in d1 if d['name']=='Mangal Dosha' and d.get('present')),None)
    mg2=next((d for d in d2 if d['name']=='Mangal Dosha' and d.get('present')),None)

    if user_id:
        ctx1 = _build_chart_context(p1, hd1, [], d1, None, pm1)
        ctx2 = _build_chart_context(p2, hd2, [], d2, None, pm2)
        system_prompt = AI_SYSTEM_PROMPT + (
            "\nProvide a detailed marriage compatibility analysis between these two people. "
            "Cover: 1) Emotional and mental compatibility, 2) Physical attraction and chemistry, "
            "3) Financial compatibility, 4) Family harmony potential, 5) Mangal Dosha impact, "
            "6) Timing of marriage if applicable, 7) Overall compatibility score and advice."
        )
        user_prompt = f"Person 1 Chart:\n{ctx1}\n\nPerson 2 Chart:\n{ctx2}\n\nProvide detailed marriage compatibility analysis."
        ai_text, err = _call_ai_provider(user_id, system_prompt, user_prompt)
        if ai_text:
            mi1=ZODIAC_SIGNS.index(m1) if m1 in ZODIAC_SIGNS else 0
            mi2=ZODIAC_SIGNS.index(m2) if m2 in ZODIAC_SIGNS else 0
            diff=(mi2-mi1)%12
            return {'status':200,'response':{'compatibilityAnalysis':ai_text,'source':'ai',
                    'person1':{'ascendant':a1['sign'],'moonSign':m1},
                    'person2':{'ascendant':a2['sign'],'moonSign':m2},
                    'moonCompatibility':('EXCELLENT' if diff==0 else 'GOOD' if diff in (4,6,8) else 'CHALLENGING' if diff in (2,10) else 'MODERATE')}}

    P:List[str]=[]
    P.append(f"MARRIAGE COMPATIBILITY\nPerson 1: Asc {a1['sign']}, Moon {m1}.\nPerson 2: Asc {a2['sign']}, Moon {m2}.")
    mi1=ZODIAC_SIGNS.index(m1) if m1 in ZODIAC_SIGNS else 0
    mi2=ZODIAC_SIGNS.index(m2) if m2 in ZODIAC_SIGNS else 0
    diff=(mi2-mi1)%12
    if diff in (0,4,6,8):
        P.append(f"Moon compatibility: {'EXCELLENT' if diff==0 else 'GOOD'} \u2014 {diff} signs apart, {'strong harmony' if diff==0 else 'complementary energies'}.")
    elif diff in (2,10):
        P.append(f"Moon compatibility: CHALLENGING \u2014 {diff} signs apart, conscious communication needed.")
    else:
        P.append(f"Moon compatibility: MODERATE \u2014 {diff} signs apart, mixed but workable.")
    if v1 and v2:
        P.append(f"Venus: P1 {v1['sign']} ({planet_status('Venus',v1['sign'])}) | P2 {v2['sign']} ({planet_status('Venus',v2['sign'])}).")
    if mg1 and mg2: P.append("Mangal Dosha: Both have it \u2014 effects neutralize, favorable.")
    elif mg1: P.append(f"P1 has Mangal Dosha ({mg1.get('severity','Medium')}). Remedies recommended.")
    elif mg2: P.append(f"P2 has Mangal Dosha ({mg2.get('severity','Medium')}). Remedies recommended.")
    else: P.append("Mangal Dosha: Neither has it \u2014 very favorable for harmony.")
    h71=hd1['houses'][6] if len(hd1['houses'])>6 else None
    h72=hd2['houses'][6] if len(hd2['houses'])>6 else None
    if h71 and h72:
        l1,l2=SIGN_LORDS.get(h71['sign'],'?'),SIGN_LORDS.get(h72['sign'],'?')
        P.append(f"7th house: P1 {h71['sign']} (lord {l1})"+(f" [{', '.join(h71['planets'])}]" if h71['planets'] else "")
                 +f" | P2 {h72['sign']} (lord {l2})"+(f" [{', '.join(h72['planets'])}]" if h72['planets'] else "")+".")
    gn={'Sun':'Deva','Moon':'Manushya','Mars':'Rakshasa','Mercury':'Deva','Jupiter':'Deva','Venus':'Manushya','Saturn':'Rakshasa','Rahu':'Rakshasa','Ketu':'Manushya'}
    g1=gn.get(pm1.get('Moon',{}).get('nakshatraLord',''),'?')
    g2=gn.get(pm2.get('Moon',{}).get('nakshatraLord',''),'?')
    P.append(f"Gana: P1 {g1} | P2 {g2}. "+("Deva-Deva: spiritual harmony." if g1==g2=='Deva' else "Mixed gana: growth opportunities."))
    pos=[]; chal=[]
    if diff in (0,4,6,8): pos.append("Moon compatibility")
    else: chal.append("Moon distance")
    if (mg1 and mg2) or (not mg1 and not mg2): pos.append("Mangal status")
    else: chal.append("Mangal imbalance")
    P.append(f"Summary: Positive: {', '.join(pos) or 'None specific'}. Challenges: {', '.join(chal) or 'None specific'}.")
    return {'status':200,'response':{'compatibilityAnalysis':"\n\n".join(P),'source':'rule-based',
            'person1':{'ascendant':a1['sign'],'moonSign':m1,'seventhHouse':h71,
                       'mangalDosha':{'present':bool(mg1),'severity':mg1.get('severity') if mg1 else None}},
            'person2':{'ascendant':a2['sign'],'moonSign':m2,'seventhHouse':h72,
                       'mangalDosha':{'present':bool(mg2),'severity':mg2.get('severity') if mg2 else None}},
            'moonCompatibility':('EXCELLENT' if diff==0 else 'GOOD' if diff in (4,6,8) else 'CHALLENGING' if diff in (2,10) else 'MODERATE')}}
