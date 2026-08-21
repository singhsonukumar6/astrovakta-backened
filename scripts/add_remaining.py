#!/usr/bin/env python3
"""Add missing short-term translation categories to ta.py, gu.py, pa.py."""
import os

TRANS_DIR = os.path.join(os.path.dirname(__file__), '..', 'app', 'i18n', 'translations')

SHORT_CATS = {
    'ta': {
        'dignity': {'Exalted': 'உயர்ந்த', 'Debilitated': 'தாழ்ந்த', 'Own Sign': 'சொந்த ராசி', 'Moolatrikona': 'மூலத்ரிகோணம்', 'Friendly': 'நண்பன்', 'Enemy': 'எதிரி', 'Neutral': 'நடுநிலை', 'Very Strong': 'மிகவும் வலுவான', 'Strong': 'வலுவான', 'Moderate': 'சராசரி', 'Weak': 'பலவீனம்'},
        'muhurat_name': {'Abhijit Muhurta': 'அபிஜித் முகூர்த்தம்', 'Brahma Muhurta': 'பிரம்ம முகூர்த்தம்', 'Amrit Ghadi': 'அமிர்த காலம்', 'Shubh Muhurta': 'சுப முகூர்த்தம்', 'Labh Ghadi': 'லாப காலம்'},
        'muhurat_rating_cap': {'Excellent': 'சிறப்பு', 'Good': 'நல்ல', 'Avoid': 'தவிர்க்கவும்', 'Inauspicious': 'அசுபம்'},
        'hindu_month': {'Chaitra': 'சித்திரை', 'Vaishakh': 'வைகாசி', 'Jyeshtha': 'ஜேஷ்ட', 'Ashadha': 'ஆடி', 'Shravana': 'ஆவணி', 'Bhadrapada': 'புரட்டாசி', 'Ashwin': 'ஐப்பசி', 'Kartik': 'கார்த்திகை', 'Margashirsha': 'மார்கழி', 'Paush': 'தை', 'Magh': 'மாசி', 'Phalguna': 'பங்குனி'},
        'month_name': {'January': 'ஜனவரி', 'February': 'பிப்ரவரி', 'March': 'மார்ச்', 'April': 'ஏப்ரல்', 'May': 'மே', 'June': 'ஜூன்', 'July': 'ஜூலை', 'August': 'ஆகஸ்ட்', 'September': 'செப்டம்பர்', 'October': 'அக்டோபர்', 'November': 'நவம்பர்', 'December': 'டிசம்பர்'},
        'festival_type': {'Sankranti': 'சங்கராந்தி', 'Harvest Festival': 'அறுவடை விழா', 'Puja': 'பூஜை', 'Fasting': 'விரதம்', 'New Year': 'புத்தாண்டு', 'Auspicious Day': 'சுப தினம்', 'Holy Bath': 'புனித நீராடல்', 'Amavasya': 'அமாவாசை', 'Purnima': 'பௌர்ணமி', 'Festival': 'விழா', 'Jayanti': 'ஜெயந்தி', 'Ekadashi Fasting': 'ஏகாதசி விரதம்'},
        'sade_sati_phase': {'Rising': 'ஏறும் சாடே சாதி', 'Peak': 'உச்ச சாடே சாதி', 'Setling': 'இறங்கும் சாடே சாதி', 'rising': 'ஏறும் சாடே சாதி', 'peak': 'உச்ச சாடே சாதி', 'settling': 'இறங்கும் சாடே சாதி', 'No Sade Sati or Dhaiya active': 'சாடே சாதி அல்லது தைய்யா செயல்படவில்லை'},
        'compatibility_verdict_ext': {'Very Good Match': 'மிக நல்ல பொருத்தம்', 'Excellent': 'சிறப்பு', 'Very Good': 'மிக நல்ல', 'Good': 'நல்ல', 'Average': 'சராசரி', 'Poor': 'மோசம்', 'Very Poor': 'மிக மோசம்'},
        'aspect_name': {'Conjunction': 'யுதி', 'Trine': 'திரிகோணம்', 'Square': 'சதுரம்', 'Opposition': 'எதிர்வு', 'Sextile': 'ஷஷ்டகம்', 'Semi-Sextile': 'அரை ஷஷ்டகம்', 'Quincunx': 'க்வின்கன்க்ஸ்'},
        'confirmation': {'Strong confirmation': 'வலுவான உறுதிப்பாடு', 'Moderate confirmation': 'சராசரி உறுதிப்பாடு', 'Weak or no confirmation': 'பலவீனம் அல்லது உறுதிப்பாடு இல்லை'},
        'chart_title': {'East Indian Chart': 'கிழக்கு இந்திய சார்ட்', 'Moon Chart': 'சந்திரன் சார்ட்', 'Navamsa Chart': 'நவாம்ச சார்ட்', 'Hora Chart': 'ஹோரா சார்ட்', 'Sudarshana Chakra': 'சுதர்ஷன சக்கரம்', 'North Indian Chart': 'வட இந்திய சார்ட்', 'South Indian Chart': 'தென் இந்திய சார்ட்', 'Asc': 'லக்னம்'},
        'zodiac_full': {'Aries': 'மேஷம்', 'Taurus': 'ரிஷபம்', 'Gemini': 'மிதுனம்', 'Cancer': 'கடகம்', 'Leo': 'சிம்மம்', 'Virgo': 'கன்னி', 'Libra': 'துலாம்', 'Scorpio': 'விருச்சிகம்', 'Sagittarius': 'தனுசு', 'Capricorn': 'மகரம்', 'Aquarius': 'கும்பம்', 'Pisces': 'மீனம்'},
        'planet_position': {'in': 'இல்', 'at': 'இல்', 'degree': 'பாகை', 'retrograde': 'வக்கிரம்', 'combust': 'எரிந்த', 'House': 'பாவம்', 'Sign': 'ராசி', 'Nakshatra': 'நட்சத்திரம்'},
        'astro_term': {'Ascendant': 'லக்னம்', 'Lagna': 'லக்னம்', 'Moon Sign': 'சந்திர ராசி', 'Sun Sign': 'சூரிய ராசி', 'Birth Star': 'பிறந்த நட்சத்திரம்', 'Nakshatra Lord': 'நட்சத்திர அதிபதி', 'Sign Lord': 'ராசி அதிபதி', 'Vimshottari Dasha': 'விம்சோத்தரி தசா', 'System': 'முறை', 'Unknown': 'அறியப்படாத'},
    },
    'gu': {
        'dignity': {'Exalted': 'ઉચ્ચ', 'Debilitated': 'નીચ', 'Own Sign': 'સ્વરાશિ', 'Moolatrikona': 'મૂલત્રિકોણ', 'Friendly': 'મિત્ર', 'Enemy': 'શત્રુ', 'Neutral': 'તટસ્થ', 'Very Strong': 'અત્યંત બળવાન', 'Strong': 'બળવાન', 'Moderate': 'મધ્યમ', 'Weak': 'દુર્બળ'},
        'muhurat_name': {'Abhijit Muhurta': 'અભિજિત મુહૂર્ત', 'Brahma Muhurta': 'બ્રહ્મ મુહૂર્ત', 'Amrit Ghadi': 'અમૃત ઘડી', 'Shubh Muhurta': 'શુભ મુહૂર્ત', 'Labh Ghadi': 'લાભ ઘડી'},
        'muhurat_rating_cap': {'Excellent': 'ઉત્કૃષ્ટ', 'Good': 'સારું', 'Avoid': 'ટાળો', 'Inauspicious': 'અશુભ'},
        'hindu_month': {'Chaitra': 'ચૈત્ર', 'Vaishakh': 'વૈશાખ', 'Jyeshtha': 'જ્યેષ્ઠ', 'Ashadha': 'આષાઢ', 'Shravana': 'શ્રાવણ', 'Bhadrapada': 'ભાદ્રપદ', 'Ashwin': 'આશ્વિન', 'Kartik': 'કાર્તિક', 'Margashirsha': 'માર્ગશીર્ષ', 'Paush': 'પૌષ', 'Magh': 'માઘ', 'Phalguna': 'ફાલ્ગુન'},
        'month_name': {'January': 'જાન્યુઆરી', 'February': 'ફેબ્રુઆરી', 'March': 'માર્ચ', 'April': 'એપ્રિલ', 'May': 'મે', 'June': 'જૂન', 'July': 'જુલાઈ', 'August': 'ઑગસ્ટ', 'September': 'સપ્ટેમ્બર', 'October': 'ઑક્ટોબર', 'November': 'નવેમ્બર', 'December': 'ડિસેમ્બર'},
        'festival_type': {'Sankranti': 'સંક્રાંતિ', 'Harvest Festival': 'ફસળ ઉત્સવ', 'Puja': 'પૂજા', 'Fasting': 'વ્રત', 'New Year': 'નવું વર્ષ', 'Auspicious Day': 'શુભ દિવસ', 'Holy Bath': 'પવિત્ર સ્નાન', 'Amavasya': 'અમાસ', 'Purnima': 'પૂનમ', 'Festival': 'ઉત્સવ', 'Jayanti': 'જયંતી', 'Ekadashi Fasting': 'એકાદશી વ્રત'},
        'sade_sati_phase': {'Rising': 'વધતું સાડે સાતી', 'Peak': 'ચરમ સાડે સાતી', 'Setling': 'ઉતરતું સાડે સાતી', 'rising': 'વધતું સાડે સાતી', 'peak': 'ચરમ સાડે સાતી', 'settling': 'ઉતરતું સાડે સાતી', 'No Sade Sati or Dhaiya active': 'સાડે સાતી અથવા દૈહ્ય સક્રિય નથી'},
        'compatibility_verdict_ext': {'Very Good Match': 'ખૂબ સારી જોડી', 'Excellent': 'ઉત્કૃષ્ટ', 'Very Good': 'ખૂબ સારું', 'Good': 'સારું', 'Average': 'સરેરાશ', 'Poor': 'ખરાબ', 'Very Poor': 'ખૂબ ખરાબ'},
        'aspect_name': {'Conjunction': 'યુતિ', 'Trine': 'ત્રિકોણ', 'Square': 'ચોરસ', 'Opposition': 'સપ્તમ', 'Sextile': 'ષષ્ટક', 'Semi-Sextile': 'અર્ધ ષષ્ટક', 'Quincunx': 'ક્વિન્કન્ક્સ'},
        'confirmation': {'Strong confirmation': 'મજબૂત ખાતરી', 'Moderate confirmation': 'મધ્યમ ખાતરી', 'Weak or no confirmation': 'નબળી અથવા ખાતરી નથી'},
        'chart_title': {'East Indian Chart': 'પૂર્વ ભારતીય ચાર્ટ', 'Moon Chart': 'ચંદ્ર ચાર્ટ', 'Navamsa Chart': 'નવાંશ ચાર્ટ', 'Hora Chart': 'હોરા ચાર્ટ', 'Sudarshana Chakra': 'સુદર્શન ચક્ર', 'North Indian Chart': 'ઉત્તર ભારતીય ચાર્ટ', 'South Indian Chart': 'દક્ષિણ ભારતીય ચાર્ટ', 'Asc': 'લગ્ન'},
        'zodiac_full': {'Aries': 'મેષ', 'Taurus': 'વૃષભ', 'Gemini': 'મિથુન', 'Cancer': 'કર્ક', 'Leo': 'સિંહ', 'Virgo': 'કન્યા', 'Libra': 'તુલા', 'Scorpio': 'વૃશ્ચિક', 'Sagittarius': 'ધનુ', 'Capricorn': 'મકર', 'Aquarius': 'કુંભ', 'Pisces': 'મીન'},
        'planet_position': {'in': 'રાશિમાં', 'at': 'અંશે', 'degree': 'અંશ', 'retrograde': 'વક્ર', 'combust': 'દગ્ધ', 'House': 'ભાવ', 'Sign': 'રાશિ', 'Nakshatra': 'નક્ષત્ર'},
        'astro_term': {'Ascendant': 'લગ્ન', 'Lagna': 'લગ્ન', 'Moon Sign': 'ચંદ્ર રાશિ', 'Sun Sign': 'સૂર્ય રાશિ', 'Birth Star': 'જન્મ નક્ષત્ર', 'Nakshatra Lord': 'નક્ષત્ર અધિપતિ', 'Sign Lord': 'રાશિ અધિપતિ', 'Vimshottari Dasha': 'વિમ્શોત્તરી દશા', 'System': 'પદ્ધતિ', 'Unknown': 'અજ્ઞાત'},
    },
    'pa': {
        'dignity': {'Exalted': 'ਉੱਚ', 'Debilitated': 'ਨੀਚ', 'Own Sign': 'ਆਪਣੀ ਰਾਸ਼ੀ', 'Moolatrikona': 'ਮੂਲਤ੍ਰਿਕੋਣ', 'Friendly': 'ਮਿੱਤਰ', 'Enemy': 'ਦੁਸ਼ਮਣ', 'Neutral': 'ਤਟਸਥ', 'Very Strong': 'ਬਹੁਤ ਤਾਕਤਵਰ', 'Strong': 'ਤਾਕਤਵਰ', 'Moderate': 'ਦਰਮਿਆਨਾ', 'Weak': 'ਕਮਜ਼ੋਰ'},
        'muhurat_name': {'Abhijit Muhurta': 'ਅਭਿਜਿਤ ਮੁਹੂਰਤ', 'Brahma Muhurta': 'ਬ੍ਰਹਮ ਮੁਹੂਰਤ', 'Amrit Ghadi': 'ਅਮ੍ਰਿਤ ਘੜੀ', 'Shubh Muhurta': 'ਸ਼ੁਭ ਮੁਹੂਰਤ', 'Labh Ghadi': 'ਲਾਭ ਘੜੀ'},
        'muhurat_rating_cap': {'Excellent': 'ਸ਼੍ਰੇਸ਼ਠ', 'Good': 'ਵਧੀਆ', 'Avoid': 'ਬਚੋ', 'Inauspicious': 'ਅਸ਼ੁਭ'},
        'hindu_month': {'Chaitra': 'ਚੈਤ੍ਰ', 'Vaishakh': 'ਵੈਸਾਖ', 'Jyeshtha': 'ਜਿੱਠ', 'Ashadha': 'ਹਾੜ', 'Shravana': 'ਸਾਵਣ', 'Bhadrapada': 'ਭਾਦੋ', 'Ashwin': 'ਅਸ਼ੂਈਂ', 'Kartik': 'ਕਾਰਤਿਕ', 'Margashirsha': 'ਮੱਗਸਰ', 'Paush': 'ਪੌਸ', 'Magh': 'ਮਾਘ', 'Phalguna': 'ਫੱਗਣ'},
        'month_name': {'January': 'ਜਨਵਰੀ', 'February': 'ਫ਼ਰਵਰੀ', 'March': 'ਮਾਰਚ', 'April': 'ਅਪ੍ਰੈਲ', 'May': 'ਮਈ', 'June': 'ਜੂਨ', 'July': 'ਜੁਲਾਈ', 'August': 'ਅਗਸਤ', 'September': 'ਸਤੰਬਰ', 'October': 'ਅਕਤੂਬਰ', 'November': 'ਨਵੰਬਰ', 'December': 'ਦਸੰਬਰ'},
        'festival_type': {'Sankranti': 'ਸੰਕ੍ਰਾਂਤੀ', 'Harvest Festival': 'ਫਸਲ ਦਾ ਤਿਉਹਾਰ', 'Puja': 'ਪੂਜਾ', 'Fasting': 'ਵਰਤ', 'New Year': 'ਨਵਾਂ ਸਾਲ', 'Auspicious Day': 'ਸ਼ੁਭ ਦਿਨ', 'Holy Bath': 'ਪਵਿੱਤਰ ਸਨਾਨ', 'Amavasya': 'ਅਮਾਵਸ', 'Purnima': 'ਪੂਰਨਮੀ', 'Festival': 'ਤਿਉਹਾਰ', 'Jayanti': 'ਜਯੰਤੀ', 'Ekadashi Fasting': 'ਏਕਾਦਸ਼ੀ ਵਰਤ'},
        'sade_sati_phase': {'Rising': 'ਵਧਦਾ ਸਾਡੇ ਸਾਤੀ', 'Peak': 'ਚਰਮ ਸਾਡੇ ਸਾਤੀ', 'Setling': 'ਉਤਰਦਾ ਸਾਡੇ ਸਾਤੀ', 'rising': 'ਵਧਦਾ ਸਾਡੇ ਸਾਤੀ', 'peak': 'ਚਰਮ ਸਾਡੇ ਸਾਤੀ', 'settling': 'ਉਤਰਦਾ ਸਾਡੇ ਸਾਤੀ', 'No Sade Sati or Dhaiya active': 'ਸਾਡੇ ਸਾਤੀ ਜਾਂ ਦੈਹੀ ਸਰਗਰਮ ਨਹੀਂ'},
        'compatibility_verdict_ext': {'Very Good Match': 'ਬਹੁਤ ਵਧੀਆ ਜੋੜਾ', 'Excellent': 'ਸ਼ਾਨਦਾਰ', 'Very Good': 'ਬਹੁਤ ਵਧੀਆ', 'Good': 'ਵਧੀਆ', 'Average': 'ਔਸਤ', 'Poor': 'ਮਾੜਾ', 'Very Poor': 'ਬਹੁਤ ਮਾੜਾ'},
        'aspect_name': {'Conjunction': 'ਯੁਤੀ', 'Trine': 'ਤਿਕੋਣ', 'Square': 'ਚੌਰਸ', 'Opposition': 'ਸਪਤਮ', 'Sextile': 'ਸ਼ਸ਼ਟਕ', 'Semi-Sextile': 'ਅੱਧਾ ਸ਼ਸ਼ਟਕ', 'Quincunx': 'ਕੁਇਨਕਨਕਸ'},
        'confirmation': {'Strong confirmation': 'ਮਜ਼ਬੂਤ ਤਸਦੀਕ', 'Moderate confirmation': 'ਦਰਮਿਆਨਾ ਤਸਦੀਕ', 'Weak or no confirmation': 'ਕਮਜ਼ੋਰ ਜਾਂ ਤਸਦੀਕ ਨਹੀਂ'},
        'chart_title': {'East Indian Chart': 'ਪੂਰਬੀ ਭਾਰਤੀ ਚਾਰਟ', 'Moon Chart': 'ਚੰਦਰਮਾ ਚਾਰਟ', 'Navamsa Chart': 'ਨਵਾਂਸ਼ ਚਾਰਟ', 'Hora Chart': 'ਹੋਰਾ ਚਾਰਟ', 'Sudarshana Chakra': 'ਸੁਦਰਸ਼ਨ ਚੱਕਰ', 'North Indian Chart': 'ਉੱਤਰੀ ਭਾਰਤੀ ਚਾਰਟ', 'South Indian Chart': 'ਦੱਖਣੀ ਭਾਰਤੀ ਚਾਰਟ', 'Asc': 'ਲੱਗਣ'},
        'zodiac_full': {'Aries': 'ਮੇਸ਼', 'Taurus': 'ਵ੍ਰਿਸ਼ਭ', 'Gemini': 'ਮਿਥੁਨ', 'Cancer': 'ਕਰਕ', 'Leo': 'ਸਿੰਘ', 'Virgo': 'ਕੰਨੀ', 'Libra': 'ਤੁਲਾ', 'Scorpio': 'ਵ੍ਰਿਸ਼ਚਿਕ', 'Sagittarius': 'ਧਨੁ', 'Capricorn': 'ਮਕਰ', 'Aquarius': 'ਕੁੰਭ', 'Pisces': 'ਮੀਨ'},
        'planet_position': {'in': 'ਰਾਸ਼ੀ ਵਿੱਚ', 'at': 'ਅੰਸ਼ ਤੇ', 'degree': 'ਅੰਸ਼', 'retrograde': 'ਵਕਰ', 'combust': 'ਦਹਿਣ', 'House': 'ਭਾਵ', 'Sign': 'ਰਾਸ਼ੀ', 'Nakshatra': 'ਨੱਕਸ਼ਤਰ'},
        'astro_term': {'Ascendant': 'ਲੱਗਣ', 'Lagna': 'ਲੱਗਣ', 'Moon Sign': 'ਚੰਦਰਮਾ ਰਾਸ਼ੀ', 'Sun Sun': 'ਸੂਰਜ ਰਾਸ਼ੀ', 'Birth Star': 'ਜਨਮ ਨੱਕਸ਼ਤਰ', 'Nakshatra Lord': 'ਨੱਕਸ਼ਤਰ ਅਧਿਪਤੀ', 'Sign Lord': 'ਰਾਸ਼ੀ ਅਧਿਪਤੀ', 'Vimshottari Dasha': 'ਵਿਮਸ਼ੋਤਰੀ ਦਸ਼ਾ', 'System': 'ਪ੍ਰਣਾਲੀ', 'Unknown': 'ਅਣਜਾਣ'},
    },
}

for lang in ["ta", "gu", "pa"]:
    path = os.path.join(TRANS_DIR, f"{lang}.py")
    with open(path, "r") as f:
        content = f.read()
    
    cats = SHORT_CATS[lang]
    lines = []
    for cat_name, translations in cats.items():
        lines.append(f"        '{cat_name}': {{")
        for k, v in translations.items():
            lines.append(f"            '{k}': '{v}',")
        lines.append("        },")
    
    insert_block = "\n".join(lines)
    
    last_brace = content.rfind("}")
    new_content = content[:last_brace] + "\n" + insert_block + "\n" + content[last_brace:]
    
    with open(path, "w") as f:
        f.write(new_content)
    print(f"Updated {lang}.py")

# Verify
for lang in ["ta", "gu", "pa"]:
    path = os.path.join(TRANS_DIR, f"{lang}.py")
    spec = importlib.util.spec_from_file_location("mod", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    print(f"{lang}: {len(mod.TRANSLATIONS)} categories")
