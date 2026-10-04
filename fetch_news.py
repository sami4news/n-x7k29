import json, re, time, urllib.request, html
import xml.etree.ElementTree as ET
from urllib.parse import quote
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone, timedelta

def GN(q, days=1):
    return "https://news.google.com/rss/search?q=" + quote(q + " when:%dd" % days) + "&hl=ar&gl=SA&ceid=SA:ar"

# ("GN", عبارة بحث) = أخبار جوجل بحسب موضوع قروبك، وغيرها روابط RSS مباشرة
FEEDS = [
 ("GN","إنذار أحمر المركز الوطني للأرصاد"),
 ("GN","الدفاع المدني الإنذار المبكر السعودية"),
 ("GN","اعتراض مسيرة السعودية الحوثي"),
 ("GN","إيران أمريكا إسرائيل تصعيد"),
 ("GN","مضيق هرمز"),
 ("GN","عاجل السعودية"),
 # أخبار الطائف (نافذة 3 أيام لأن أخبارها أقل عددًا)
 ("GT","الطائف"),
 ("GT","أمانة الطائف"),
 ("GT","محافظة الطائف"),
 ("GT","الطائف أمطار"),
 ("GT","جامعة الطائف"),
 ("GT","إمارة منطقة مكة الطائف"),
 ("الجزيرة","https://www.aljazeera.net/aljazeerarss/a7c186be-1baa-4bd4-9d80-a84db769f779/73d0e1b4-532f-45ef-b135-bfdb83b6f7b8"),
 ("BBC عربي","https://feeds.bbci.co.uk/arabic/rss.xml"),
 ("سكاي نيوز عربية","https://www.skynewsarabia.com/web/rss"),
 ("العربية","https://www.alarabiya.net/feed/rss2/ar.xml"),
 ("الشرق الأوسط","https://aawsat.com/feed"),
 ("فرانس 24","https://www.france24.com/ar/rss"),
]
KW = {
 "urgent": ["عاجل","حصري"],
 "wx": ["الأرصاد","إنذار أحمر","إنذار برتقالي","أمطار غزيرة","الدفاع المدني","صفارات الإنذار","الإنذار المبكر","تعليق الدراسة","الدراسة عن بعد","الدوام عن بعد"],
 "war": ["غزة","حرب","قصف","غارة","غارات","صاروخ","صواريخ","هجوم","الحوثي","الحوثيين","أوكرانيا","معارك","مسيّرة","مسيرة","إسرائيل","لبنان","إيران","هرمز","الحرس الثوري","اعتراض","انفجارات","تعبئة","البنتاغون"],
 "sa": ["السعود","الرياض","جدة","مكة","المدينة المنورة","ولي العهد","خادم الحرمين","الملك سلمان","نيوم","الدمام","أبها","الطائف","تبوك"],
 "eco": ["نفط","أسهم","الذهب","اقتصاد","بورصة","الدولار","أوبك","تضخم","الفائدة","الديزل","البنزين","ميزانية","أرامكو","استثمار"],
}
POL = ["رئيس","الرئيس","وزير","وزارة","حكومة","الحكومة","ترامب","بوتين","نتنياهو","بايدن","زيلينسكي","البيت الأبيض","الكرملين","الأمم المتحدة","مجلس الأمن","الناتو","الخارجية","سفارة","قنصلية","قمة","اتفاق","اتفاقية","مفاوضات","عقوبات","انتخابات","الجيش","قوات","قوة","سوريا","العراق","اليمن","مصر","الأردن","الكويت","الإمارات","قطر","البحرين","عُمان","تركيا","روسيا","الصين","أمريكا","أميركا","الولايات المتحدة","إسرائيل","فلسطين","غزة","لبنان","إيران","الخليج","مجلس التعاون","أوروبا","الاتحاد الأوروبي","هجوم","حادث","طائرة","انفجار","اعتقال","وفاة","مقتل","إصابة","ضحايا","أمن","أمني","الداخلية","الدفاع","طوارئ","زلزال","حريق","فيضانات","عاصفة"]
# الطائف: كلمة كاملة حتى لا تلتقط "الطائفة/الطائفية"
TAIF_RX = re.compile(r"(?<![\u0621-\u064A])(?:و|ب|ل|ف|ك)?(?:ال)?(?:طائف|الهدا|الحوية|ثقيف)(?![\u0621-\u064A])")
ORDER = ["urgent","wx","war","sa","eco","me"]
KW["me"] = POL

# فلاتر الاستبعاد: مطابقة كلمة كاملة (حتى لا تُحذف كلمات مثل "استهداف" أو "مذكرة")
SPORT = ["مباراة","مباريات","كأس","دوري","منتخب","الهلال","النصر","الأهلي","كرة","لاعب","لاعبين","بطولة","رياضة","رياضي","مدرب","ميسي","رونالدو","مدريد","برشلونة","ليفربول","مانشستر","تشيلسي","أرسنال","الفورمولا","الجائزة الكبرى","التنس","أولمبي","الميركاتو","يويفا","فيفا","حارس مرمى","تسجيل هدف","خليجي","البادل","بادل","الألعاب","ألعاب","الآسيوية","منافسات","ميدالية","ميداليات","ذهبية","فضية","برونزية","لاعبة","لاعبات","سباحة","جودو","تايكوندو","كاراتيه","الغولف","الجولف","ملاكمة","نزال","الأولمبية","أولمبية","دورة","الدورة","بطل","البطل","أبطال","تدريبات","الجولة","الملعب","ملعب","الفريق","فريق","نادي","أندية"]
MAGAZINE = ["مشاهير","فنانة","فنان","مسلسل","مسلسلات","فيلم","أفلام","سينما","موضة","أزياء","عارضة","رجيم","ريجيم","وصفة","وصفات","أبراج","حظك","ديكور","ماكياج","سياحة","تخفيضات","برعاية","محتوى مدفوع","لن تصدق","صادم","فضيحة","تريند","ترند","حفل زفاف","خطوبة","انفصال","أسرار","حوار","مقابلة","قصة نجاح","مهرجان","معرض","احتفال","احتفالات","حفل","كتاب","رواية","شعر","ثقافة","سيرة","ذكرى","بالصور","بالفيديو والصور","نصائح","فوائد الصحية","تعرف على"]
UNVERIFIED = ["شائعة","شائعات","يُشاع","يشاع","مزعوم","مزعومة","غير مؤكد","غير مؤكدة","فبركة","مفبرك","مفبركة"]
BAD_PATH = ["/sport","/sports","riyada","/lifestyle","/fann","/art/","/celebrit","/women","/beauty","/food","/travel","/cars","/entertainment"]
AR = "\u0621-\u064A"
RX = re.compile(r"(?<![%s])(?:و|ب|ل|ف|ك)?(?:ال)?(?:%s)(?![%s])" % (AR, "|".join(map(re.escape, SPORT+MAGAZINE+UNVERIFIED)), AR))

SOFT = re.compile(r"ل\s*ـ?\s*[«\"]?الشرق الأوسط[»\"]?\s*:|^رأي|^مقال|^تحليل|^شاهد|^إنفوغراف")

def blocked(title, summ, link):
    if SOFT.search(title): return True
    if any(p in link.lower() for p in BAD_PATH): return True
    return bool(RX.search(title + " " + summ))

def classify(t):
    for c in ORDER:
        if any(k in t for k in KW[c]): return c
    return None

def clean(s):
    return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",s or ""))).strip()

def img_of(it):
    for el in it.iter():
        tag = el.tag.split("}")[-1]
        if tag in ("content","thumbnail","enclosure"):
            u, t = el.get("url"), el.get("type","")
            if u and (tag!="enclosure" or t.startswith("image")) and not t.startswith("video"):
                return u
    m = re.search(r'<img[^>]+src=["\']([^"\']+)', ET.tostring(it, encoding="unicode"))
    return html.unescape(m.group(1)) if m else ""

def video_of(it):
    for el in it.iter():
        u = el.get("url") or ""
        if el.get("type","").startswith("video") or u.endswith(".mp4"):
            return u
    return ""


def meta(h, prop):
    for pat in (r'<meta[^>]+(?:property|name)=["\']%s["\'][^>]*content=["\']([^"\']+)' % prop,
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]*(?:property|name)=["\']%s["\']' % prop):
        m = re.search(pat, h, re.I)
        if m: return html.unescape(m.group(1))
    return ""

def enrich(it):
    """يجلب صورة/فيديو الخبر من صفحة المصدر (og:image / og:video)"""
    try:
        req = urllib.request.Request(it["s"], headers={"User-Agent":"Mozilla/5.0"})
        h = urllib.request.urlopen(req, timeout=8).read(250000).decode("utf-8","ignore")
    except Exception:
        return
    og = meta(h, "og:image")
    if og: it["img"] = og  # صورة الصفحة أعلى جودة من مصغّرة RSS
    if not it["vid"]: it["vid"] = meta(h, "og:video:secure_url") or meta(h, "og:video")


# ===== تطبيع النص العربي =====
_MAP = str.maketrans("أإآٱىةؤئ٠١٢٣٤٥٦٧٨٩", "اااايهوي0123456789")
def norm(s):
    s = re.sub(r"[\u064B-\u0652\u0640]", "", (s or "").lower())
    return s.translate(_MAP)

STOP = set(norm(w) for w in "في على من الى إلى عن مع بعد قبل بين خلال حول ضد هذا هذه ذلك التي الذي الذين قال قالت يقول ان إن كان كانت لا لم لن قد تم يتم ثم او أو كما حتى عند منذ بسبب نحو اثر إثر بشأن لدى اليوم امس غدا كل عدة اكثر بعض وفق حسب بحسب".split())

def sig(title):
    out = set()
    for w in re.findall(r"[\u0621-\u064A0-9a-z]+", norm(title)):
        if w.isdigit(): out.add(w); continue   # الأرقام تُحفظ مهما قصرت (للتفريق بين إنذار 25 وإنذار 26)
        w = re.sub(r"^(وال|بال|لل|فال|كال|ال)", "", w)
        if len(w) > 3: w = re.sub(r"[اه]$", "", w)
        if len(w) >= 3 and w not in STOP: out.add(w)
    return out

def same_story(a, b):
    """هل العنوانان لنفس الخبر؟ تشابه كلمات + حارس أرقام + حارس زمن"""
    if abs(a["ts"] - b["ts"]) > 10 * 3600: return False
    A, B = a["sig"], b["sig"]
    if not A or not B: return False
    na = {w for w in A if w.isdigit()}; nb = {w for w in B if w.isdigit()}
    if na and nb and na != nb: return False   # تواريخ/أعداد مختلفة = خبر مختلف
    inter = len(A & B)
    if inter < 3: return False
    jac = inter / len(A | B)
    ovl = inter / min(len(A), len(B))
    return jac >= 0.5 or (ovl >= 0.8 and inter >= 4)

# ===== موثوقية المصدر =====
def canon(name):
    n = norm(name)
    n = re.sub(r"^(صحيفه|جريده|موقع|قناه|وكاله|شبكه|بوابه|مجله)\s+", "", n)
    return re.sub(r"[\s\.\-_]*(نت|\.com|\.net)$", "", n).strip()

def _m(n, key):
    return n == key or n.startswith(key + " ") or n.startswith(key + ".")

OFFICIAL = ["واس", "الانباء السعوديه", "الاخباريه", "الاخبارية", "وزاره", "الدفاع المدني", "المركز الوطني", "الارصاد",
            "الامن العام", "المرور", "مرور", "شرطه", "الجوازات", "الهلال الاحمر", "هيئه", "امانه", "اماره", "جامعه", "spa", "saudi press agency"]
TRUSTED = ["العربيه", "الحدث", "الجزيره", "الجزيره نت", "bbc", "سكاي نيوز", "الشرق الاوسط", "فرانس 24", "france 24", "رويترز",
           "reuters", "الشرق", "اندبندنت", "independent", "cnn", "عكاظ", "الرياض", "الوطن", "المدينه", "اليوم", "سبق",
           "الاقتصاديه", "اخبار 24", "الانباء", "الاناضول", "anadolu", "فرانس برس", "afp", "associated press", "الاتحاد",
           "البيان", "الخليج", "القبس", "الراي", "دويتشه فيله", "dw", "al arabiya", "al jazeera", "aljazeera", "sky news",
           "asharq", "the national", "arab news", "عرب نيوز", "saudi gazette", "okaz", "اقتصاد الشرق"]
OFF_N = [norm(x) for x in OFFICIAL]
TRU_N = [norm(x) for x in TRUSTED]

def trust(name):
    """2 = رسمي، 1 = موثوق، 0 = غير معروف"""
    n = canon(name)
    if any(_m(n, k) for k in OFF_N): return 2
    if any(_m(n, k) for k in TRU_N): return 1
    return 0

def cat_rank(c): return ORDER.index(c) if c in ORDER else 99

def cluster(cands):
    """يدمج الأخبار المتشابهة في بطاقة واحدة مع عدّ المصادر المختلفة"""
    cands.sort(key=lambda x: -x["ts"])
    groups = []
    for c in cands:
        for g in groups:
            if any(same_story(c, m) for m in g):
                g.append(c); break
        else:
            groups.append([c])
    out = []
    for g in groups:
        rep = max(g, key=lambda x: (x["tr"] * 3 + (2 if x["img"] else 0) + (1 if x["b"] else 0) + (1 if x["vid"] else 0), x["ts"]))
        seen_src, srcs, alts = set(), [], []
        for m in sorted(g, key=lambda x: (-x["tr"], -x["ts"])):
            cs = canon(m["src"])
            if cs in seen_src: continue
            seen_src.add(cs); srcs.append(m["src"])
            if m is not rep and len(alts) < 6: alts.append({"src": m["src"], "s": m["s"]})
        it = {k: v for k, v in rep.items() if k != "sig"}
        if not it["img"]:
            for m in g:
                if m["img"]: it["img"], it["vid"] = m["img"], it["vid"] or m["vid"]; break
        it["c"] = min((m["c"] for m in g), key=cat_rank)
        it["tf"] = any(m["tf"] for m in g)
        it["tr"] = max(m["tr"] for m in g)
        it["n"] = len(seen_src)
        it["srcs"] = srcs[:8]
        it["alts"] = alts
        out.append(it)
    return out

if __name__ == "__main__":
    cands, links = [], set()
    now = datetime.now(timezone.utc)
    for name, q in FEEDS:
        gn = name in ("GN", "GT")
        url = (GN(q, 3) if name == "GT" else GN(q)) if gn else q
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            root = ET.fromstring(urllib.request.urlopen(req, timeout=25).read())
        except Exception as e:
            print("FAIL", name, q[:40], e); continue
        for it in root.iter("item"):
            g = lambda k: (it.findtext(k) or "")
            title, link = clean(g("title")), g("link").strip()
            if not title or not link or link in links: continue
            src, summ = name, clean(g("description"))[:240]
            if gn:
                summ = ""
                if " - " in title: title, src = title.rsplit(" - ", 1)
            src = src.strip()
            if len(title) < 28 or "؟" in title or re.match(r"^\d+\s", title): continue
            try: d = parsedate_to_datetime(g("pubDate"))
            except Exception: d = now
            if d.tzinfo is None: d = d.replace(tzinfo=timezone.utc)
            tf = bool(TAIF_RX.search(title + " " + summ))
            if now - d > timedelta(hours=72 if tf else 48): continue
            if blocked(title, summ, link): continue
            cat = classify(title + " " + summ)
            if not cat: continue
            links.add(link)
            cands.append({"t": title, "b": summ, "s": link, "src": src, "c": cat, "tf": tf,
                          "img": img_of(it), "vid": video_of(it), "ts": int(d.timestamp()),
                          "tr": trust(src), "sig": sig(title)})
    items = cluster(cands)
    items.sort(key=lambda x: -x["ts"])
    items = items[:200]
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(8) as ex:
        list(ex.map(enrich, [i for i in items if not i["img"] and "news.google.com" not in i["s"]][:60]))
    if not items:
        # حماية: إذا تعطلت المصادر كلها لا نفرّغ الموقع، نبقي آخر أخبار سليمة
        try:
            old = json.load(open("news.json", encoding="utf-8"))
            if old.get("items"):
                print("لا أخبار جديدة (تعطل المصادر؟) — أُبقي على الملف السابق"); raise SystemExit(0)
        except (OSError, ValueError):
            pass
    json.dump({"updated": int(time.time()), "items": items}, open("news.json", "w", encoding="utf-8"), ensure_ascii=False)
    print("candidates:", len(cands), "-> cards:", len(items), "| multi-source:", sum(1 for i in items if i["n"] > 1))
