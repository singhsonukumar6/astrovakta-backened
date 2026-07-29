from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import pytz
import hashlib

router = APIRouter()

# ──────────────────────────────────────────────
# Request / response models
# ──────────────────────────────────────────────

class HoroscopeRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    zodiacSign: Optional[str] = Field(None, example="Aries")


# ──────────────────────────────────────────────
# Prediction template banks
# Each category maps sign → list of template dicts
# with keys: overview, positive, challenging
# ──────────────────────────────────────────────

# ── DAILY ────────────────────────────────────

DAILY_OVERVIEW: Dict[str, List[Dict[str, str]]] = {
    'Aries': [
        {"positive": "Your bold energy is amplified today as the Moon transits your sign. Expect a surge of confidence that helps you tackle pending tasks head-on. A leadership opportunity may present itself unexpectedly.", "challenging": "Impulsive decisions could lead to unnecessary friction with colleagues. Take a breath before responding to provocation today."},
        {"positive": "Mars aspects bring fire to your endeavors — initiating new projects yields favorable results. Physical activity will channel your abundant energy productively.", "challenging": "Restlessness may make it difficult to focus on routine work. Try to channel your fiery temperament into creative outlets rather than arguments."},
        {"positive": "A dynamic day where your natural initiative shines. Others look to you for direction, and you deliver with characteristic Aries courage. Romance gets a playful spark.", "challenging": "You may come across as overly aggressive in negotiations. Soften your approach to achieve better outcomes."},
        {"positive": "The cosmic alignment favors bold moves today. Your pioneering spirit attracts allies and resources. Trust your instincts on financial matters.", "challenging": "Watch for overcommitting yourself — enthusiasm is high but energy may wane by evening. Pace yourself wisely."},
    ],
    'Taurus': [
        {"positive": "Venus graces your financial sector, bringing unexpected monetary gains or a valuable appreciation from a loved one. Sensual pleasures are heightened — enjoy good food and comfort.", "challenging": "Stubbornness may prevent you from seeing a better alternative today. Be open to adjusting your well-laid plans."},
        {"positive": "Material comforts and stable relationships are favored. A family matter resolves beautifully, strengthening bonds. Your patient approach to a long-term goal begins to show results.", "challenging": "Resistance to change could create tension with a partner. Flexibility today prevents bigger conflicts tomorrow."},
        {"positive": "Your earthy wisdom helps ground chaotic situations around you. Financial investments made today have strong long-term potential. Enjoy nature for emotional recharge.", "challenging": "Indulgence in luxury spending could strain your budget. Exercise restraint even when everything looks appealing."},
        {"positive": "A deeply satisfying day for Taurus natives. Creative projects flourish, and your aesthetic sense is particularly sharp. Relationships deepen through shared quiet moments.", "challenging": "Jealousy or possessiveness may surface in romantic connections. Trust your partner and give them space."},
    ],
    'Gemini': [
        {"positive": "Mercury's favorable placement sparks brilliant communication. Ideas flow effortlessly, making it an excellent day for writing, presentations, or meaningful conversations. Social connections expand.", "challenging": "Scattered attention may prevent you from completing what you start. Choose one priority and commit to it."},
        {"positive": "Your wit and charm are magnetic today. Networking events or casual encounters lead to valuable connections. Learning something new satisfies your restless mind.", "challenging": "Gossip or idle talk could backfire. Be mindful of what you share and with whom."},
        {"positive": "Mental agility is at its peak — solve complex problems with ease. Siblings or neighbors bring good news. Short trips prove surprisingly rewarding.", "challenging": "Overthinking a simple decision creates unnecessary anxiety. Sometimes the first instinct is the best one."},
        {"positive": "Versatility is your superpower today. Juggling multiple tasks effortlessly earns admiration. A creative writing project or social media endeavor gains traction.", "challenging": "Superficial engagement in relationships leaves partners feeling undervalued. Go deeper in your interactions."},
    ],
    'Cancer': [
        {"positive": "The Moon illuminates your emotional depths, bringing profound intuitive insights. Home matters flourish — a family gathering or domestic project brings deep satisfaction.", "challenging": "Mood sensitivity is amplified today. Small slights may feel overwhelming. Practice emotional boundaries to protect your peace."},
        {"positive": "Your nurturing nature creates a sanctuary for loved ones. Property or real estate matters move favorably. Trust your gut feelings — they are especially accurate now.", "challenging": "Clinging to the past prevents you from embracing present opportunities. Release old emotional baggage."},
        {"positive": "A emotionally rich day where deep connections are formed. Your empathic abilities help heal rifts in the family. Comfort cooking or gardening provides therapeutic relief.", "challenging": "Avoid retreating into your shell when challenges arise. Confront issues directly rather than avoiding them."},
        {"positive": "The cosmic tide supports emotional healing and inner reflection. A mother figure or maternal bond brings comfort. Your home radiates warmth and safety for all who enter.", "challenging": "Mood swings could disrupt household harmony. Communicate your feelings rather than expecting others to guess."},
    ],
    'Leo': [
        {"positive": "The Sun beams directly on your creativity and romance sectors. Self-expression flourishes — pursue artistic endeavors with confidence. Romance sparkles with dramatic flair.", "challenging": "Pride may prevent you from accepting helpful advice. Humility opens doors that ego keeps closed."},
        {"positive": "Your natural magnetism is irresistible today. Career recognition arrives through a creative project. Children or younger people bring joy and inspiration.", "challenging": "Centering every conversation around yourself alienates friends. Show genuine interest in others' stories."},
        {"positive": "A royally good day for Leos — leadership roles come naturally and others respond to your warmth. Creative vision translates into tangible成果. Love life sizzles.", "challenging": "Overconfidence in financial decisions could lead to losses. Seek counsel before major expenditures."},
        {"positive": "Your generous spirit attracts abundance in all forms. The spotlight finds you effortlessly — use it to uplift others. A passionate connection deepens.", "challenging": "Dramatic reactions to minor setbacks waste precious energy. Maintain your regal composure under pressure."},
    ],
    'Virgo': [
        {"positive": "Mercury's analytical influence helps you organize and optimize every area of life. Health routines yield excellent results. Detailed work receives recognition and praise.", "challenging": "Perfectionism creates paralysis — done is better than perfect today. Allow some margin for human error."},
        {"positive": "Your practical approach to problems solves a long-standing issue. Service to others brings unexpected rewards. A health regimen begun today yields lasting benefits.", "challenging": "Critical analysis of loved ones hurts feelings. Offer constructive feedback with gentleness and timing."},
        {"positive": "Productivity soars as your methodical nature aligns with cosmic order. Financial planning and budgeting are especially favored. Dietary improvements show quick results.", "challenging": "Anxiety about details robs you of enjoying the bigger picture. Zoom out and appreciate your progress."},
        {"positive": "The stars bless your diligent efforts with tangible results. A work project reaches completion ahead of schedule. Your helpful nature earns deep respect from peers.", "challenging": "Worrying about health symptoms that don't exist creates unnecessary stress. Focus on preventive care rather than imagined ailments."},
    ],
    'Libra': [
        {"positive": "Venus, your ruling planet, enhances social grace and artistic sensibility. Partnerships of all kinds thrive. Aesthetic endeavors and beauty treatments yield satisfying results.", "challenging": "Indecisiveness may cause you to miss a time-sensitive opportunity. Weigh options quickly and commit."},
        {"positive": "Harmony in relationships reaches a peak. Diplomatic skills resolve a conflict that seemed intractable. Legal matters or contracts favorably align.", "challenging": "People-pleasing at the expense of your own needs leads to resentment. Balance giving with receiving."},
        {"positive": "Your charm offensive opens doors in both personal and professional realms. A creative collaboration produces beautiful results. Social invitations bring delightful connections.", "challenging": "Avoiding confrontation to maintain peace only delays inevitable difficult conversations. Address issues with tact but honesty."},
        {"positive": "Balance is your superpower today — you mediate, create beauty, and foster cooperation wherever you go. Financial partnerships and shared resources are especially blessed.", "challenging": "Dependency on external validation undermines your confidence. Your worth isn't determined by others' opinions."},
    ],
    'Scorpio': [
        {"positive": "Pluto's transformative energy helps you release what no longer serves you. Deep psychological insights lead to powerful personal breakthroughs. Intimacy deepens profoundly.", "challenging": "Suspicion and jealousy may poison an otherwise healthy relationship. Choose trust over paranoia."},
        {"positive": "Your penetrating insight uncovers hidden truths that benefit you and others. Research and investigation work are especially successful. Financial transformations begin.", "challenging": "Obsessive focus on a grudge consumes energy better spent on growth. Release and regenerate."},
        {"positive": "Mars empowers your strategic mind — plans execute with precision. Occult or metaphysical studies yield fascinating discoveries. Shared resources bring unexpected benefits.", "challenging": "Control dynamics in relationships create power struggles. Practice vulnerability instead of dominance."},
        {"positive": "A day of profound regeneration — shed old skin and emerge stronger. Your intensity is an asset in negotiations. Emotional breakthroughs lead to liberation.", "challenging": "Secrecy and manipulation backfire spectacularly. Authenticity, not control, is your path to power today."},
    ],
    'Sagittarius': [
        {"positive": "Jupiter's expansive influence opens new horizons — literally and figuratively. Travel, education, or philosophical discussions ignite your spirit. Optimism attracts fortunate outcomes.", "challenging": "Overconfidence in a risky venture could lead to losses. Temper enthusiasm with practical assessment."},
        {"positive": "Your infectious enthusiasm inspires everyone around. A teaching or mentoring role brings fulfillment. International connections or long-distance communications bring good tidings.", "challenging": "Tactless honesty hurts sensitive people. Your words carry weight today — use them wisely."},
        {"positive": "Adventure calls — whether physical travel or intellectual exploration, say yes today. Higher learning and spiritual studies are especially favored. Your faith in the future is rewarded.", "challenging": "Restlessness disrupts steady progress. Find joy in the journey rather than constantly seeking the next horizon."},
        {"positive": "The Archer's arrow hits its mark — goals set in motion find their target. Legal matters resolve favorably. Your philosophical outlook provides comfort to a worried friend.", "challenging": "Overcommitting to too many projects dilutes your effectiveness. Choose your most meaningful pursuit and focus."},
    ],
    'Capricorn': [
        {"positive": "Saturn's disciplined energy rewards your consistent hard work with visible career progress. Authority figures recognize your reliability. Long-term structures you've built begin to pay dividends.", "challenging": "Workaholism strains personal relationships. Make time for loved ones despite your ambitious drive."},
        {"positive": "Professional milestones are within reach — your mountain-climbing determination has brought you to a new plateau. Financial planning and legacy-building are especially supported.", "challenging": "Rigidity in your methods prevents adaptation to changing circumstances. Flexibility doesn't mean weakness."},
        {"positive": "Your practical, step-by-step approach to challenges inspires confidence in your team. Property and career matters advance significantly. Patience proves its worth.", "challenging": "Pessimism or cynicism closes you off from joyful experiences. Lighten up and allow happiness in."},
        {"positive": "The Goat scales new heights in professional achievement. Structured planning transforms abstract goals into concrete results. Mentors and elders offer invaluable guidance.", "challenging": "Emotional suppression creates physical tension. Allow yourself to feel and express vulnerability."},
    ],
    'Aquarius': [
        {"positive": "Uranus sparks innovative ideas that revolutionize your approach to community and technology. Group projects gain momentum. Your unique perspective is your greatest asset today.", "challenging": "Emotional detachment alienates those who need your warmth. Balance your intellectual brilliance with genuine human connection."},
        {"positive": "Social networks expand in exciting directions. Humanitarian causes you support gain visibility. A friendship transforms into something deeper and more meaningful.", "challenging": "Rebellious streak creates unnecessary conflict with authority. Choose your battles with wisdom."},
        {"positive": "Your visionary thinking solves problems others didn't even recognize. Technology and innovation favor your plans. Friends become family in surprising ways.", "challenging": "Unpredictability makes partners feel insecure. Provide some stability alongside your excitement."},
        {"positive": "The future looks bright as your progressive ideas gain traction. Collective efforts yield extraordinary results. Your eccentricity is celebrated rather than tolerated today.", "challenging": "Detachment from current responsibilities in pursuit of future visions creates practical problems. Balance idealism with action."},
    ],
    'Pisces': [
        {"positive": "Neptune's mystical influence deepens your already powerful intuition. Creative and spiritual pursuits flourish. Dreams carry important messages — keep a journal by your bed.", "challenging": "Escapist tendencies could lead to neglecting responsibilities. Face reality with compassion rather than avoidance."},
        {"positive": "Your empathic sensitivity heals emotional wounds — both yours and others'. Artistic expression reaches new heights. Compassionate service brings deep spiritual satisfaction.", "challenging": "Absorbing others' emotional burdens depletes your energy. Practice discernment in who you help and how."},
        {"positive": "A deeply spiritual day where the veil between worlds thins in your favor. Meditation and prayer are especially powerful. Healing abilities are amplified.", "challenging": "Confusion clouds practical decision-making. Delay major choices until clarity returns."},
        {"positive": "The cosmic ocean supports your soul's journey. Intuitive flashes guide you toward your highest good. Music, poetry, and art become vehicles for transcendence.", "challenging": "Boundary issues in relationships create confusion about where you end and others begin. Strengthen your energetic boundaries."},
    ],
}

# ── WEEKLY ───────────────────────────────────

WEEKLY_OVERVIEW: Dict[str, List[Dict[str, str]]] = {
    'Aries': [
        {"positive": "This week ignites your competitive spirit — professional challenges that seemed daunting become exciting opportunities. Mars drives you forward with unstoppable momentum. By Friday, a significant milestone is reached.", "challenging": "Early-week aggression may create workplace friction. Channel your fire into projects rather than arguments with colleagues."},
        {"positive": "A transformative week where courage leads to breakthroughs. New partnerships form that enhance your reach. Physical vitality peaks mid-week — perfect for athletic challenges.", "challenging": "Impatience with slower-moving collaborators creates tension. Remember that everyone operates at different speeds."},
    ],
    'Taurus': [
        {"positive": "Financial matters stabilize beautifully this week. A long-term investment or savings plan bears unexpected fruit. Venus enhances romantic connections — singles may encounter someone deeply appealing.", "challenging": "Resistance to adapting your routine creates missed opportunities. Flexibility this week yields surprising rewards."},
        {"positive": "Your patient, methodical approach pays off as projects reach completion. Home improvements or family gatherings bring deep satisfaction. Sensory pleasures — good food, music, nature — recharge your spirit.", "challenging": "Overindulgence in comfort threatens to derail health goals. Enjoy pleasures mindfully and in moderation."},
    ],
    'Gemini': [
        {"positive": "Communication breakthroughs transform a stalled project. Mercury empowers your natural gift for words — writing, speaking, or teaching endeavors flourish. Social calendar fills with exciting possibilities.", "challenging": "Spreading yourself too thin across social commitments leads to superficial connections. Prioritize depth over breadth."},
        {"positive": "Your intellectual curiosity leads to exciting discoveries. Learning a new skill or subject gains traction. Siblings or neighbors become important allies. Short travel brings unexpected delight.", "challenging": "Inconsistency in commitments erodes trust. Follow through on promises, even small ones."},
    ],
    'Cancer': [
        {"positive": "Emotional healing reaches a turning point this week. Family dynamics shift in a positive direction as old wounds are acknowledged and addressed. Property matters advance favorably.", "challenging": "Mood fluctuations affect decision-making early in the week. Wait for emotional clarity before important choices."},
        {"positive": "Home becomes your sanctuary as domestic projects bring pride and comfort. Intuitive guidance proves remarkably accurate — trust your gut feelings on relational matters. Culinary experiments delight loved ones.", "challenging": "Clinging to outdated emotional patterns prevents growth. Seek professional support if past trauma resurfaces."},
    ],
    'Leo': [
        {"positive": "Creative projects reach a spectacular climax this week. Your artistic vision impresses even the most discerning critics. Romance is dramatic and passionate — expect a memorable gesture from a loved one.", "challenging": "Ego clashes with authority figures create professional risk. Practice diplomacy without losing your authentic voice."},
        {"positive": "The spotlight shines brilliantly on your talents. A performance, presentation, or creative showcase garners acclaim. Children bring joy and inspiration. Love life reaches new heights of passion.", "challenging": "Financial generosity, while noble, strains resources this week. Give within your means."},
    ],
    'Virgo': [
        {"positive": "Health and wellness initiatives gain powerful momentum. A dietary change or exercise routine begun this week produces noticeable results. Work efficiency earns admiration from supervisors.", "challenging": "Over-criticism of yourself and others creates a negative atmosphere. Celebrate small wins instead of focusing on imperfections."},
        {"positive": "Your analytical abilities solve a complex problem that has baffled others. Detailed-oriented tasks receive your masterful attention. Service activities bring unexpected emotional rewards.", "challenging": "Anxiety about upcoming deadlines disrupts sleep. Practice relaxation techniques and prioritize tasks realistically."},
    ],
    'Libra': [
        {"positive": "Partnerships of all kinds flourish this week. A business collaboration or romantic partnership reaches a new level of harmony and mutual benefit. Social grace opens unexpected doors.", "challenging": "Avoiding necessary conflicts to maintain peace allows problems to fester. Address issues early with your trademark tact."},
        {"positive": "Artistic pursuits receive cosmic support — your creative output is exceptionally beautiful and balanced. Legal matters or contract negotiations favor your position. Beauty treatments yield striking results.", "challenging": "Decision paralysis about a career move wastes valuable time. Set a deadline for yourself and commit."},
    ],
    'Scorpio': [
        {"positive": "Deep psychological work yields powerful breakthroughs this week. Transformative experiences purify your emotional landscape. Shared financial matters resolve favorably. Intimacy deepens dramatically.", "challenging": "Trust issues resurface and threaten a new relationship. Recognize past patterns and choose a different response."},
        {"positive": "Your strategic mind operates at peak efficiency — long-term plans execute flawlessly. Research projects reveal hidden knowledge. Financial restructuring brings long-term security.", "challenging": "Intensity frightens those who aren't accustomed to your depth. Gradually reveal your deeper layers rather than overwhelming others."},
    ],
    'Sagittarius': [
        {"positive": "A week of expansive possibilities — travel plans, educational pursuits, and philosophical explorations all gain traction. Jupiter's blessings manifest as lucky breaks and serendipitous encounters.", "challenging": "Over-promising and under-delivering damages credibility. Be realistic about what you can accomplish."},
        {"positive": "Higher learning and spiritual studies yield profound insights. International connections bring exciting opportunities. Your optimism inspires a friend going through a difficult time.", "challenging": "Restlessness disrupts focus on important tasks. Ground yourself through physical activity before mental work."},
    ],
    'Capricorn': [
        {"positive": "Career aspirations advance significantly this week. A promotion, recognition, or new responsibility acknowledges your consistent dedication. Financial planning sessions produce excellent long-term strategies.", "challenging": "Work-life balance suffers under the weight of professional ambition. Schedule time for relationships and self-care."},
        {"positive": "Your disciplined approach transforms challenges into stepping stones. Property investments or structural improvements yield lasting value. Mentors provide crucial guidance at a pivotal moment.", "challenging": "Emotional unavailability frustrates a partner who needs connection. Vulnerability strengthens rather than weakens your position."},
    ],
    'Aquarius': [
        {"positive": "Innovation and technology favor your ventures this week. Group projects accelerate as collective intelligence proves greater than the sum of its parts. Friendships deepen through shared purpose.", "challenging": "Detachment from emotional needs of close friends creates distance. Show up with your heart, not just your mind."},
        {"positive": "Your humanitarian vision gains practical momentum — a cause you champion receives support and visibility. Social connections expand in enriching ways. Original ideas disrupt stagnant situations productively.", "challenging": "Rebellion for its own sake wastes energy. Choose causes worth fighting for with strategic wisdom."},
    ],
    'Pisces': [
        {"positive": "Spiritual and creative channels flow abundantly this week. Dreams and intuitions carry messages of deep significance — record and reflect on them. Healing work, whether self-directed or for others, yields powerful results.", "challenging": "Escapism through substances or excessive screen time drains your sensitive energy. Choose healthy outlets for emotional processing."},
        {"positive": "Your compassionate nature attracts someone who needs exactly what you offer. Artistic projects reach a beautiful completion. Meditation and spiritual practices open extraordinary inner doors.", "challenging": "Boundary erosion in relationships creates emotional confusion. Healthy boundaries protect both you and those you love."},
    ],
}

# ── MONTHLY ──────────────────────────────────

MONTHLY_OVERVIEW: Dict[str, List[Dict[str, str]]] = {
    'Aries': [
        {"positive": "This month marks a turning point in your professional trajectory. Mars transiting your career house ignites ambition and drive — a job offer, promotion, or business venture gains serious momentum. Romance blooms through shared adventures.", "challenging": "Burnout threatens by mid-month if you don't pace yourself. Strategic rest isn't laziness — it's essential fuel for your fire."},
        {"positive": "A powerful month for initiating bold new chapters. Jupiter's influence expands your social circle with influential contacts. Financial gains through innovative ventures surprise and delight. Physical health reaches a new peak.", "challenging": "Relationship friction from prioritizing career over connection requires conscious attention. Schedule dedicated partner time."},
    ],
    'Taurus': [
        {"positive": "Venus governs a month of deep material and emotional satisfaction. Savings grow, assets appreciate, and a creative passion project gains traction. Relationships deepen through shared quiet luxuries and genuine presence.", "challenging": "Resistance to necessary changes in a relationship or financial strategy creates stagnation. Embrace evolution."},
        {"positive": "Your patient investments — financial and emotional — begin yielding substantial returns. Home and family matters bring deep contentment. A health routine established this month transforms your vitality.", "challenging": "Over-attachment to a particular outcome causes unnecessary suffering. Trust the process and release rigid expectations."},
    ],
    'Gemini': [
        {"positive": "Mercury empowers a month of intellectual breakthroughs. Writing projects, business communications, and learning endeavors flourish. Social connections multiply — every conversation is a potential doorway to opportunity.", "challenging": "Inconsistency and scattered focus prevent completion of important projects. Commit to one priority at a time."},
        {"positive": "Your versatile mind masters a new skill or field of knowledge with impressive speed. Networking events yield valuable professional connections. Short trips bring both adventure and practical benefits.", "challenging": "Superficial engagement in relationships leaves partners wanting more depth. Go beyond the surface this month."},
    ],
    'Cancer': [
        {"positive": "Home and family life reaches a beautiful crescendo. A property purchase, renovation, or family celebration marks this month as significant. Emotional intelligence guides you through complex interpersonal dynamics with grace.", "challenging": "Emotional overload from taking on everyone's problems depletes your reserves. Practice selective empathy."},
        {"positive": "Your nurturing instincts create profound healing in your domestic sphere. A mother figure or maternal relationship deepens. Financial matters related to property or home investments yield positive results.", "challenging": "Nostalgia prevents you from fully embracing present opportunities. Honor the past while stepping boldly into the future."},
    ],
    'Leo': [
        {"positive": "A month where your creative powers reach extraordinary heights. Artistic projects receive recognition and reward. Romance is passionate and deeply fulfilling — express your love with dramatic generosity.", "challenging": "Financial overextension from extravagant displays of affection strains resources. Love doesn't require expensive props."},
        {"positive": "Your natural leadership inspires a team to achieve remarkable results. Children or creative projects bring immense pride. The Sun's influence strengthens your physical vitality and personal magnetism throughout the month.", "challenging": "Dominating conversations and relationships alienates those who need to be heard. Practice the art of listening."},
    ],
    'Virgo': [
        {"positive": "Health transformation reaches a major milestone this month. A wellness routine established now yields lasting benefits. Career details you've mastered receive formal recognition. Analytical work produces groundbreaking insights.", "challenging": "Perfectionist tendencies delay project completion. Set realistic standards and ship the work."},
        {"positive": "Your meticulous approach to a complex project produces exceptional results. Service to others brings unexpected emotional and material rewards. Financial budgeting this month creates long-term security.", "challenging": "Critical self-talk undermines confidence. Replace the inner critic with a compassionate inner mentor."},
    ],
    'Libra': [
        {"positive": "Partnerships and collaborations reach harmonious peaks. A business alliance or romantic relationship enters a deeply balanced and mutually fulfilling phase. Social elegance opens exclusive opportunities.", "challenging": "Codependency patterns emerge in close relationships. Maintain your individual identity within partnerships."},
        {"positive": "Artistic and creative endeavors receive cosmic blessing — your aesthetic sensibility produces genuinely beautiful work. Legal matters conclude favorably. Social prestige rises through grace and diplomacy.", "challenging": "Avoidance of necessary confrontations allows small issues to become major problems. Address them with elegance and honesty."},
    ],
    'Scorpio': [
        {"positive": "A month of profound transformation and regeneration. Deep psychological work liberates you from limiting patterns. Financial restructuring creates lasting security. Intimate relationships reach new depths of trust and connection.", "challenging": "Trust issues from past betrayals may sabotage current blessings. Therapy or deep self-reflection helps process old wounds."},
        {"positive": "Your strategic brilliance produces exceptional results in research, investigation, or occult studies. Shared resources yield unexpected benefits. Pluto's influence empowers radical authenticity.", "challenging": "Controlling behavior in relationships creates destructive power dynamics. Practice surrender and trust."},
    ],
    'Sagittarius': [
        {"positive": "Jupiter opens doors to exciting international or educational opportunities. A long-term vision gains practical momentum. Travel plans materialize beautifully. Philosophy and spirituality deepen your understanding of life's meaning.", "challenging": "Overextension across too many pursuits dilutes your impact. Choose your most meaningful adventure and commit fully."},
        {"positive": "A month of expansive growth — your optimism attracts fortunate circumstances. Teaching or mentoring roles bring deep satisfaction. Legal matters and publishing ventures progress favorably.", "challenging": "Restlessness disrupts important projects. Ground your fire through regular physical exercise and meditation."},
    ],
    'Capricorn': [
        {"positive": "Professional aspirations reach a significant milestone this month. Years of disciplined effort culminate in tangible recognition — a promotion, award, or major accomplishment. Financial legacy-building gains strong momentum.", "challenging": "Workaholism damages personal relationships. Schedule intentional quality time with loved ones this month."},
        {"positive": "Your mountain goat determination scales new professional heights. Property investments and structural projects yield lasting value. Mentorship from an elder provides crucial career guidance.", "challenging": "Emotional suppression creates physical ailments. Express feelings through journaling, therapy, or trusted confidants."},
    ],
    'Aquarius': [
        {"positive": "Social networks and humanitarian projects gain remarkable momentum. Your innovative ideas attract funding, support, and enthusiastic collaborators. Technology-related ventures progress favorably. Friendships deepen through shared purpose.", "challenging": "Emotional detachment in intimate relationships creates disconnection. Engage your heart alongside your brilliant mind."},
        {"positive": "A revolutionary month where your progressive vision becomes reality. Group achievements surpass individual efforts. Unique talents find appreciative audiences. Community leadership roles emerge naturally.", "challenging": "Unpredictable behavior creates insecurity in partners. Balance excitement with some reassuring consistency."},
    ],
    'Pisces': [
        {"positive": "A deeply spiritual month where intuition reaches extraordinary heights. Creative projects achieve transcendent beauty. Healing abilities amplify — whether for yourself or others. Dreams carry prophetic significance.", "challenging": "Escapist tendencies threaten to derail important responsibilities. Face challenges with your characteristic compassion rather than avoidance."},
        {"positive": "Neptune's mystical influence opens profound spiritual channels. Artistic expression reaches new heights of emotional depth. Compassionate service transforms both the served and the server.", "challenging": "Boundary confusion in relationships creates emotional chaos. Healthy boundaries serve love rather than opposing it."},
    ],
}

# ── YEARLY ───────────────────────────────────

YEARLY_OVERVIEW: Dict[str, List[Dict[str, str]]] = {
    'Aries': [
        {"positive": "This year Jupiter's transit through your wealth and communication sectors brings significant financial growth and a voice that commands attention. Saturn's stabilizing influence transforms your career from scattered efforts into a focused, powerful trajectory. Major professional milestones await those who persist.", "challenging": "Saturn's restrictive energy in your spiritual house may create periods of doubt and isolation. Rahu's influence tempts you with shortcuts — resist them. Sustainable success comes through disciplined Mars-inspired action."},
        {"positive": "A landmark year where your pioneering spirit finds its perfect expression. New business ventures launched in the first half gain tremendous traction. Relationships deepen as you learn to balance independence with genuine partnership.", "challenging": "Health requires vigilant attention — Mars transits may bring inflammation or accidents if you're reckless. Prioritize preventive care and channel aggression into sports rather than conflict."},
    ],
    'Taurus': [
        {"positive": "Venus bestows a year of extraordinary beauty, love, and material abundance. Long-term investments mature beautifully. Relationships that have been carefully nurtured reach a deeply satisfying new chapter. Creative talents find profitable expression.", "challenging": "Saturn's transit through your karma house creates karmic reckoning — past debts, emotional and financial, demand settlement. Resistance to this necessary cleansing prolongs the discomfort."},
        {"positive": "Your steadfast nature builds empires this year. Jupiter expands your social network with influential contacts who accelerate your goals. Home and property matters bring exceptional satisfaction. Health stabilizes beautifully.", "challenging": "Stubbornness in adapting to changing market conditions costs opportunities. Your fixed nature is a strength — but flexibility is its necessary complement."},
    ],
    'Gemini': [
        {"positive": "Mercury's favorable transits make this a year of brilliant communication and intellectual achievement. Writing, speaking, teaching, or media careers reach new professional heights. Social connections multiply exponentially.", "challenging": "Scattered energy across too many interests prevents mastery in any. Choose your most important pursuit and commit deeply. Saturn demands focused discipline from your naturally diffuse nature."},
        {"positive": "Your versatile mind masters multiple subjects and skills this year, creating unique professional value. Travel expands your horizons in unexpected ways. Financial gains come through communication-based ventures.", "challenging": "Relationships suffer from inconsistency and divided attention. Your partners need presence, not just charming intermittent engagement."},
    ],
    'Cancer': [
        {"positive": "Home and family life undergoes beautiful transformation this year. Jupiter blesses property matters, renovations, and domestic happiness. Emotional healing reaches profound depths as you release generational patterns. Maternal bonds strengthen.", "challenging": "Saturn's transit through your career house creates professional pressures that strain personal life. Setting boundaries between work and home becomes essential for survival."},
        {"positive": "Your emotional intelligence reaches maturity this year, enabling you to navigate complex family dynamics with unusual grace. Financial security increases through property investments and steady professional advancement.", "challenging": "Clinging to outdated emotional patterns prevents growth. Therapy or deep introspection this year yields life-changing insights."},
    ],
    'Leo': [
        {"positive": "A year where your creative vision and leadership abilities reach legendary status. Jupiter expands your artistic and romantic horizons. A major creative project receives public acclaim. Romance is passionate, dramatic, and deeply fulfilling.", "challenging": "Saturn's influence in your education and philosophy house challenges your belief systems. Sacred cow-slaying, while painful, leads to a more authentic and mature worldview."},
        {"positive": "The Sun's transits throughout the year consistently strengthen your vitality and personal magnetism. Children or creative projects bring extraordinary pride. Financial growth through creative enterprises accelerates.", "challenging": "Overconfidence leads to financial overextension. Even Leos must respect budgets and seek financial counsel for major decisions."},
    ],
    'Virgo': [
        {"positive": "Health transformation reaches a life-changing milestone this year. A wellness commitment begun now produces results that redefine your physical capabilities. Analytical work earns significant professional recognition. Service roles bring deep fulfillment.", "challenging": "Saturn's transit through your relationship house tests partnerships with sustained pressure. Only the strongest relationships survive — and they emerge transformed and fortified."},
        {"positive": "Your methodical approach builds systems that operate with elegant efficiency. Financial planning this year creates decades of security. A dietary or lifestyle change begun now extends your healthy years dramatically.", "challenging": "Perfectionism becomes a prison rather than a standard. Learn to celebrate 'excellent' rather than demanding 'flawless'."},
    ],
    'Libra': [
        {"positive": "Venus guides a year of profound relational harmony and social elevation. Partnerships — romantic, business, and creative — reach beautiful equilibriums. Artistic achievements receive lasting recognition. Legal matters resolve favorably.", "challenging": "Saturn's transit through your work house demands sustained professional effort without immediate visible reward. Trust the long-term process."},
        {"positive": "Your diplomatic genius mediates conflicts that others couldn't touch, earning lasting respect and influence. Social prestige rises through graceful generosity. Creative collaborations produce masterworks.", "challenging": "People-pleasing at the expense of personal needs creates deep resentment. Your balance must include self-care."},
    ],
    'Scorpio': [
        {"positive": "A year of profound regeneration and transformation. Pluto, your ruling planet, clears out what no longer serves you, making space for extraordinary rebirth. Financial restructuring creates lasting wealth. Deep psychological work liberates your spirit.", "challenging": "The intensity of transformation may overwhelm those around you. Pace your metamorphosis to allow relationships to adapt."},
        {"positive": "Your strategic mind operates at its highest level this year — long-term plans execute with devastating precision. Research, investigation, and occult studies yield remarkable discoveries. Intimacy reaches unprecedented depths.", "challenging": "Control dynamics in relationships create destructive cycles. Surrender — perhaps the hardest lesson for a Scorpio — is this year's most important spiritual curriculum."},
    ],
    'Sagittarius': [
        {"positive": "Jupiter, your ruling planet, delivers a year of extraordinary expansion and blessing. International travel, higher education, publishing, and philosophical pursuits all flourish. Your optimistic worldview attracts genuinely fortunate circumstances.", "challenging": "Saturn's transit through your foundation house destabilizes your sense of security. Building new foundations while old ones shake requires faith — which, fortunately, is your natural strength."},
        {"positive": "The Archer's aim is true this year — goals set with genuine intention find their mark. Teaching and mentoring roles bring deep satisfaction. Spiritual practices deepen profoundly under Jupiter's expansive grace.", "challenging": "Overextension across too many interests prevents mastery. Choose wisely and go deep rather than wide."},
    ],
    'Capricorn': [
        {"positive": "Saturn, your ruling planet, rewards decades of disciplined effort with major career achievements. Professional recognition reaches its highest level. Financial legacy-building creates generational wealth. Property investments yield extraordinary returns.", "challenging": "Saturn's transit through your communication house creates delays and misunderstandings. Extra patience with paperwork, negotiations, and daily communications is essential this year."},
        {"positive": "Your mountain goat nature reaches the summit this year — a peak professional achievement or recognition marks a life milestone. Structured planning transforms abstract dreams into concrete, lasting realities.", "challenging": "Health requires careful attention — Saturn's influence demands respect for your body's limits. Preventive care and regular maintenance prevent breakdown."},
    ],
    'Aquarius': [
        {"positive": "Uranus electrifies your year with revolutionary ideas and unexpected breakthroughs. Social movements and humanitarian projects you champion gain powerful momentum. Technology-related ventures achieve remarkable success.", "challenging": "Saturn's transit through your identity house creates a crisis of self — who you've been may not align with who you're becoming. This painful identity work leads to authentic self-expression."},
        {"positive": "Collective endeavors produce results far exceeding individual efforts. Your network becomes a powerhouse of innovation and support. Original ideas disrupt established systems in beneficial ways.", "challenging": "Emotional unavailability in close relationships creates loneliness despite social popularity. True connection requires vulnerability."},
    ],
    'Pisces': [
        {"positive": "Neptune deepens your already extraordinary spiritual and creative gifts this year. Artistic projects reach transcendent beauty. Healing abilities — whether physical, emotional, or spiritual — reach their highest expression. Dreams carry prophetic weight.", "challenging": "Saturn's transit through your hidden house creates confrontation with unconscious patterns, fears, and addictions. This shadow work is necessary and ultimately liberating."},
        {"positive": "Your compassionate nature attracts opportunities to serve at the highest levels. Music, poetry, film, and visual arts achieve their most profound expressions through you. Intuitive guidance leads you unerringly toward your highest good.", "challenging": "Boundary dissolution threatens your physical and emotional health. Discernment — knowing where you end and others begin — is this year's most critical skill."},
    ],
}

# ── CAREER ───────────────────────────────────

CAREER: Dict[str, List[Dict[str, str]]] = {
    'Aries': [
        {"positive": "Mars empowers your professional ambitions — a leadership role or entrepreneurial venture gains significant momentum. Your decisive action impresses superiors and attracts valuable partnerships. Career recognition through bold initiative is assured.", "challenging": "Workplace conflicts from an overly aggressive approach damage professional relationships. Temper your natural directness with diplomacy."},
        {"positive": "Your pioneering energy initiates projects that others couldn't even conceptualize. Salary negotiations or business deals favor your position. Physical energy supports long hours when pursuing meaningful goals.", "challenging": "Impulsive career changes without proper research lead to disappointment. Channel your impatience into thorough preparation."},
    ],
    'Taurus': [
        {"positive": "Venus blesses career endeavors with aesthetic excellence and financial acumen. Your reliable, steady approach builds lasting professional structures. Creative industries and financial sectors especially favor your talents this period.", "challenging": "Resistance to professional innovation or technology adoption falls behind competitors. Embrace necessary changes to your tried methods."},
        {"positive": "Your patient investment in skills and relationships yields substantial career returns. A promotion or recognition reflects years of consistent, high-quality work. Financial rewards finally match your contribution level.", "challenging": "Over-comfort in current position prevents growth. Seek stretch assignments that develop new capabilities."},
    ],
    'Gemini': [
        {"positive": "Mercury's analytical gift makes you the communication hub of every project. Writing, marketing, teaching, or consulting careers flourish. Your ability to translate complex ideas into clear language is your greatest professional asset.", "challenging": "Scattered professional interests prevent mastery in any single area. Choose your most promising career track and develop depth."},
        {"positive": "Intellectual versatility opens diverse career opportunities simultaneously. Technology, media, and communication-based roles especially reward your multifaceted talents. Networking creates breakthrough professional connections.", "challenging": "Inconsistency in work output disappoints supervisors expecting reliability. Follow through consistently, even when interest wanes."},
    ],
    'Cancer': [
        {"positive": "Your emotional intelligence becomes a powerful professional asset. Careers in caregiving, real estate, hospitality, or human resources reach new heights. Your intuitive understanding of people creates exceptional professional relationships.", "challenging": "Taking work stress home and home stress to work creates a destructive cycle. Establish clear professional-emotional boundaries."},
        {"positive": "Nurturing leadership styles inspire loyal, productive teams. Property-related careers or home-based businesses achieve remarkable success. Your protective instincts create safe, productive work environments.", "challenging": "Mood fluctuations affect professional consistency. Develop emotional regulation techniques for workplace stability."},
    ],
    'Leo': [
        {"positive": "The Sun illuminates your professional path with creative brilliance. Leadership positions in creative, entertainment, or performance industries bring exceptional fulfillment. Your natural charisma attracts lucrative opportunities.", "challenging": "Ego-driven decisions about professional direction lead to costly mistakes. Seek feedback and counsel before major career moves."},
        {"positive": "Creative vision transforms stagnant professional environments. Your ability to inspire and motivate teams produces outstanding organizational results. Public-facing roles showcase your exceptional talents.", "challenging": "Monopolizing team credit for collaborative achievements creates professional enemies. Share recognition generously."},
    ],
    'Virgo': [
        {"positive": "Mercury's analytical power makes you indispensable in quality-focused roles. Detail-oriented careers in healthcare, editing, accounting, or engineering reward your meticulous nature. Your systematic approach solves problems others miss entirely.", "challenging": "Perfectionism delays project completion and frustrates team members who need progress over perfection. Ship the work."},
        {"positive": "Professional mastery through continuous improvement yields industry recognition. Your service-oriented approach creates loyal clients and colleagues. Financial management skills ensure career stability.", "challenging": "Over-criticism of colleagues creates hostile work environments. Offer constructive feedback with genuine warmth."},
    ],
    'Libra': [
        {"positive": "Venus graces your professional life with exceptional social intelligence. Partnership-based careers, law, design, diplomacy, and consulting reach new heights. Your aesthetic sensibility creates valuable professional differentiation.", "challenging": "Conflict avoidance in professional situations allows problems to escalate. Address workplace issues directly and diplomatically."},
        {"positive": "Your ability to create harmony in tense professional environments is a rare and valuable skill. Negotiation, mediation, and client relations roles bring exceptional success and satisfaction.", "challenging": "Indecision about career direction wastes valuable time. Trust your analytical Libra mind and make the call."},
    ],
    'Scorpio': [
        {"positive": "Your strategic mind transforms professional challenges into competitive advantages. Research, investigation, psychology, finance, and occult sciences reward your penetrating approach. Transformative leadership creates organizational revolution.", "challenging": "Trust issues with colleagues and superiors create professional isolation. Strategic vulnerability builds stronger alliances."},
        {"positive": "Pluto's transformative power rebuilds your professional identity from the ground up. A career change or major pivot this period leads to profoundly authentic work. Financial restructuring creates lasting professional security.", "challenging": "Controlling management styles alienate talented team members. Empower rather than micromanage for superior results."},
    ],
    'Sagittarius': [
        {"positive": "Jupiter expands professional horizons through international work, education, publishing, or philosophy. Teaching and mentoring careers reach their highest fulfillment. Your optimistic vision attracts ambitious projects and generous funding.", "challenging": "Overconfidence in professional abilities leads to accepting challenges beyond current competence. Honest self-assessment prevents embarrassing failures."},
        {"positive": "Your philosophical approach to professional challenges inspires innovative solutions. Travel-based careers, import-export, or cross-cultural work flourish under Jupiter's expansive grace. Faith in your mission attracts powerful allies.", "challenging": "Restlessness disrupts steady career progress. Commit to long-term professional goals despite temporary discomfort."},
    ],
    'Capricorn': [
        {"positive": "Saturn rewards your disciplined approach with peak career achievement. Executive leadership, management, and institutional roles reach their highest expression. Your structured methodology creates enduring professional legacy.", "challenging": "Workaholism sacrifices health and relationships for career advancement. Sustainable success requires balance."},
        {"positive": "Your patient, step-by-step approach to career building finally reaches its most ambitious milestone. Property-related careers, construction, or organizational leadership bring exceptional fulfillment and recognition.", "challenging": "Emotional suppression in professional settings creates physical ailments. Express needs and boundaries with appropriate vulnerability."},
    ],
    'Aquarius': [
        {"positive": "Uranus electrifies your career with revolutionary innovation. Technology, social enterprise, group projects, and humanitarian work reach new heights. Your unconventional approach disrupts stale professional norms productively.", "challenging": "Emotional detachment from colleagues creates perception of coldness. Warmth alongside brilliance creates the most powerful professional presence."},
        {"positive": "Your visionary thinking anticipates professional trends before they emerge. Group-based career ventures produce extraordinary collective results. Social networks become powerful professional accelerators.", "challenging": "Unpredictable career decisions create professional instability. Some consistency builds the trust that unconventional approaches require."},
    ],
    'Pisces': [
        {"positive": "Neptune blesses creative, healing, and spiritual careers with transcendent success. Your intuitive understanding of others creates exceptional value in counseling, healthcare, art, and spirituality. Compassionate service becomes profoundly professional.", "challenging": "Boundary issues in professional settings lead to exploitation. Your generous nature requires firm limits to remain sustainable."},
        {"positive": "Your empathic gifts transform professional environments. Musical, artistic, or spiritual careers reach their highest expression. Healing professions — whether physical, emotional, or spiritual — bring both fulfillment and financial reward.", "challenging": "Escapist tendencies avoid necessary professional development. Face skill gaps and practical limitations with courageous honesty."},
    ],
}

# ── LOVE ─────────────────────────────────────

LOVE: Dict[str, List[Dict[str, str]]] = {
    'Aries': [
        {"positive": "Mars ignites passionate romantic connections that burn with exciting intensity. Singles attract partners through confident, authentic self-expression. Existing relationships benefit from adventurous shared experiences that reignite the flame.", "challenging": "Impulsive romantic decisions create unnecessary drama. Pause before sending that text or making that declaration."},
        {"positive": "Your bold romantic gestures delight and surprise your partner. Physical chemistry reaches extraordinary levels. A spontaneous adventure together strengthens your bond immeasurably.", "challenging": "Dominating the relationship with your needs and desires leaves partners feeling unheard. Practice romantic reciprocity."},
    ],
    'Taurus': [
        {"positive": "Venus deepens romantic connections with sensual beauty and genuine comfort. Shared experiences of good food, nature, and physical affection strengthen bonds. A relationship built on solid ground reaches beautiful new depths.", "challenging": "Possessiveness and jealousy create toxic dynamics. Trust your partner and resist the urge to control romantic outcomes."},
        {"positive": "Your patient, devoted approach to love creates security that allows relationships to flourish. Material comforts shared with a loved one create deeply satisfying domestic bliss. Loyalty is your most attractive quality now.", "challenging": "Resistance to relationship growth creates stagnation. Embrace evolution and new experiences together."},
    ],
    'Gemini': [
        {"positive": "Mercury makes your wit and conversation irresistible in romantic contexts. Intellectual connection deepens physical attraction. A partner who matches your verbal dexterity brings extraordinary satisfaction.", "challenging": "Emotional superficiality in relationships leaves partners feeling undervalued. Go beyond charm to genuine depth."},
        {"positive": "Social connections multiply romantic possibilities. Flirtation through communication — texts, letters, conversation — reaches art form levels. A meeting of minds precedes and enhances physical attraction.", "challenging": "Inconsistency in romantic communication creates confusion and hurt feelings. Be reliable in your romantic expressions."},
    ],
    'Cancer': [
        {"positive": "The Moon deepens emotional intimacy to extraordinary levels. Your nurturing nature creates a love that feels like home — safe, warm, and profoundly comforting. Family bonds and romantic love intertwine beautifully.", "challenging": "Emotional clinginess or neediness pushes partners away. Maintain your emotional center within romantic connections."},
        {"positive": "Your empathic understanding of your partner's needs creates deeply fulfilling intimacy. Shared domestic bliss — cooking together, building a home, caring for family — strengthens romantic bonds beyond measure.", "challenging": "Moodiness creates confusing romantic dynamics. Communicate feelings clearly rather than expecting partners to decode signals."},
    ],
    'Leo': [
        {"positive": "The Sun radiates romantic warmth that attracts admirers and delights partners. Grand romantic gestures — done with genuine sincerity — create unforgettable love stories. Passion runs deep and expressively.", "challenging": "Ego-driven romantic behavior — jealousy, possessiveness, need for constant admiration — creates unnecessary conflict. Love authentically."},
        {"positive": "Your generous, warm-hearted approach to romance inspires devotion. Creative expressions of love — art, music, performances — touch your partner's heart profoundly. Romance reaches cinematic levels.", "challenging": "Making every romantic moment about yourself alienates partners. Celebrate your partner's uniqueness alongside your own."},
    ],
    'Virgo': [
        {"positive": "Mercury enhances thoughtful, practical expressions of love. Acts of service — fixing things, organizing, caring for daily needs — communicate devotion more eloquently than words. A detailed, attentive approach to romance delights partners.", "challenging": "Over-critical analysis of a partner's flaws undermines romantic connection. Appreciate imperfection as human beauty."},
        {"positive": "Your devoted, reliable approach to relationships creates security that allows love to mature beautifully. Health-conscious shared activities strengthen both body and bond. Thoughtful planning creates meaningful romantic experiences.", "challenging": "Perfectionist expectations in a partner create chronic disappointment. Accept and love your partner as they are."},
    ],
    'Libra': [
        {"positive": "Venus, your ruling planet, creates magnetic romantic attraction. Your social grace, aesthetic sensibility, and diplomatic nature make you irresistible. Partnerships reach exquisite states of balance and mutual admiration.", "challenging": "People-pleasing in relationships creates resentment. Your needs matter equally — express them clearly and lovingly."},
        {"positive": "Romantic harmony reaches its most beautiful expression. Shared aesthetic pleasures — art, music, beauty, elegant settings — deepen connection. Your ability to create partnership equilibrium is profoundly attractive.", "challenging": "Avoiding necessary romantic conversations to preserve peace allows problems to fester. Gentle honesty is the kindest approach."},
    ],
    'Scorpio': [
        {"positive": "Pluto deepens romantic connections to their most profound expression. Intimacy — physical, emotional, and psychological — reaches extraordinary depths. Trust, once truly given, creates bonds that transcend ordinary love.", "challenging": "Trust issues from past betrayals poison current blessings. Forgiveness liberates you more than it releases the offender."},
        {"positive": "Your magnetic intensity creates irresistible romantic attraction. Passion runs deeper than words, creating connections that feel fated and transformative. Vulnerability, when genuinely offered, creates the deepest intimacy.", "challenging": "Possessive and controlling behavior destroys the trust you crave. Trust is the foundation — control is its antithesis."},
    ],
    'Sagittarius': [
        {"positive": "Jupiter expands romantic possibilities beyond your current horizon. Shared adventures, philosophical discussions, and mutual growth create exciting, expansive love. A partner who shares your thirst for knowledge and freedom is deeply fulfilling.", "challenging": "Fear of romantic commitment creates instability and hurt feelings. Freedom within commitment is possible with honest communication."},
        {"positive": "Your infectious optimism and adventurous spirit attract exciting romantic connections. Travel with a partner deepens bonds through shared discoveries. Philosophical compatibility enhances physical attraction beautifully.", "challenging": "Tactless honesty about romantic dissatisfaction damages relationships. Deliver truth with love and timing."},
    ],
    'Capricorn': [
        {"positive": "Saturn's disciplined approach creates relationships built on solid, lasting foundations. Your commitment, reliability, and long-term vision attract partners seeking genuine stability. Love matures into its most enduring form.", "challenging": "Emotional unavailability frustrates partners needing warmth and vulnerability. Open your heart alongside offering your stability."},
        {"positive": "Your practical approach to romance — thoughtful gestures, reliable presence, shared goals — creates deeply satisfying partnerships. Love deepens through shared accomplishment and mutual respect for each other's ambitions.", "challenging": "Prioritizing career over romance creates relationship neglect. Schedule love as deliberately as you schedule work."},
    ],
    'Aquarius': [
        {"positive": "Uranus creates exciting, unconventional romantic connections. A friendship that evolves into love brings the deepest fulfillment. Intellectual compatibility is your most important romantic criterion — honor it.", "challenging": "Emotional detachment in intimate relationships creates confusion about your commitment level. Communicate your unique capacity for love."},
        {"positive": "Your progressive approach to relationships creates exciting new models of partnership. Shared social causes and humanitarian work strengthen romantic bonds through shared purpose and meaning.", "challenging": "Unpredictability in romantic behavior creates insecurity. Some consistency builds the trust your unique approach requires."},
    ],
    'Pisces': [
        {"positive": "Neptune creates deeply romantic, almost mystical connections that transcend ordinary love. Your empathic understanding of your partner's deepest needs creates extraordinary intimacy. Creative and spiritual bonds enhance physical attraction.", "challenging": "Idealizing a partner beyond their reality creates devastating disillusionment. Love the real person, not the projection."},
        {"positive": "Your compassionate, selfless approach to love creates deeply healing relationships. Music, art, and shared spiritual practice deepen romantic connection to transcendent levels. Soul connections reach their highest expression.", "challenging": "Boundary dissolution in relationships creates codependency. Healthy love maintains two distinct selves choosing to share."},
    ],
}

# ── FINANCE ──────────────────────────────────

FINANCE: Dict[str, List[Dict[str, str]]] = {
    'Aries': [
        {"positive": "Mars drives bold financial moves that pay off handsomely. Entrepreneurial ventures, competitive financial environments, and innovative investments yield strong returns. Your risk-taking instinct is particularly well-calibrated now.", "challenging": "Impulsive spending and hasty investment decisions lead to preventable losses. Research thoroughly before committing resources."},
        {"positive": "Your decisive action in financial matters creates momentum that attracts opportunities. Physical energy translates into productive work hours and increased earning potential. A competitive financial environment favors your bold approach.", "challenging": "Overconfidence in a single financial strategy creates dangerous exposure. Diversify your approach to protect against volatility."},
    ],
    'Taurus': [
        {"positive": "Venus blesses your financial sector with steady, accumulating wealth. Long-term investments mature beautifully. Your patient, methodical approach to money management builds genuine financial security over time.", "challenging": "Over-attachment to material comfort leads to hoarding rather than strategic investing. Release money's emotional grip."},
        {"positive": "Your natural financial acuity reaches its peak — investments, savings, and asset-building all yield favorable results. Real estate, luxury goods, and beauty-related investments particularly reward your aesthetic sense.", "challenging": "Indulgence in luxury spending threatens savings goals. Enjoy pleasures mindfully within your financial plan."},
    ],
    'Gemini': [
        {"positive": "Mercury's analytical influence creates brilliant financial strategies. Communication-based income streams — writing, consulting, teaching, media — flourish. Diversified investments benefit from your versatile understanding of markets.", "challenging": "Scattered financial attention prevents focused wealth-building. Choose your most promising income stream and develop it deeply."},
        {"positive": "Intellectual curiosity leads to financial innovation. Information-based advantages create profitable opportunities. Social connections open doors to valuable financial partnerships and insider knowledge.", "challenging": "Gossip-based financial tips lead to costly mistakes. Research independently before acting on others' recommendations."},
    ],
    'Cancer': [
        {"positive": "The Moon illuminates intuitive financial decisions that prove remarkably accurate. Property investments, family wealth transfers, and home-based businesses yield significant returns. Emotional intelligence guides profitable relationship-based ventures.", "challenging": "Emotional spending driven by mood fluctuations undermines financial goals. Implement spending delays for non-essential purchases."},
        {"positive": "Your protective instinct creates secure financial structures that shelter and grow family wealth. Real estate and property-related investments particularly favor your natural understanding of shelter and security.", "challenging": "Fear-based financial decisions — hoarding or excessive caution — limit growth potential. Balance prudence with calculated risk."},
    ],
    'Leo': [
        {"positive": "The Sun empowers bold financial ventures that attract attention and profit. Creative investments, entertainment-related income, and leadership roles bring financial abundance. Your generous spirit paradoxically attracts more wealth.", "challenging": "Extravagant spending to maintain appearances drains resources. True wealth doesn't require display."},
        {"positive": "Your natural magnetism attracts financial opportunities and generous patrons. Creative monetization of talents proves particularly lucrative. Financial generosity creates karmic abundance cycles.", "challenging": "Financial overconfidence leads to risky investments without adequate research. Even Leos need financial advisors."},
    ],
    'Virgo': [
        {"positive": "Mercury's precision creates exceptional financial management. Detailed budgeting, careful investing, and systematic saving build wealth methodically. Your analytical abilities identify financial inefficiencies others overlook entirely.", "challenging": "Excessive frugality creates unnecessary deprivation. Enjoy the fruits of your labor — money is a tool, not just a number."},
        {"positive": "Your methodical approach to financial planning produces reliable, consistent returns. Healthcare, service industries, and detail-oriented businesses reward your analytical excellence. Financial organization brings peace of mind.", "challenging": "Perfectionist analysis paralysis prevents timely financial action. Sometimes a good-enough financial decision now beats a perfect one never made."},
    ],
    'Libra': [
        {"positive": "Venus graces financial partnerships and aesthetic investments with exceptional returns. Collaborative financial ventures, legal settlements, and beauty/luxury industries reward your refined sensibilities. Balance between saving and spending reaches ideal proportions.", "challenging": "Financial decisions driven by others' opinions rather than your own analysis lead to dissatisfaction. Trust your financial instincts."},
        {"positive": "Your diplomatic skills create profitable negotiations and business partnerships. Social capital translates into financial advantage. Artistic and creative investments benefit from your exceptional aesthetic judgment.", "challenging": "Indecisiveness about financial moves wastes time-sensitive opportunities. Set decision deadlines and honor them."},
    ],
    'Scorpio': [
        {"positive": "Pluto transforms your financial landscape through strategic restructuring. Shared resources, investments, inheritance, and deep research reveal hidden financial opportunities. Your penetrating insight uncovers profitable ventures others miss.", "challenging": "Financial secrecy or manipulation damages trusted partnerships. Transparent financial communication builds lasting wealth."},
        {"positive": "Your strategic financial mind operates at peak efficiency. Long-term investment strategies, financial investigation, and deep market analysis yield exceptional returns. Transformation of financial habits creates lasting security.", "challenging": "Obsessive focus on financial gain at all costs corrupts your values. Wealth must serve your integrity, not replace it."},
    ],
    'Sagittarius': [
        {"positive": "Jupiter, your ruling planet, expands financial horizons through international ventures, education-related income, publishing, and philosophy. Lucky breaks and serendipitous financial opportunities appear throughout this period.", "challenging": "Over-optimism about financial ventures leads to impractical investments. Temper enthusiasm with due diligence."},
        {"positive": "Your philosophical approach to wealth creates generous abundance cycles. Teaching, mentoring, and wisdom-sharing generate unexpected income. Travel-related financial ventures prove particularly profitable.", "challenging": "Overextension across too many financial interests dilutes returns. Focus resources on your most promising ventures."},
    ],
    'Capricorn': [
        {"positive": "Saturn rewards disciplined financial strategies with substantial, lasting wealth. Property investments, long-term savings plans, and institutional financial products yield exceptional results through patient, consistent application.", "challenging": "Over-prioritizing financial accumulation at the expense of life enjoyment creates a joyless relationship with money. Spend on experiences, not just security."},
        {"positive": "Your mountain goat determination builds financial empires brick by brick. Conservative, well-researched financial decisions compound over time into extraordinary wealth. Career earnings reach their highest level through persistent excellence.", "challenging": "Emotional suppression around financial stress creates anxiety and poor decisions. Address financial fears directly."},
    ],
    'Aquarius': [
        {"positive": "Uranus electrifies financial prospects through technology, innovation, and group-based ventures. Collaborative investments, social enterprises, and cutting-edge financial instruments yield exciting returns. Unconventional approaches to wealth creation prove visionary.", "challenging": "Financial unpredictability from following every innovative trend creates instability. Filter innovation through practical financial principles."},
        {"positive": "Your visionary approach to finance anticipates profitable trends before they emerge. Social networks provide valuable financial intelligence. Technology-related investments and humanitarian ventures balance profit with purpose beautifully.", "challenging": "Emotional detachment from financial consequences leads to impractical decisions. Connect your brilliant ideas to measurable financial outcomes."},
    ],
    'Pisces': [
        {"positive": "Neptune's intuitive influence guides financial decisions that prove surprisingly profitable. Creative income streams, healing professions, and spiritual businesses generate meaningful revenue. Compassionate service becomes financially rewarding.", "challenging": "Financial naivety or unrealistic expectations lead to losses. Balance intuition with practical financial verification."},
        {"positive": "Your empathic understanding of market needs creates uniquely valuable financial offerings. Artistic and spiritual ventures attract genuine financial support. Generous financial energy creates karmic abundance cycles.", "challenging": "Boundary issues in financial relationships lead to exploitation. Protect your financial interests with clear agreements and limits."},
    ],
}

# ── HEALTH ───────────────────────────────────

HEALTH: Dict[str, List[Dict[str, str]]] = {
    'Aries': [
        {"positive": "Mars empowers exceptional physical vitality and recovery capacity. Athletic pursuits, high-intensity exercise, and physical challenges yield outstanding results. Your natural energy reserves support ambitious health goals.", "challenging": "Mars' aggressive energy creates risk of inflammation, accidents, and headaches. Temper physical intensity with adequate recovery and cooling practices."},
        {"positive": "Your pioneering approach to fitness creates innovative health routines that others want to follow. Physical courage supports addressing health concerns proactively. Head and facial areas receive healing attention.", "challenging": "Impulsive health decisions — crash diets, extreme exercises — create more problems than they solve. Sustainable approaches serve you better."},
    ],
    'Taurus': [
        {"positive": "Venus enhances physical pleasure in healthy eating, gentle exercise, and sensory wellness practices. Your steady commitment to health routines creates lasting physical improvements. Throat and neck areas receive healing focus.", "challenging": "Overindulgence in rich foods and sedentary comfort undermines health goals. Enjoy sensual pleasures mindfully and in moderation."},
        {"positive": "Your patient approach to health transformation produces durable results. Consistent, moderate exercise and nutritious eating build a body that serves you beautifully for decades. Stability in health habits is your greatest strength.", "challenging": "Resistance to changing unhealthy habits despite knowing better creates long-term consequences. Small, consistent changes beat dramatic overhauls."},
    ],
    'Gemini': [
        {"positive": "Mercury supports nervous system health through varied, stimulating mental activities. Walking, social exercise, and intellectual engagement maintain vitality. Your adaptable nature easily incorporates new health information.", "challenging": "Nervous system overstimulation creates anxiety, insomnia, and scattered energy. Develop calming practices to balance your naturally active mind."},
        {"positive": "Your versatile approach to health keeps routines interesting and sustainable. Learning about nutrition and wellness motivates practical improvements. Social exercise — group classes, walking with friends — maintains consistency.", "challenging": "Inconsistency in health habits prevents lasting improvement. Choose a simple routine and stick with it despite changing interests."},
    ],
    'Cancer': [
        {"positive": "The Moon deepens your connection to body rhythms and emotional health. Intuitive eating, moon-cycle awareness, and emotional wellness practices produce profound healing. Stomach and digestive health receive positive attention.", "challenging": "Emotional eating and stress-related digestive issues require conscious attention. Develop non-food coping mechanisms for emotional challenges."},
        {"positive": "Your nurturing approach to self-care creates genuinely healing health practices. Home-cooked nutritious meals, comfortable sleep environments, and emotional security support robust health. Water-based activities particularly benefit you.", "challenging": "Mood-related health fluctuations require systematic tracking and management. Emotional health and physical health are deeply connected for Cancer natives."},
    ],
    'Leo': [
        {"positive": "The Sun radiates physical vitality and a powerful healing capacity. Heart health and cardiovascular fitness receive positive cosmic support. Creative physical expression — dance, performance, play — brings exceptional health benefits.", "challenging": "Pride may prevent seeking necessary medical attention. Regular check-ups and professional health guidance serve you better than self-diagnosis."},
        {"positive": "Your natural vitality inspires others to pursue healthier lifestyles. Leadership in group fitness or wellness communities amplifies your health benefits. Solar energy — sunlight exposure, vitamin D — particularly supports your health.", "challenging": "Overexertion and inability to rest creates cardiovascular strain. Schedule recovery as deliberately as you schedule exercise."},
    ],
    'Virgo': [
        {"positive": "Mercury's analytical approach creates optimized health systems. Detailed health tracking, precise nutrition, and systematic wellness routines produce measurable, impressive results. Digestive health particularly benefits from your careful approach.", "challenging": "Health anxiety and hypochondria waste medical resources and create unnecessary stress. Trust systematic tracking over obsessive symptom-checking."},
        {"positive": "Your methodical approach to wellness identifies and addresses health issues before they become serious. Preventive care, detailed health records, and evidence-based practices create a model of sustainable health.", "challenging": "Perfectionist health standards create stress that undermines the very health you're trying to optimize. Compassionate self-care outperforms rigid health regimens."},
    ],
    'Libra': [
        {"positive": "Venus enhances physical beauty through health practices that balance body and mind. Kidney health and hormonal balance receive positive support. Aesthetic motivation drives consistent wellness efforts that produce beautiful results inside and out.", "challenging": "Indecisiveness about health approaches wastes time and creates inconsistency. Choose one evidence-based approach and commit to it."},
        {"positive": "Your balanced approach to health — neither extreme nor negligent — creates sustainable wellness. Partner workouts and relationship harmony support physical health. Skin and appearance benefit from your natural health-consciousness.", "challenging": "People-pleasing at the expense of personal health needs undermines wellness. Your health boundaries deserve the same respect as your relational ones."},
    ],
    'Scorpio': [
        {"positive": "Pluto's transformative power creates profound health regeneration. Deep healing — whether physical, emotional, or psychological — reaches cellular levels. Your investigative nature leads to discovering effective health solutions others miss.", "challenging": "Reproductive and eliminative systems require careful attention. Secrecy about health issues prevents timely intervention and healing."},
        {"positive": "Your intense commitment to health transformation produces dramatic results. Detoxification, deep healing work, and transformative wellness practices yield extraordinary outcomes. Emotional health breakthroughs support physical healing.", "challenging": "Obsessive health behaviors — excessive fasting, extreme exercise, or orthorexia — create new problems. Balance intensity with moderation."},
    ],
    'Sagittarius': [
        {"positive": "Jupiter expands physical vitality and healing capacity. Hips, thighs, and liver receive positive cosmic attention. Adventure-based fitness — hiking, travel, outdoor activities — combines joy with excellent health benefits.", "challenging": "Overindulgence in food and drink strains liver and weight management. Enjoy life's pleasures within healthy limits."},
        {"positive": "Your optimistic approach to health creates self-fulfilling prophecies of wellness. Philosophical understanding of health as holistic — body, mind, spirit — guides comprehensive wellness practices. Active, outdoor lifestyles particularly benefit you.", "challenging": "Overconfidence in physical abilities creates injury risk. Warm up properly and respect your body's current limitations."},
    ],
    'Capricorn': [
        {"positive": "Saturn's disciplined influence creates exceptional health structure. Bones, joints, and skin receive careful attention. Your patient, consistent approach to health builds physical resilience that sustains you through life's challenges.", "challenging": "Overwork creates chronic stress, bone/joint problems, and premature aging. Rest and play are not optional luxuries — they're health necessities."},
        {"positive": "Your methodical health routines produce lasting physical benefits. Structured exercise, consistent nutrition, and preventive care create a body that supports your ambitious life goals for decades.", "challenging": "Emotional suppression manifests as physical ailments — headaches, joint pain, skin conditions. Emotional expression supports physical health."},
    ],
    'Aquarius': [
        {"positive": "Uranus brings innovative health approaches that produce surprising results. Circulatory system and neurological health receive attention. Technology-assisted wellness — health apps, wearables, biohacking — particularly benefits your forward-thinking approach.", "challenging": "Unpredictable health routines prevent the consistency that lasting wellness requires. Balance innovation with sustainable habits."},
        {"positive": "Your unconventional approach to health discovers methods that become mainstream later. Community health initiatives and group wellness projects amplify your health benefits. Nervous system regulation through technology supports wellbeing.", "challenging": "Emotional detachment from physical symptoms delays important health interventions. Tune into your body's signals with regular attention."},
    ],
    'Pisces': [
        {"positive": "Neptune enhances healing sensitivity and spiritual wellness practices. Feet health, immune function, and emotional wellbeing receive positive cosmic support. Meditation, yoga, and water-based healing arts particularly benefit your constitution.", "challenging": "Escapist health behaviors — substance use, emotional avoidance, excessive sleep — undermine physical health. Face health challenges with your characteristic compassion rather than avoidance."},
        {"positive": "Your empathic healing abilities benefit both yourself and others. Intuitive health guidance leads to effective treatment choices. Spiritual wellness practices create profound health transformations that complement conventional care.", "challenging": "Boundary issues in health — absorbing others' illness energy, neglecting own needs while caring for others — deplete your vital reserves. Protect your health while serving others."},
    ],
}

# ── LUCKY ATTRIBUTES ─────────────────────────

LUCKY_COLORS = {
    'Aries': ['Red', 'Orange', 'Crimson', 'Scarlet'],
    'Taurus': ['Green', 'Pink', 'Earth tones', 'Emerald'],
    'Gemini': ['Yellow', 'Light green', 'Silver', 'Lavender'],
    'Cancer': ['White', 'Silver', 'Sea green', 'Cream'],
    'Leo': ['Gold', 'Orange', 'Royal purple', 'Yellow'],
    'Virgo': ['Grey', 'Beige', 'Navy blue', 'Muted green'],
    'Libra': ['Pink', 'Lavender', 'Light blue', 'White'],
    'Scorpio': ['Maroon', 'Black', 'Deep red', 'Burgundy'],
    'Sagittarius': ['Purple', 'Turquoise', 'Saffron', 'Blue'],
    'Capricorn': ['Black', 'Dark brown', 'Grey', 'Deep green'],
    'Aquarius': ['Electric blue', 'Silver', 'Neon green', 'Aqua'],
    'Pisces': ['Sea green', 'Lavender', 'Aquamarine', 'White'],
}

LUCKY_NUMBERS = {
    'Aries': [1, 8, 17, 23],
    'Taurus': [2, 6, 15, 24],
    'Gemini': [5, 14, 23, 32],
    'Cancer': [2, 7, 11, 29],
    'Leo': [1, 5, 9, 19],
    'Virgo': [5, 14, 23, 32],
    'Libra': [6, 15, 24, 33],
    'Scorpio': [8, 11, 18, 27],
    'Sagittarius': [3, 9, 21, 33],
    'Capricorn': [8, 10, 19, 28],
    'Aquarius': [4, 11, 22, 29],
    'Pisces': [3, 7, 12, 21],
}

LUCKY_DIRECTIONS = {
    'Aries': ['East', 'North-East'],
    'Taurus': ['South-East', 'North'],
    'Gemini': ['North', 'East'],
    'Cancer': ['North-West', 'West'],
    'Leo': ['South', 'South-West'],
    'Virgo': ['North-East', 'South'],
    'Libra': ['North-West', 'South-East'],
    'Scorpio': ['South-West', 'North'],
    'Sagittarius': ['North-East', 'South-West'],
    'Capricorn': ['West', 'North-West'],
    'Aquarius': ['West', 'South-West'],
    'Pisces': ['South-East', 'North-West'],
}

PLANETARY_REMEDIES = {
    'Sun': ['Offer water to the rising Sun daily', 'Chant "Om Suryaya Namaha" 7 times at sunrise', 'Wear ruby or red coral', 'Donate wheat or jaggery on Sundays'],
    'Moon': ['Donate white rice or milk on Mondays', 'Chant "Om Chandraya Namaha" 108 times', 'Wear pearl or moonstone', 'Visit a temple or sacred water body on Mondays'],
    'Mars': ['Donate red lentils on Tuesdays', 'Chant "Om Mangalaya Namaha" 108 times', 'Wear red coral after proper consultation', 'Practice martial arts or vigorous exercise'],
    'Mercury': ['Donate green gram or green cloth on Wednesdays', 'Chant "Om Budhaya Namaha" 108 times', 'Wear emerald after proper consultation', 'Plant trees or support education of children'],
    'Jupiter': ['Donate yellow gram or turmeric on Thursdays', 'Chant "Om Gurave Namaha" 108 times', 'Wear yellow sapphire after consultation', 'Feed and support teachers and spiritual guides'],
    'Venus': ['Donate white sweets or clothes on Fridays', 'Chalt "Om Shukraya Namaha" 108 times', 'Wear diamond or white sapphire after consultation', 'Cultivate art, beauty, and harmonious relationships'],
    'Saturn': ['Donate black sesame or iron on Saturdays', 'Chant "Om Shanaye Namaha" 108 times', 'Wear blue sapphire after careful consultation', 'Serve the elderly and disadvantaged with humility'],
    'Rahu': ['Donate dark blue or black cloth', 'Chalt "Om Rahave Namaha" 108 times', 'Feed birds or stray animals', 'Practice meditation for mental clarity'],
    'Ketu': ['Donate multi-colored cloth or blankets', 'Chalt "Om Ketave Namaha" 108 times', 'Spend time in spiritual retreat or meditation', 'Feed dogs and show compassion to animals'],
}


# ──────────────────────────────────────────────
# Helper utilities
# ──────────────────────────────────────────────

def _dpick(items, chart, req):
    if not items:
        return items[0] if items else None
    moon = next((p for p in chart.get("planets",[]) if p.get("name")=="Moon"), {})
    asc = chart.get("ascendant", {})
    mlon = int(moon.get("longitude", 0)) % 360
    adeg = int(asc.get("degree", 0))
    try:
        now = __import__("datetime").datetime.now(__import__("pytz").timezone(req.timezone))
    except:
        now = __import__("datetime").datetime.now()
    s = f"{mlon}-{adeg}-{now.day}-{now.month}-{now.year % 100}"
    h = int(__import__("hashlib").md5(s.encode()).hexdigest()[:8], 16)
    return items[h % len(items)]

def _build_chart(date_of_birth: str, time_of_birth: str, lat: float, lon: float, tz: str):
    from ..main import to_julian, calc_planets, calc_houses
    jd = to_julian(date_of_birth, time_of_birth, tz)
    planets = calc_planets(jd, None, 'mean')
    houses_data = calc_houses(jd, lat, lon, planets, 'W')
    return {
        'jd': jd,
        'planets': planets,
        'houses': houses_data['houses'],
        'ascendant': houses_data['ascendant'],
    }


def _get_planet_info(planets: list, name: str) -> dict:
    for p in planets:
        if p['name'] == name:
            return p
    return {}


def _get_house_planets(houses: list, house_num: int) -> list:
    if 1 <= house_num <= len(houses):
        return houses[house_num - 1].get('planets', [])
    return []


def _get_sign_dignity(planet_name: str, sign: str) -> str:
    props = {
        'Sun':     {'exalted': 'Aries', 'debil': 'Libra', 'own': ['Leo']},
        'Moon':    {'exalted': 'Taurus', 'debil': 'Scorpio', 'own': ['Cancer']},
        'Mars':    {'exalted': 'Capricorn', 'debil': 'Cancer', 'own': ['Aries', 'Scorpio']},
        'Mercury': {'exalted': 'Virgo', 'debil': 'Pisces', 'own': ['Gemini', 'Virgo']},
        'Jupiter': {'exalted': 'Cancer', 'debil': 'Capricorn', 'own': ['Sagittarius', 'Pisces']},
        'Venus':   {'exalted': 'Pisces', 'debil': 'Virgo', 'own': ['Taurus', 'Libra']},
        'Saturn':  {'exalted': 'Libra', 'debil': 'Aries', 'own': ['Capricorn', 'Aquarius']},
    }
    info = props.get(planet_name)
    if not info:
        return 'Neutral'
    if info['exalted'] == sign:
        return 'Exalted'
    if info['debil'] == sign:
        return 'Debilitated'
    if sign in info.get('own', []):
        return 'Own Sign'
    return 'Friendly'


def _dasha_lord(jd: float) -> str:
    # Simplified: use Moon longitude to approximate current dasha lord
    import swisseph as swe
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    xx, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
    moon_lon = xx[0]
    # Vimshottari: each nakshatra is 13.333 degrees, dasha sequence repeats
    DASHA_SEQUENCE = ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury']
    DASHA_YEARS = {'Ketu': 7, 'Venus': 20, 'Sun': 6, 'Moon': 10, 'Mars': 7, 'Rahu': 18, 'Jupiter': 16, 'Saturn': 19, 'Mercury': 17}
    total_cycle = sum(DASHA_YEARS.values())  # 120 years
    total_days = total_cycle * 365.25
    position_in_cycle = (moon_lon % 360) / 360 * total_days
    accumulated = 0
    for lord in DASHA_SEQUENCE:
        lord_days = DASHA_YEARS[lord] * 365.25
        if position_in_cycle < accumulated + lord_days:
            return lord
        accumulated += lord_days
    return 'Jupiter'


def _pick_template(bank: dict, sign: str, chart: dict, req: HoroscopeRequest) -> dict:
    templates = bank.get(sign, bank.get('Aries', []))
    if not templates:
        return {"positive": "", "challenging": ""}
    return _dpick(templates, chart, req)


def _build_response(sign, period, overview, extra, chart, req):
    lucky_color = _dpick(LUCKY_COLORS.get(sign, ['White']), chart, req)
    lucky_num = _dpick(LUCKY_NUMBERS.get(sign, [1]), chart, req)
    lucky_dir = _dpick(LUCKY_DIRECTIONS.get(sign, ['North']), chart, req)

    dasha_lord = extra.get('dasha_lord', 'Jupiter')
    remedies = PLANETARY_REMEDIES.get(dasha_lord, PLANETARY_REMEDIES['Jupiter'])
    remedy = _dpick(remedies, chart, req)

    return {
        'sign': sign,
        'period': period,
        'overview': overview.get('positive', '') + ' ' + overview.get('challenging', ''),
        'career': extra.get('career', {}),
        'love': extra.get('love', {}),
        'finance': extra.get('finance', {}),
        'health': extra.get('health', {}),
        'luckyColor': lucky_color,
        'luckyNumber': lucky_num,
        'luckyDirection': lucky_dir,
        'remedy': remedy,
    }


def _determine_sign(req: HoroscopeRequest, chart: dict) -> str:
    from ..main import ZODIAC_SIGNS
    if req.zodiacSign and req.zodiacSign in ZODIAC_SIGNS:
        return req.zodiacSign
    moon = _get_planet_info(chart['planets'], 'Moon')
    return moon.get('sign', 'Aries')


def _period_label(period: str, req: HoroscopeRequest) -> str:
    today = datetime.now(pytz.timezone(req.timezone))
    if period == 'daily':
        return today.strftime('%B %d, %Y')
    elif period == 'weekly':
        start = today
        end = today + timedelta(days=6)
        return f"{start.strftime('%b %d')} - {end.strftime('%b %d, %Y')}"
    elif period == 'monthly':
        return today.strftime('%B %Y')
    else:
        return today.strftime('%Y')


def _build_full_response(req: HoroscopeRequest, chart: dict, overview_bank: dict,
                         extra_bank: dict, period: str) -> dict:
    
    from ..main import SIGN_LORDS
    sign = _determine_sign(req, chart)
    period_lbl = _period_label(period, req)
    dasha_lord = _dasha_lord(chart['jd'])

    overview_tmpl = _pick_template(overview_bank, sign, chart, req)
    career_tmpl = _pick_template(CAREER, sign, chart, req)
    love_tmpl = _pick_template(LOVE, sign, chart, req)
    finance_tmpl = _pick_template(FINANCE, sign, chart, req)
    health_tmpl = _pick_template(HEALTH, sign, chart, req)

    extra = {
        'dasha_lord': dasha_lord,
        'career': {
            'positive': career_tmpl['positive'],
            'challenging': career_tmpl['challenging'],
            'rulingPlanet': _get_planet_info(chart['planets'], 'Sun').get('signLord', 'Sun'),
        },
        'love': {
            'positive': love_tmpl['positive'],
            'challenging': love_tmpl['challenging'],
            'venusSign': _get_planet_info(chart['planets'], 'Venus').get('sign', 'Unknown'),
            'moonSign': _get_planet_info(chart['planets'], 'Moon').get('sign', 'Unknown'),
        },
        'finance': {
            'positive': finance_tmpl['positive'],
            'challenging': finance_tmpl['challenging'],
            'jupiterSign': _get_planet_info(chart['planets'], 'Jupiter').get('sign', 'Unknown'),
        },
        'health': {
            'positive': health_tmpl['positive'],
            'challenging': health_tmpl['challenging'],
            'marsSign': _get_planet_info(chart['planets'], 'Mars').get('sign', 'Unknown'),
        },
    }

    result = _build_response(sign, period_lbl, overview_tmpl, extra, chart, req)
    return {'status': 200, 'data': result}


# ──────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────

@router.post('/horoscope/daily')
def daily_horoscope(req: HoroscopeRequest):
    chart = _build_chart(req.dateOfBirth, req.timeOfBirth, req.latitude, req.longitude, req.timezone)
    return _build_full_response(req, chart, DAILY_OVERVIEW, {}, 'daily')


@router.post('/horoscope/weekly')
def weekly_horoscope(req: HoroscopeRequest):
    chart = _build_chart(req.dateOfBirth, req.timeOfBirth, req.latitude, req.longitude, req.timezone)
    return _build_full_response(req, chart, WEEKLY_OVERVIEW, {}, 'weekly')


@router.post('/horoscope/monthly')
def monthly_horoscope(req: HoroscopeRequest):
    chart = _build_chart(req.dateOfBirth, req.timeOfBirth, req.latitude, req.longitude, req.timezone)
    return _build_full_response(req, chart, MONTHLY_OVERVIEW, {}, 'monthly')


@router.post('/horoscope/yearly')
def yearly_horoscope(req: HoroscopeRequest):
    chart = _build_chart(req.dateOfBirth, req.timeOfBirth, req.latitude, req.longitude, req.timezone)
    return _build_full_response(req, chart, YEARLY_OVERVIEW, {}, 'yearly')


@router.post('/horoscope/career')
def career_horoscope(req: HoroscopeRequest):
    from ..main import SIGN_LORDS
    chart = _build_chart(req.dateOfBirth, req.timeOfBirth, req.latitude, req.longitude, req.timezone)
    sign = _determine_sign(req, chart)
    period_lbl = _period_label('monthly', req)
    dasha_lord = _dasha_lord(chart['jd'])
    career_tmpl = _pick_template(CAREER, sign, chart, req)
    lucky_color = _dpick(LUCKY_COLORS.get(sign, ['White']), chart, req)
    lucky_num = _dpick(LUCKY_NUMBERS.get(sign, [1]), chart, req)
    lucky_dir = _dpick(LUCKY_DIRECTIONS.get(sign, ['North']), chart, req)
    remedies = PLANETARY_REMEDIES.get(dasha_lord, PLANETARY_REMEDIES['Jupiter'])

    tenth_house_planets = _get_house_planets(chart['houses'], 10)
    sun_info = _get_planet_info(chart['planets'], 'Sun')
    saturn_info = _get_planet_info(chart['planets'], 'Saturn')

    return {
        'status': 200,
        'data': {
            'sign': sign,
            'period': period_lbl,
            'overview': f"{career_tmpl['positive']} {career_tmpl['challenging']}",
            'career': {
                'positive': career_tmpl['positive'],
                'challenging': career_tmpl['challenging'],
                'tenthHousePlanets': tenth_house_planets,
                'sunSign': sun_info.get('sign', 'Unknown'),
                'sunDignity': _get_sign_dignity('Sun', sun_info.get('sign', 'Unknown')),
                'saturnSign': saturn_info.get('sign', 'Unknown'),
                'saturnDignity': _get_sign_dignity('Saturn', saturn_info.get('sign', 'Unknown')),
                'tenthHouseLord': SIGN_LORDS.get(chart['houses'][9].get('sign', 'Aries'), 'Unknown') if len(chart['houses']) >= 10 else 'Unknown',
            },
            'love': {},
            'finance': {},
            'health': {},
            'luckyColor': lucky_color,
            'luckyNumber': lucky_num,
            'luckyDirection': lucky_dir,
            'remedy': _dpick(remedies, chart, req),
        }
    }


@router.post('/horoscope/love')
def love_horoscope(req: HoroscopeRequest):
    from ..main import SIGN_LORDS
    chart = _build_chart(req.dateOfBirth, req.timeOfBirth, req.latitude, req.longitude, req.timezone)
    sign = _determine_sign(req, chart)
    period_lbl = _period_label('monthly', req)
    dasha_lord = _dasha_lord(chart['jd'])
    love_tmpl = _pick_template(LOVE, sign, chart, req)
    lucky_color = _dpick(LUCKY_COLORS.get(sign, ['White']), chart, req)
    lucky_num = _dpick(LUCKY_NUMBERS.get(sign, [1]), chart, req)
    lucky_dir = _dpick(LUCKY_DIRECTIONS.get(sign, ['North']), chart, req)
    remedies = PLANETARY_REMEDIES.get(dasha_lord, PLANETARY_REMEDIES['Jupiter'])

    seventh_house_planets = _get_house_planets(chart['houses'], 7)
    venus_info = _get_planet_info(chart['planets'], 'Venus')
    moon_info = _get_planet_info(chart['planets'], 'Moon')

    return {
        'status': 200,
        'data': {
            'sign': sign,
            'period': period_lbl,
            'overview': f"{love_tmpl['positive']} {love_tmpl['challenging']}",
            'career': {},
            'love': {
                'positive': love_tmpl['positive'],
                'challenging': love_tmpl['challenging'],
                'seventhHousePlanets': seventh_house_planets,
                'venusSign': venus_info.get('sign', 'Unknown'),
                'venusDignity': _get_sign_dignity('Venus', venus_info.get('sign', 'Unknown')),
                'moonSign': moon_info.get('sign', 'Unknown'),
                'seventhHouseLord': SIGN_LORDS.get(chart['houses'][6].get('sign', 'Libra'), 'Unknown') if len(chart['houses']) >= 7 else 'Unknown',
            },
            'finance': {},
            'health': {},
            'luckyColor': lucky_color,
            'luckyNumber': lucky_num,
            'luckyDirection': lucky_dir,
            'remedy': _dpick(remedies, chart, req),
        }
    }


@router.post('/horoscope/finance')
def finance_horoscope(req: HoroscopeRequest):
    from ..main import SIGN_LORDS
    chart = _build_chart(req.dateOfBirth, req.timeOfBirth, req.latitude, req.longitude, req.timezone)
    sign = _determine_sign(req, chart)
    period_lbl = _period_label('monthly', req)
    dasha_lord = _dasha_lord(chart['jd'])
    finance_tmpl = _pick_template(FINANCE, sign, chart, req)
    lucky_color = _dpick(LUCKY_COLORS.get(sign, ['White']), chart, req)
    lucky_num = _dpick(LUCKY_NUMBERS.get(sign, [1]), chart, req)
    lucky_dir = _dpick(LUCKY_DIRECTIONS.get(sign, ['North']), chart, req)
    remedies = PLANETARY_REMEDIES.get(dasha_lord, PLANETARY_REMEDIES['Jupiter'])

    second_house_planets = _get_house_planets(chart['houses'], 2)
    eleventh_house_planets = _get_house_planets(chart['houses'], 11)
    jupiter_info = _get_planet_info(chart['planets'], 'Jupiter')
    venus_info = _get_planet_info(chart['planets'], 'Venus')

    return {
        'status': 200,
        'data': {
            'sign': sign,
            'period': period_lbl,
            'overview': f"{finance_tmpl['positive']} {finance_tmpl['challenging']}",
            'career': {},
            'love': {},
            'finance': {
                'positive': finance_tmpl['positive'],
                'challenging': finance_tmpl['challenging'],
                'secondHousePlanets': second_house_planets,
                'eleventhHousePlanets': eleventh_house_planets,
                'jupiterSign': jupiter_info.get('sign', 'Unknown'),
                'jupiterDignity': _get_sign_dignity('Jupiter', jupiter_info.get('sign', 'Unknown')),
                'venusSign': venus_info.get('sign', 'Unknown'),
                'secondHouseLord': SIGN_LORDS.get(chart['houses'][1].get('sign', 'Taurus'), 'Unknown') if len(chart['houses']) >= 2 else 'Unknown',
                'eleventhHouseLord': SIGN_LORDS.get(chart['houses'][10].get('sign', 'Aquarius'), 'Unknown') if len(chart['houses']) >= 11 else 'Unknown',
            },
            'health': {},
            'luckyColor': lucky_color,
            'luckyNumber': lucky_num,
            'luckyDirection': lucky_dir,
            'remedy': _dpick(remedies, chart, req),
        }
    }


@router.post('/horoscope/health')
def health_horoscope(req: HoroscopeRequest):
    chart = _build_chart(req.dateOfBirth, req.timeOfBirth, req.latitude, req.longitude, req.timezone)
    sign = _determine_sign(req, chart)
    period_lbl = _period_label('monthly', req)
    dasha_lord = _dasha_lord(chart['jd'])
    health_tmpl = _pick_template(HEALTH, sign, chart, req)
    lucky_color = _dpick(LUCKY_COLORS.get(sign, ['White']), chart, req)
    lucky_num = _dpick(LUCKY_NUMBERS.get(sign, [1]), chart, req)
    lucky_dir = _dpick(LUCKY_DIRECTIONS.get(sign, ['North']), chart, req)
    remedies = PLANETARY_REMEDIES.get(dasha_lord, PLANETARY_REMEDIES['Jupiter'])

    first_house_planets = _get_house_planets(chart['houses'], 1)
    sixth_house_planets = _get_house_planets(chart['houses'], 6)
    mars_info = _get_planet_info(chart['planets'], 'Mars')
    saturn_info = _get_planet_info(chart['planets'], 'Saturn')

    return {
        'status': 200,
        'data': {
            'sign': sign,
            'period': period_lbl,
            'overview': f"{health_tmpl['positive']} {health_tmpl['challenging']}",
            'career': {},
            'love': {},
            'finance': {},
            'health': {
                'positive': health_tmpl['positive'],
                'challenging': health_tmpl['challenging'],
                'firstHousePlanets': first_house_planets,
                'sixthHousePlanets': sixth_house_planets,
                'marsSign': mars_info.get('sign', 'Unknown'),
                'marsDignity': _get_sign_dignity('Mars', mars_info.get('sign', 'Unknown')),
                'saturnSign': saturn_info.get('sign', 'Unknown'),
                'saturnDignity': _get_sign_dignity('Saturn', saturn_info.get('sign', 'Unknown')),
                'ascendantSign': chart['ascendant'].get('sign', 'Unknown'),
            },
            'luckyColor': lucky_color,
            'luckyNumber': lucky_num,
            'luckyDirection': lucky_dir,
            'remedy': _dpick(remedies, chart, req),
        }
    }
