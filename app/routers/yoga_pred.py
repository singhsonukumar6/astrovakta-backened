from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from ..utils import (
    to_julian, calc_planets, calc_houses, get_sign, get_nakshatra,
    ZODIAC_SIGNS, SIGN_LORDS, PLANET_PROPS, planet_status,
)

router = APIRouter()


class YogaPredRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    houseSystem: Optional[str] = Field('W', example='W')
    nodeMode: Optional[str] = Field('mean', example='mean')


class YogaDetailedRequest(YogaPredRequest):
    yogaName: str = Field(..., example="Gajakesari Yoga")


YOGA_PREDICTIONS = {
    'Ruchaka Yoga (Mahapurusha)': {
        'description': 'Mars in own sign (Aries/Scorpio) or exalted sign (Capricorn) in a kendra house (1/4/7/10). One of the five Pancha Mahapurusha yogas.',
        'planets': ['Mars'],
        'housesAffected': [1, 4, 7, 10],
        'lifeAreas': ['career', 'authority', 'courage', 'leadership'],
        'prediction': 'Ruchaka Yoga bestows a commanding personality with natural authority and courage. The native excels in military, police, sports, surgery, or any field requiring boldness. They possess strong willpower, sharp features, and a charismatic leadership presence. Political success and respect from authorities are common outcomes.',
        'strengthGuide': {
            'strong': 'Mars exalted in Capricorn in kendra — maximum martial power, unshakeable authority.',
            'moderate': 'Mars in own sign in kendra — solid courage and leadership with some limitations.',
            'weak': 'Mars in own sign but in dusthana or combust — benefits reduced, courage present but poorly directed.',
        },
        'timing': 'Activates during Mars Mahadasha or Antardasha periods.',
        'remedies': [
            'Mangal Puja on Tuesdays',
            'Hanuman Chalisa recitation',
            'Donate red lentils (masoor dal) on Tuesdays',
            'Wear red coral after proper consultation',
            'Tuesday fasting',
        ],
    },
    'Bhadra Yoga (Mahapurusha)': {
        'description': 'Mercury in own sign (Gemini/Virgo) or exalted sign (Virgo) in a kendra house. One of the Pancha Mahapurusha yogas.',
        'planets': ['Mercury'],
        'housesAffected': [1, 4, 7, 10],
        'lifeAreas': ['intelligence', 'education', 'commerce', 'communication'],
        'prediction': 'Bhadra Yoga grants exceptional intelligence, eloquence, and learning. The native becomes a skilled communicator, scholar, accountant, or businessperson. They have a strong memory, analytical mind, and talent for languages. Success in education, writing, media, and trade is assured.',
        'strengthGuide': {
            'strong': 'Mercury exalted in Virgo in kendra — extraordinary intellectual and commercial prowess.',
            'moderate': 'Mercury in Gemini/Virgo in kendra — strong intelligence and communication skills.',
            'weak': 'Mercury in own sign but combust or in dusthana — intellect present but underutilized.',
        },
        'timing': 'Activates during Mercury Mahadasha or Antardasha periods.',
        'remedies': [
            'Chant Budh Mantra on Wednesdays',
            'Donate green moong dal on Wednesdays',
            'Wear emerald after proper consultation',
            'Study and promote education',
            'Wednesday fasting with green foods',
        ],
    },
    'Hamsa Yoga (Mahapurusha)': {
        'description': 'Jupiter in own sign (Sagittarius/Pisces) or exalted sign (Cancer) in a kendra house. One of the Pancha Mahapurusha yogas.',
        'planets': ['Jupiter'],
        'housesAffected': [1, 4, 7, 10],
        'lifeAreas': ['wisdom', 'spirituality', 'wealth', 'children', 'fortune'],
        'prediction': 'Hamsa Yoga confers wisdom, spiritual depth, noble character, and good fortune. The native is naturally inclined toward dharmic living, teaching, and counseling. They enjoy prosperity, blessed children, and respect from learned communities. Jupiter\'s expansive energy brings optimism and moral authority.',
        'strengthGuide': {
            'strong': 'Jupiter exalted in Cancer in kendra — immense wisdom, wealth, spiritual leadership.',
            'moderate': 'Jupiter in Sagittarius/Pisces in kendra — strong fortune and philosophical bent.',
            'weak': 'Jupiter in own sign but combust or weak — wisdom present but not fully manifested.',
        },
        'timing': 'Activates during Jupiter Mahadasha or Antardasha periods.',
        'remedies': [
            'Thursday fasting',
            'Chant Guru Beej Mantra',
            'Donate yellow gram (chana dal) on Thursdays',
            'Wear yellow sapphire after proper consultation',
            'Teach underprivileged students',
        ],
    },
    'Malavya Yoga (Mahapurusha)': {
        'description': 'Venus in own sign (Taurus/Libra) or exalted sign (Pisces) in a kendra house. One of the Pancha Mahapurusha yogas.',
        'planets': ['Venus'],
        'housesAffected': [1, 4, 7, 10],
        'lifeAreas': ['art', 'beauty', 'luxury', 'marriage', 'comfort', 'creativity'],
        'prediction': 'Malavya Yoga blesses the native with beauty, artistic talent, luxury, and harmonious relationships. They have a refined aesthetic sense and enjoy comforts, fine art, music, and fashion. Marriage is typically prosperous and幸福. Success in arts, entertainment, luxury goods, and hospitality is indicated.',
        'strengthGuide': {
            'strong': 'Venus exalted in Pisces in kendra — extraordinary beauty, artistic mastery, abundant luxury.',
            'moderate': 'Venus in Taurus/Libra in kendra — strong artistic sense and comfortable life.',
            'weak': 'Venus in own sign but combust or afflicted — aesthetic sense present but compromised.',
        },
        'timing': 'Activates during Venus Mahadasha or Antardasha periods.',
        'remedies': [
            'Friday fasting with white foods',
            'Chant Shukra Mantra',
            'Donate white sweets or clothes on Fridays',
            'Wear diamond or white sapphire after proper consultation',
            'Support arts and women\'s welfare',
        ],
    },
    'Shasha Yoga (Mahapurusha)': {
        'description': 'Saturn in own sign (Capricorn/Aquarius) or exalted sign (Libra) in a kendra house. One of the Pancha Mahapurusha yogas.',
        'planets': ['Saturn'],
        'housesAffected': [1, 4, 7, 10],
        'lifeAreas': ['authority', 'discipline', 'patience', 'service', 'longevity', 'management'],
        'prediction': 'Shasha Yoga produces a powerful, disciplined leader with excellent management skills. The native rises to positions of authority through perseverance and hard work. They excel in governance, administration, mining, oil, iron, and large organizations. Despite initial delays, they achieve lasting power and respect.',
        'strengthGuide': {
            'strong': 'Saturn exalted in Libra in kendra — immense authority, political power, disciplined success.',
            'moderate': 'Saturn in Capricorn/Aquarius in kendra — strong management and leadership qualities.',
            'weak': 'Saturn in own sign but combust or in dusthana — discipline present but authority delayed.',
        },
        'timing': 'Activates during Saturn Mahadasha or Antardasha periods.',
        'remedies': [
            'Saturday fasting',
            'Chant Shani Mantra (Om Sham Shanaishcharaya Namaha)',
            'Donate black sesame, mustard oil on Saturdays',
            'Wear blue sapphire after thorough testing',
            'Serve elderly and disabled people',
        ],
    },
    'Gajakesari Yoga': {
        'description': 'Jupiter and Moon in mutual kendra (1/4/7/10 from each other). One of the most auspicious and powerful yogas in Vedic astrology.',
        'planets': ['Jupiter', 'Moon'],
        'housesAffected': [1, 4, 7, 10],
        'lifeAreas': ['wisdom', 'wealth', 'reputation', 'fortune', 'emotional intelligence', 'public standing'],
        'prediction': 'Gajakesari Yoga is among the most celebrated yogas, indicating wisdom, lasting wealth, and unshakeable reputation. The native possesses great learning, eloquence, and moral character. They are respected scholars, leaders, or spiritual figures. The name "Gajakesari" (elephant-lion) suggests one who combines the strength of an elephant with the courage of a lion. Wealth and fame endure across generations.',
        'strengthGuide': {
            'strong': 'Both Jupiter and Moon in kendras, Jupiter in exaltation or own sign — legendary wisdom and fortune.',
            'moderate': 'Jupiter and Moon in kendras with moderate dignity — strong intelligence and prosperity.',
            'weak': 'Jupiter or Moon debilitated or combust — benefits reduced but learning still prominent.',
        },
        'timing': 'Activates during Jupiter or Moon Mahadasha/Antardasha periods.',
        'remedies': [
            'Thursday and Monday fasting',
            'Chant Guru and Chandra mantras',
            'Donate yellow and white foods on Thursdays and Mondays',
            'Worship Lord Vishnu and Lord Shiva',
            'Study and teach sacred texts',
        ],
    },
    'Budha Aditya Yoga': {
        'description': 'Sun and Mercury in conjunction in the same sign. A natural combination of intelligence and authority.',
        'planets': ['Sun', 'Mercury'],
        'housesAffected': [],
        'lifeAreas': ['intelligence', 'government favor', 'communication', 'analytical ability', 'career'],
        'prediction': 'Budha Aditya Yoga combines the Sun\'s authority with Mercury\'s intelligence, creating a sharp analytical mind with government or institutional favor. The native excels in administration, law, banking, accounting, and communication fields. They possess strong logical reasoning, eloquence, and the ability to influence authority figures. The combination is especially powerful when both planets are not combust.',
        'strengthGuide': {
            'strong': 'Both planets in strong dignity, not combust, in kendra or trikona — exceptional intelligence and official success.',
            'moderate': 'Conjunction in neutral houses, mild dignity — good analytical skills, moderate career success.',
            'weak': 'Mercury combust, or both in dusthana — intelligence present but may be overshadowed by the Sun.',
        },
        'timing': 'Activates during Sun or Mercury Mahadasha/Antardasha periods.',
        'remedies': [
            'Sunday fasting for Sun',
            'Chant Aditya Hridayam',
            'Donate wheat on Sundays',
            'Avoid ego clashes with authority',
            'Respect father figures and mentors',
        ],
    },
    'Chandra Mangala Yoga': {
        'description': 'Moon and Mars in conjunction, or mutual aspect. A combination of emotional strength and earning power.',
        'planets': ['Moon', 'Mars'],
        'housesAffected': [],
        'lifeAreas': ['wealth', 'courage', 'emotional strength', 'earning ability', 'bold action'],
        'prediction': 'Chandra Mangala Yoga merges Moon\'s emotional sensitivity with Mars\'s dynamic energy, creating a person with strong earning ability and bold decision-making. The native is financially independent, courageous, and assertive. They excel in business, real estate, agriculture, and fields requiring emotional intelligence combined with physical or strategic action. Wealth comes through one\'s own efforts and courage.',
        'strengthGuide': {
            'strong': 'Both planets in strong dignity, in kendra or trikona — exceptional earning power and bold personality.',
            'moderate': 'Conjunction in neutral houses — good financial ability with some emotional turbulence.',
            'weak': 'Moon debilitated (Scorpio) or Mars debilitated (Cancer) — emotional volatility may reduce benefits.',
        },
        'timing': 'Activates during Moon or Mars Mahadasha/Antardasha periods.',
        'remedies': [
            'Monday and Tuesday fasting',
            'Chant Chandra and Mangal mantras',
            'Donate rice on Mondays, red lentils on Tuesdays',
            'Control anger through meditation',
            'Wear pearl or red coral after proper consultation',
        ],
    },
    'Neecha Bhanga Raja Yoga': {
        'description': 'Cancellation of a planet\'s debilitation through specific conditions — the debilitated planet\'s lord being exalted, in own sign, or in kendra from the ascendant.',
        'planets': ['Various'],
        'housesAffected': [],
        'lifeAreas': ['resilience', 'comeback', 'authority', 'overcoming adversity', 'transformation'],
        'prediction': 'Neecha Bhanga Raja Yoga turns weakness into strength. While the native faces initial setbacks and humbling experiences, they eventually rise to positions of unexpected power and recognition. This yoga teaches resilience — the person who falls lowest often rises highest. It is especially powerful in political and public life, where overcoming adversity becomes the foundation of authority.',
        'strengthGuide': {
            'strong': 'Debilitated planet\'s dispositor is exalted — powerful reversal of fortune.',
            'moderate': 'Debilitated planet\'s dispositor in own sign — solid comeback with sustained success.',
            'weak': 'Cancellation condition weak or afflicted — partial relief, slower recovery.',
        },
        'timing': 'Activates when the debilitated planet\'s dasha or the dispositor\'s dasha arrives.',
        'remedies': [
            'Strengthen the debilitated planet through specific mantras',
            'Respect and serve people from whom you initially felt humbled',
            'Practice gratitude for early challenges',
            'Donate to charities related to the debilitated planet',
            'Chant the beej mantra of the debilitated planet',
        ],
    },
    'Amala Yoga': {
        'description': 'Jupiter or Venus in the 1st or 4th house from the ascendant — natural virtue and lasting good fortune.',
        'planets': ['Jupiter', 'Venus'],
        'housesAffected': [1, 4],
        'lifeAreas': ['character', 'virtue', 'home', 'happiness', 'good fortune', 'reputation'],
        'prediction': 'Amala Yoga (meaning "pure" or "virtuous") grants the native an inherently good character and lasting fortune. When Jupiter occupies the 1st or 4th, the person is naturally dharmic, generous, and wise. When Venus occupies these houses, they are artistic, compassionate, and attract beauty and comfort. The 4th house placement specifically blesses the home environment and mother\'s influence.',
        'strengthGuide': {
            'strong': 'Jupiter/Venus exalted or in own sign in 1st or 4th — exceptional virtue and abundant fortune.',
            'moderate': 'Planet in own sign in 1st or 4th — strong moral character and consistent good luck.',
            'weak': 'Planet afflicted or combust in these houses — virtue present but tested by challenges.',
        },
        'timing': 'Activates during Jupiter or Venus Mahadasha/Antardasha periods.',
        'remedies': [
            'Maintain moral integrity in all dealings',
            'Donate to educational or artistic causes',
            'Chant the planet\'s mantra regularly',
            'Practice charity without expectation of return',
            'Nurture a positive home environment',
        ],
    },
    'Kemadruma Yoga': {
        'description': 'No planets in the 2nd or 12th house from the Moon — indicates emotional challenges and need for self-reliance.',
        'planets': ['Moon'],
        'housesAffected': [],
        'lifeAreas': ['emotional health', 'self-reliance', 'mental peace', 'stability'],
        'prediction': 'Kemadruma Yoga creates emotional isolation and challenges in finding support from family or close associates. The native must develop self-reliance and inner strength. While initial life may feel lonely or unsupported, this yoga can produce remarkably independent and resilient individuals who achieve through sheer self-effort. Mental health practices and spiritual discipline become essential coping mechanisms.',
        'strengthGuide': {
            'strong': 'Moon debilitated with Kemadruma — significant emotional and financial challenges, need for strong remedies.',
            'moderate': 'Moon in neutral sign — moderate emotional challenges, manageable with self-discipline.',
            'weak': 'Moon in own sign/exaltation — Kemadruma effects reduced, self-reliance easier to achieve.',
        },
        'timing': 'Effects are persistent but intensify during Moon Mahadasha or Antardasha periods.',
        'remedies': [
            'Monday fasting and Chandra Puja',
            'Worship Lord Shiva on Mondays',
            'Donate white sweets on Mondays',
            'Practice meditation and mindfulness',
            'Maintain close friendships and community ties',
            'Wear pearl after proper consultation',
        ],
    },
    'Dhana Yoga': {
        'description': 'Lords of wealth houses (2nd, 5th, 9th, 11th) in favorable positions, or Jupiter-Venus/Sun combination in kendra/trikona.',
        'planets': ['Jupiter', 'Venus', 'Sun'],
        'housesAffected': [1, 2, 5, 9, 11],
        'lifeAreas': ['wealth', 'financial prosperity', 'inheritance', 'speculation', 'fortune'],
        'prediction': 'Dhana Yoga is a powerful indicator of financial prosperity and material abundance. The native accumulates wealth through multiple sources — career earnings, investments, inheritance, or business. Jupiter\'s expansive nature combined with Venus\'s luxury or Sun\'s authority in favorable houses creates lasting financial security. The person often becomes a lender, investor, or wealth manager for others.',
        'strengthGuide': {
            'strong': 'Multiple dhana yogas present with planets in exaltation or own sign — exceptional wealth accumulation.',
            'moderate': 'One or two dhana yogas with moderate dignity — comfortable financial life with periodic growth.',
            'weak': 'Yoga present but planets afflicted — wealth comes but with instability or delays.',
        },
        'timing': 'Activates during Jupiter or Venus Mahadasha/Antardasha periods, or dasha of the wealth house lords.',
        'remedies': [
            'Thursday and Friday fasting',
            'Donate to temples and educational institutions',
            'Chant Kubera Mantra for wealth accumulation',
            'Practice ethical financial management',
            'Wear yellow sapphire or diamond after proper consultation',
        ],
    },
    'Raja Yoga': {
        'description': 'Lords of kendras and trikonas (or functional benefics) in mutual association — the supreme indicator of power, authority, and success.',
        'planets': ['Various'],
        'housesAffected': [1, 4, 5, 7, 9, 10],
        'lifeAreas': ['power', 'authority', 'political success', 'status', 'career pinnacle', 'fame'],
        'prediction': 'Raja Yoga is the most sought-after yoga in Vedic astrology, conferring royal status, political power, and extraordinary success. The native rises to positions of supreme authority — as a leader, executive, judge, minister, or head of an organization. This yoga operates through the connection of kendra (power) and trikona (fortune) lords. The specific nature of the Raja Yoga depends on which planets are involved.',
        'strengthGuide': {
            'strong': 'Multiple Raja Yogas with exalted or own-sign planets — extraordinary power and lasting legacy.',
            'moderate': 'One Raja Yoga with planets in friendly or own signs — significant success with some limitations.',
            'weak': 'Raja Yoga with afflicted or combust planets — power present but unstable or short-lived.',
        },
        'timing': 'Activates during the dasha of the planets forming the Raja Yoga.',
        'remedies': [
            'Maintain humility despite success',
            'Serve the community through your position of power',
            'Chant the dasha planet\'s mantra',
            'Practice ethical governance and leadership',
            'Strengthen weak planets through appropriate gemstones',
        ],
    },
    'Viparita Raja Yoga': {
        'description': 'Lords of dusthana houses (6/8/12) placed in other dusthana houses — adversity transforms into unexpected success.',
        'planets': ['Various'],
        'housesAffected': [6, 8, 12],
        'lifeAreas': ['overcoming enemies', 'victory in litigation', 'foreign success', 'transformation through hardship'],
        'prediction': 'Viparita Raja Yoga is a paradox — it brings success through defeat, wealth through loss, and power through adversity. The native often faces significant early challenges that ultimately become the foundation of their success. They excel in competitive environments, litigation, healing, foreign lands, and crisis management. The "Viparita" (reversed) nature means conventional obstacles become stepping stones.',
        'strengthGuide': {
            'strong': 'Two or more dusthana lords in other dusthanes with dignity — powerful reversal of adversity.',
            'moderate': 'One dusthana lord exchange — moderate benefits from challenges.',
            'weak': 'Condition partially met or planets afflicted — some benefits but mostly challenging.',
        },
        'timing': 'Activates during the dasha of the dusthana lords involved.',
        'remedies': [
            'Embrace challenges as opportunities',
            'Serve in hospitals, prisons, or crisis centers',
            'Practice detachment from outcomes',
            'Chant Mahamrityunjaya Mantra',
            'Help those in legal or medical difficulties',
        ],
    },
    'Lakshmi Yoga': {
        'description': 'Venus in a trikona (1/5/9) and Saturn in a kendra (1/4/7/10) — divine wealth and luxury blessing.',
        'planets': ['Venus', 'Saturn'],
        'housesAffected': [1, 4, 5, 7, 9, 10],
        'lifeAreas': ['divine wealth', 'luxury', 'abundance', 'beauty', 'art', 'material comfort'],
        'prediction': 'Lakshmi Yoga invokes the blessings of Goddess Lakshmi, granting the native exceptional wealth, beauty, and material comfort. Venus in trikona provides artistic and luxurious inclinations, while Saturn in kendra provides the discipline and structure to maintain and grow wealth. The native often accumulates property, vehicles, jewelry, and financial assets through persistent effort combined with aesthetic sense.',
        'strengthGuide': {
            'strong': 'Venus exalted in trikona, Saturn in own sign/exaltation in kendra — immense wealth and luxury.',
            'moderate': 'Both planets in own or friendly signs — comfortable wealth and aesthetic life.',
            'weak': 'Either planet debilitated or afflicted — wealth present but with restrictions.',
        },
        'timing': 'Activates during Venus or Saturn Mahadasha/Antardasha periods.',
        'remedies': [
            'Friday and Saturday worship',
            'Chant Mahalakshmi Mantra',
            'Donate to women\'s welfare and education',
            'Maintain ethical wealth practices',
            'Wear diamond or blue sapphire after proper consultation',
        ],
    },
    'Saraswati Yoga': {
        'description': 'Jupiter, Venus, and Mercury all in kendra or trikona — the combination of wisdom, arts, and knowledge.',
        'planets': ['Jupiter', 'Venus', 'Mercury'],
        'housesAffected': [1, 4, 5, 7, 9, 10],
        'lifeAreas': ['knowledge', 'arts', 'education', 'music', 'literature', 'eloquence', 'creativity'],
        'prediction': 'Saraswati Yoga invokes the blessings of Goddess Saraswati, the deity of knowledge, music, and arts. The native possesses exceptional intellectual and artistic abilities. They excel as scholars, musicians, writers, educators, and creative professionals. Jupiter provides philosophical depth, Venus provides aesthetic beauty, and Mercury provides analytical precision — together creating a polymath with mastery across multiple intellectual domains.',
        'strengthGuide': {
            'strong': 'All three planets exalted or in own signs in kendra/trikona — legendary creative and intellectual成就.',
            'moderate': 'All three in kendra/trikona with moderate dignity — strong artistic and intellectual abilities.',
            'weak': 'One or more planets combust or afflicted — intellectual abilities present but less manifest.',
        },
        'timing': 'Activates during Jupiter, Venus, or Mercury Mahadasha/Antardasha periods.',
        'remedies': [
            'Study and teach music or sacred texts',
            'Donate books and educational materials',
            'Chant Saraswati Mantra',
            'Practice and promote the arts',
            'Wednesday, Thursday, and Friday worship',
        ],
    },
    'Shubhakartari Yoga': {
        'description': 'Benefic planets (Jupiter, Venus, Mercury, Moon) flanking a planet or the ascendant in adjacent houses — creates an auspicious boundary.',
        'planets': ['Jupiter', 'Venus', 'Mercury', 'Moon'],
        'housesAffected': [],
        'lifeAreas': ['auspiciousness', 'protection', 'good fortune', 'positive environment'],
        'prediction': 'Shubhakartari Yoga ("auspicious saw") creates a protective and beneficial influence by having benefic planets on either side of a key position. The native enjoys a generally favorable life environment with protection from major adversities. Good fortune seems to surround them naturally, and they attract helpful people and opportunities. This yoga amplifies the benefits of whatever house or planet it surrounds.',
        'strengthGuide': {
            'strong': 'Multiple strong benefics flanking the ascendant or a key planet — exceptional protection and fortune.',
            'moderate': 'Two benefics in adjacent houses — solid auspiciousness and positive environment.',
            'weak': 'Only one benefic or benefics in weak dignity — mild positive influence.',
        },
        'timing': 'Effects are generally persistent but intensify during benefic planet dashas.',
        'remedies': [
            'Maintain positive relationships with neighbors and community',
            'Practice gratitude for fortunate circumstances',
            'Strengthen benefic planets through mantras',
            'Create a positive and harmonious home environment',
            'Help those less fortunate',
        ],
    },
    'Guru Chandal Yoga': {
        'description': 'Jupiter and Rahu in conjunction or same house — creates confusion in wisdom and unconventional spiritual paths.',
        'planets': ['Jupiter', 'Rahu'],
        'housesAffected': [],
        'lifeAreas': ['wisdom', 'spirituality', 'education', 'foreign connections', 'unconventional paths'],
        'prediction': 'Guru Chandal Yoga combines Jupiter\'s wisdom with Rahu\'s unconventional energy, creating a complex spiritual and intellectual dynamic. The native may follow unorthodox educational or spiritual paths, question established traditions, and seek truth through unconventional means. While this can cause confusion and rebellion against authority, it also creates innovative thinkers who challenge established paradigms. Success comes through embracing uniqueness rather than conforming.',
        'strengthGuide': {
            'strong': 'Jupiter exalted with Rahu — powerful unconventional wisdom, potential for breakthroughs.',
            'moderate': 'Jupiter in own sign with Rahu — strong intellectual rebellion with some grounding.',
            'weak': 'Jupiter debilitated with Rahu — significant confusion, need for careful guidance.',
        },
        'timing': 'Activates during Jupiter or Rahu Mahadasha/Antardasha periods.',
        'remedies': [
            'Thursday fasting and Vishnu Sahasranama',
            'Seek guidance from authentic spiritual teachers',
            'Practice meditation to clarify the mind',
            'Avoid blind faith or cult-like following',
            'Balance tradition with innovation',
        ],
    },
    'Vasumad Yoga': {
        'description': 'Jupiter and Venus in different trikona houses (1/5/9) — wealth, property, and family happiness.',
        'planets': ['Jupiter', 'Venus'],
        'housesAffected': [1, 5, 9],
        'lifeAreas': ['wealth', 'property', 'family happiness', 'spiritual growth', 'fortune'],
        'prediction': 'Vasumad Yoga (meaning "wealth-giving") combines Jupiter\'s fortune with Venus\'s luxury in the most auspicious trikona houses. The native enjoys substantial property ownership, family harmony, and material comfort. Jupiter provides philosophical and spiritual wealth while Venus adds beauty and comfort. The different trikona placements ensure wealth flows from multiple sources and life areas.',
        'strengthGuide': {
            'strong': 'Both planets exalted or in own signs in trikonas — exceptional wealth and family fortune.',
            'moderate': 'Both in friendly signs in trikonas — comfortable wealth and harmonious family life.',
            'weak': 'Either planet debilitated or afflicted — wealth present but with family or philosophical tensions.',
        },
        'timing': 'Activates during Jupiter or Venus Mahadasha/Antardasha periods.',
        'remedies': [
            'Thursday and Friday worship',
            'Donate to family welfare causes',
            'Chant Wealth Mantras',
            'Maintain family harmony through regular gatherings',
            'Invest in property and long-term assets',
        ],
    },
    'Daridra Yoga': {
        'description': 'Lords of 2nd and 12th houses both in dusthana houses (6/8/12) — indicates financial challenges and need for careful planning.',
        'planets': ['Various'],
        'housesAffected': [2, 6, 8, 12],
        'lifeAreas': ['financial challenges', 'expenditure', 'losses', 'material difficulties'],
        'prediction': 'Daridra Yoga indicates financial struggles and challenges in accumulating wealth. The native may face unexpected expenses, losses, or difficulty in maintaining financial stability. However, this yoga also teaches financial discipline and the value of money. With proper remedies and planning, the effects can be significantly reduced. Many successful people have this yoga and use it as motivation for financial discipline.',
        'strengthGuide': {
            'strong': 'Both 2nd and 12th lords in 8th house — significant financial challenges requiring immediate attention.',
            'moderate': 'One lord in 6th, other in 12th — moderate financial ups and downs.',
            'weak': 'Lords partially afflicted — mild financial challenges manageable with planning.',
        },
        'timing': 'Effects intensify during the dasha of 2nd or 12th house lords.',
        'remedies': [
            'Strict budgeting and financial planning',
            'Avoid speculative investments',
            'Donate to charity regularly (gives反向 returns)',
            'Chant Kubera and Lakshmi mantras',
            'Wear gemstones for wealth planets after proper consultation',
            'Start savings from a young age',
        ],
    },
    'Pancha Mangala Yoga': {
        'description': 'Three or more benefic planets (Jupiter, Venus, Mercury, Moon) in kendra houses — exceptionally auspicious and virtuous.',
        'planets': ['Jupiter', 'Venus', 'Mercury', 'Moon'],
        'housesAffected': [1, 4, 7, 10],
        'lifeAreas': ['virtue', 'prosperity', 'happiness', 'auspiciousness', 'family fortune'],
        'prediction': 'Pancha Mangala Yoga is an extremely auspicious combination indicating a life blessed with virtue, prosperity, and happiness. Multiple benefics in kendra houses create a powerful shield of positivity around the native. They enjoy good health, loving relationships, financial comfort, and spiritual contentment. This yoga often indicates someone who is naturally generous, kind, and beloved by their community.',
        'strengthGuide': {
            'strong': 'Four benefics in kendras, all dignified — extraordinarily blessed life with minimal obstacles.',
            'moderate': 'Three benefics in kendras — very fortunate with strong positive influences.',
            'weak': 'Three benefics but some combust — benefits present but partially reduced.',
        },
        'timing': 'Effects are generally persistent throughout life, intensifying during benefic dashas.',
        'remedies': [
            'Maintain virtuous living to amplify benefits',
            'Donate to spiritual and educational causes',
            'Practice regular worship and meditation',
            'Share good fortune with community',
            'Chant benefic planet mantras regularly',
        ],
    },
    'Chandala Yoga': {
        'description': 'Jupiter and Ketu in conjunction — spiritual detachment that may cause withdrawal from worldly pursuits.',
        'planets': ['Jupiter', 'Ketu'],
        'housesAffected': [],
        'lifeAreas': ['spirituality', 'detachment', 'renunciation', 'occult knowledge', 'past life karma'],
        'prediction': 'Chandala Yoga combines Jupiter\'s wisdom with Ketu\'s moksha-karaka nature, creating a strong pull toward spiritual detachment and renunciation. The native may lose interest in material pursuits prematurely, or may pursue occult and mystical knowledge intensely. While this can cause worldly difficulties, it also creates genuine spiritual seekers and healers. The key is to balance spiritual pursuit with practical responsibilities.',
        'strengthGuide': {
            'strong': 'Jupiter exalted with Ketu — powerful spiritual awakening, potential for genuine enlightenment.',
            'moderate': 'Jupiter in own sign with Ketu — strong spiritual inclinations with some worldly balance.',
            'weak': 'Jupiter debilitated with Ketu — confusion between spiritual and material paths.',
        },
        'timing': 'Activates during Jupiter or Ketu Mahadasha/Antardasha periods.',
        'remedies': [
            'Regular meditation and spiritual practice',
            'Balance spiritual pursuits with practical duties',
            'Chant Ganesh and Jupiter mantras',
            'Seek guidance from experienced spiritual teachers',
            'Practice mindful detachment rather than total renunciation',
        ],
    },
    'Punarpoo Yoga': {
        'description': 'Saturn and Moon conjunction in a kendra house — emotional depth with delays but eventual stability.',
        'planets': ['Saturn', 'Moon'],
        'housesAffected': [1, 4, 7, 10],
        'lifeAreas': ['emotional maturity', 'patience', 'delayed success', 'stability', 'deep thinking'],
        'prediction': 'Punarpoo Yoga combines Saturn\'s discipline with Moon\'s sensitivity in kendra houses, creating a person with deep emotional intelligence and patience. While initial life may bring emotional challenges and delays, the native develops extraordinary resilience and wisdom. They become excellent counselors, therapists, or advisors due to their understanding of both structure (Saturn) and emotion (Moon). Late-blooming success is a hallmark.',
        'strengthGuide': {
            'strong': 'Saturn exalted with Moon in kendra — powerful emotional mastery and eventual great success.',
            'moderate': 'Saturn in own sign with Moon — strong emotional stability with moderate delays.',
            'weak': 'Saturn debilitated with Moon — significant emotional challenges requiring active remedies.',
        },
        'timing': 'Activates during Saturn Mahadasha or during Saturn-Moon combined periods.',
        'remedies': [
            'Saturday and Monday worship',
            'Practice emotional regulation through yoga and meditation',
            'Chant Saturn and Moon mantras',
            'Seek therapy or counseling to process emotions',
            'Donate to elderly care and women\'s welfare',
        ],
    },
    'Sarpa Dosha': {
        'description': 'All seven classical planets confined between Rahu and Ketu axis — intense karmic pattern with snake-bite metaphor.',
        'planets': ['Rahu', 'Ketu', 'Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'],
        'housesAffected': [],
        'lifeAreas': ['karmic patterns', 'transformation', 'intensity', 'foreign connections', 'unconventional life'],
        'prediction': 'Sarpa Dosha (Serpent affliction) indicates intense karmic patterns where all classical planets are hemmed between Rahu and Ketu. The native faces significant life challenges that feel fated or karmic. However, this also creates extraordinary potential for transformation and spiritual growth. Many great spiritual leaders, healers, and transformational figures have this dosha. The key is conscious spiritual practice and acceptance of life\'s intense lessons.',
        'strengthGuide': {
            'strong': 'All planets between Rahu-Ketu with malefics dominating — intense karmic experiences requiring spiritual remedies.',
            'moderate': 'All planets between Rahu-Ketu with mixed influences — moderate karmic patterns with some relief.',
            'weak': 'Planets partially outside the axis — reduced intensity, easier navigation.',
        },
        'timing': 'Effects are lifelong but intensify during Rahu or Ketu Mahadasha/Antardasha periods.',
        'remedies': [
            'Rahu-Ketu Shanti Puja at a recognized temple',
            'Rudra Abhishek for overall planetary peace',
            'Nag Panchami worship and snake deity rituals',
            'Maha Mrityunjaya Mantra chanting',
            'Regular spiritual practice and meditation',
            'Help those bitten by snakes or suffering from poison',
        ],
    },
    'Dhana Yoga (Lord Exchange)': {
        'description': 'Lord of the 2nd house placed in the 11th house, or lord of the 11th house placed in the 2nd house — direct wealth exchange yoga.',
        'planets': ['Various'],
        'housesAffected': [2, 11],
        'lifeAreas': ['income', 'savings', 'financial growth', 'family wealth', 'accumulation'],
        'prediction': 'This specific Dhana Yoga through lord exchange creates a powerful financial circuit between the 2nd house (accumulated wealth, family money) and 11th house (income, gains, fulfillments). The native has a natural ability to convert income into lasting wealth, or to leverage family resources for income generation. This yoga indicates steady financial growth and the ability to multiply money through multiple streams.',
        'strengthGuide': {
            'strong': 'Both lords in exaltation or own signs — exceptional wealth accumulation and financial flow.',
            'moderate': 'Lords in friendly signs — good financial management with steady growth.',
            'weak': 'One or both lords debilitated — wealth present but with obstacles in accumulation.',
        },
        'timing': 'Activates during the dasha of the 2nd or 11th house lords.',
        'remedies': [
            'Save a fixed percentage of all income',
            'Invest wisely rather than spend impulsively',
            'Chant Lakshmi and Kubera mantras',
            'Donate to education and family welfare',
            'Maintain good relations with family for financial support',
        ],
    },
    'Vasundhara Yoga': {
        'description': 'Derived from Vasumad — Jupiter in 5th house and Venus in 9th house (or vice versa) — exceptional wealth and fortune through creativity and dharma.',
        'planets': ['Jupiter', 'Venus'],
        'housesAffected': [5, 9],
        'lifeAreas': ['creativity', 'fortune', 'wealth', 'dharma', 'speculation', 'spiritual wealth'],
        'prediction': 'Vasundhara Yoga (also called Vasumad variant) places the two most benefic planets in the most fortunate trikona houses. The 5th house placement of one planet blesses creativity, speculation, and children, while the 9th house placement of the other blesses fortune, dharma, and spiritual wealth. Together they create a life of both material comfort and spiritual fulfillment, with wealth flowing naturally from creative and dharmic pursuits.',
        'strengthGuide': {
            'strong': 'Both planets exalted or in own signs in trikonas — extraordinary creative wealth and spiritual fortune.',
            'moderate': 'Both in friendly signs in trikonas — strong creative and fortunate life.',
            'weak': 'One planet debilitated — reduced benefits but still present in some form.',
        },
        'timing': 'Activates during Jupiter or Venus Mahadasha/Antardasha periods.',
        'remedies': [
            'Pursue creative endeavors seriously',
            'Practice and promote dharma',
            'Thursday and Friday worship',
            'Donate to arts and spiritual education',
            'Invest in creative and spiritual ventures',
        ],
    },
}


def _get_asc_sign(planets: list, houses_data: dict) -> str:
    return houses_data.get('ascendant', {}).get('sign', '')


def _compute_chart(body: YogaPredRequest):
    from ..main import detect_yogas
    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets = calc_planets(jd, None, body.nodeMode or 'mean')
    houses_data = calc_houses(jd, body.latitude, body.longitude, planets, body.houseSystem or 'W')
    asc_sign = houses_data.get('ascendant', {}).get('sign', '')
    detected = detect_yogas(planets, houses_data.get('houses', []), asc_sign)
    return planets, houses_data, asc_sign, detected


def _enrich_yoga(yoga_name: str, yoga_info: dict, detected_yoga: dict, planets: list) -> dict:
    pred = YOGA_PREDICTIONS.get(yoga_name, {})
    pmap = {p['name']: p for p in planets}

    involved = pred.get('planets', [])
    involved_info = []
    for pname in involved:
        p = pmap.get(pname)
        if p:
            status = planet_status(pname, p.get('sign', ''))
            involved_info.append({
                'name': pname,
                'sign': p.get('sign', ''),
                'house': p.get('house', 0),
                'degree': p.get('degree', 0),
                'dignity': status,
                'retrograde': p.get('isRetrograde', False),
                'combust': p.get('isCombust', False),
            })

    dignity_map = {
        'Exalted': 'strong',
        'Own Sign': 'moderate',
        'Mooltrikona': 'moderate',
        'Friendly': 'moderate',
        'Neutral': 'weak',
        'Enemy': 'weak',
        'Debilitated': 'weak',
    }

    detected_strength = detected_yoga.get('strength', 'Medium')
    if detected_strength in ('Strong', 'Very Strong'):
        strength_level = 'strong'
    elif detected_strength in ('Medium', 'Mixed'):
        strength_level = 'moderate'
    else:
        strength_level = 'weak'

    avg_dignity = None
    dignities = [dignity_map.get(i.get('dignity', ''), 'weak') for i in involved_info]
    if dignities:
        score_map = {'strong': 3, 'moderate': 2, 'weak': 1}
        avg_score = sum(score_map.get(d, 1) for d in dignities) / len(dignities)
        if avg_score >= 2.5:
            avg_dignity = 'strong'
        elif avg_score >= 1.5:
            avg_dignity = 'moderate'
        else:
            avg_dignity = 'weak'

    final_strength = avg_dignity or strength_level
    strength_text = pred.get('strengthGuide', {}).get(final_strength, detected_strength)

    return {
        'name': yoga_name,
        'description': pred.get('description', detected_yoga.get('description', '')),
        'planetsInvolved': involved_info,
        'housesAffected': pred.get('housesAffected', []),
        'lifeAreasImpacted': pred.get('lifeAreas', []),
        'strength': {
            'level': final_strength.capitalize(),
            'detail': strength_text,
        },
        'timing': pred.get('timing', 'Dasha-dependent — consult a Vedic astrologer for precise timing.'),
        'prediction': pred.get('prediction', detected_yoga.get('description', '')),
        'isMalefic': final_strength == 'weak' and yoga_name in (
            'Kemadruma Yoga', 'Daridra Yoga', 'Guru Chandal Yoga',
            'Chandala Yoga', 'Sarpa Dosha',
        ),
        'remedies': pred.get('remedies', []) if final_strength == 'weak' or yoga_name in (
            'Kemadruma Yoga', 'Daridra Yoga', 'Guru Chandal Yoga',
            'Chandala Yoga', 'Sarpa Dosha',
        ) else [],
    }


@router.post('/horoscope/yoga/predictions')
def yoga_predictions(body: YogaPredRequest):
    planets, houses_data, asc_sign, detected = _compute_chart(body)

    enriched = []
    for dy in detected:
        name = dy.get('name', '')
        entry = _enrich_yoga(name, {}, dy, planets)
        enriched.append(entry)

    return {
        'status': 200,
        'data': {
            'ascendant': houses_data.get('ascendant', {}),
            'totalYogasDetected': len(enriched),
            'yogas': enriched,
        },
    }


@router.post('/horoscope/yoga/detailed')
def yoga_detailed(body: YogaDetailedRequest):
    planets, houses_data, asc_sign, detected = _compute_chart(body)

    target = body.yogaName.strip()
    matched = None
    for dy in detected:
        if dy.get('name', '').lower() == target.lower():
            matched = dy
            break

    if not matched:
        for dy in detected:
            if target.lower() in dy.get('name', '').lower():
                matched = dy
                break

    if not matched and target in YOGA_PREDICTIONS:
        matched = {'name': target, 'description': YOGA_PREDICTIONS[target]['description'], 'strength': 'Medium'}

    if not matched:
        return {
            'status': 404,
            'error': f"Yoga '{target}' not found in the chart. Detected yogas: {[d.get('name') for d in detected]}",
        }

    enriched = _enrich_yoga(matched['name'], {}, matched, planets)
    enriched['detailedAnalysis'] = True

    return {
        'status': 200,
        'data': enriched,
    }


def _compute_score(planets: list, detected: list) -> dict:
    score = 0
    breakdown = []
    malefic_count = 0

    positive_yogas = [
        'Ruchaka Yoga (Mahapurusha)', 'Bhadra Yoga (Mahapurusha)',
        'Hamsa Yoga (Mahapurusha)', 'Malavya Yoga (Mahapurusha)',
        'Shasha Yoga (Mahapurusha)', 'Gajakesari Yoga',
        'Budha Aditya Yoga', 'Chandra Mangala Yoga',
        'Neecha Bhanga Raja Yoga', 'Amala Yoga',
        'Dhana Yoga', 'Dhana Yoga (Lord Exchange)',
        'Raja Yoga', 'Viparita Raja Yoga',
        'Lakshmi Yoga', 'Saraswati Yoga',
        'Shubhakartari Yoga', 'Vasumad Yoga',
        'Vasundhara Yoga', 'Pancha Mangala Yoga',
    ]

    negative_yogas = [
        'Kemadruma Yoga', 'Daridra Yoga',
        'Guru Chandal Yoga', 'Chandala Yoga',
        'Sarpa Dosha',
    ]

    strength_scores = {
        'Very Strong': 15,
        'Strong': 12,
        'Medium': 8,
        'Mixed': 6,
        'Malefic': -8,
        'Weak': -5,
    }

    for dy in detected:
        name = dy.get('name', '')
        s = dy.get('strength', 'Medium')
        pts = strength_scores.get(s, 5)

        if name in positive_yogas:
            pts = max(pts, 5)
            score += pts
            breakdown.append({'yoga': name, 'points': pts, 'type': 'positive'})
        elif name in negative_yogas:
            pts = min(pts, 0)
            score += pts
            malefic_count += 1
            breakdown.append({'yoga': name, 'points': pts, 'type': 'negative'})
        else:
            if s in ('Malefic', 'Weak'):
                pts = min(pts, 0)
                malefic_count += 1
                breakdown.append({'yoga': name, 'points': pts, 'type': 'negative'})
            else:
                score += pts
                breakdown.append({'yoga': name, 'points': pts, 'type': 'positive'})

    normalized = max(0, min(100, 50 + score))

    if normalized >= 80:
        grade = 'Excellent'
        summary = 'This chart contains many powerful auspicious yogas with strong planetary dignities. The native is likely to enjoy exceptional success, fortune, and recognition.'
    elif normalized >= 65:
        grade = 'Very Good'
        summary = 'This chart has strong benefic yogas that promise good fortune and success. With proper effort, the native can achieve significant accomplishments.'
    elif normalized >= 50:
        grade = 'Good'
        summary = 'This chart has a balanced mix of positive and challenging influences. Success is achievable through sustained effort and leveraging the positive yogas.'
    elif normalized >= 35:
        grade = 'Moderate'
        summary = 'This chart has some challenges but also compensating yogas. The native should focus on remedies and making the most of available opportunities.'
    else:
        grade = 'Challenging'
        summary = 'This chart has significant challenges that require active remedies and spiritual practice. However, even challenging yogas can be transformed through conscious effort.'

    return {
        'overallScore': normalized,
        'grade': grade,
        'summary': summary,
        'totalYogasAnalyzed': len(detected),
        'beneficYogas': len([b for b in breakdown if b['type'] == 'positive']),
        'maleficYogas': malefic_count,
        'breakdown': breakdown,
    }


@router.post('/horoscope/yoga/score')
def yoga_score(body: YogaPredRequest):
    planets, houses_data, asc_sign, detected = _compute_chart(body)
    score_data = _compute_score(planets, detected)

    return {
        'status': 200,
        'data': {
            'ascendant': houses_data.get('ascendant', {}),
            **score_data,
        },
    }
