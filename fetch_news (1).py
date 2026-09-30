import json, re, time, urllib.request, html
import xml.etree.ElementTree as ET
from urllib.parse import quote
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone, timedelta

def GN(q):
    return "https://news.google.com/rss/search?q=" + quote(q + " when:1d") + "&hl=ar&gl=SA&ceid=SA:ar"

# ("GN", عبارة بحث) = أخبار جوجل بحسب موضوع قروبك، وغيرها روابط RSS مباشرة
FEEDS = [
 ("GN","إنذار أحمر المركز الوطني للأرصاد"),
 ("GN","الدفاع المدني الإنذار المبكر السعودية"),
 ("GN","اعتراض مسيرة السعودية الحوثي"),
 ("GN","إيران أمريكا إسرائيل تصعيد"),
 ("GN","مضيق هرمز"),
 ("GN","عاجل السعودية"),
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
ORDER = ["urgent","wx","war","sa","eco"]

# فلاتر الاستبعاد: مطابقة كلمة كاملة (حتى لا تُحذف كلمات مثل "استهداف" أو "مذكرة")
SPORT = ["مباراة","مباريات","كأس","دوري","منتخب","الهلال","النصر","الأهلي","كرة","لاعب","لاعبين","بطولة","رياضة","رياضي","مدرب","ميسي","رونالدو","مدريد","برشلونة","ليفربول","مانشستر","تشيلسي","أرسنال","الفورمولا","الجائزة الكبرى","التنس","أولمبي","الميركاتو","يويفا","فيفا","حارس مرمى","تسجيل هدف","خليجي"]
MAGAZINE = ["مشاهير","فنانة","فنان","مسلسل","مسلسلات","فيلم","أفلام","سينما","موضة","أزياء","عارضة","رجيم","ريجيم","وصفة","وصفات","أبراج","حظك","ديكور","ماكياج","سياحة","تخفيضات","برعاية","محتوى مدفوع","لن تصدق","صادم","فضيحة","تريند","ترند","حفل زفاف","خطوبة","انفصال","أسرار"]
UNVERIFIED = ["شائعة","شائعات","يُشاع","يشاع","مزعوم","مزعومة","غير مؤكد","غير مؤكدة","فبركة","مفبرك","مفبركة"]
BAD_PATH = ["/sport","/sports","riyada","/lifestyle","/fann","/art/","/celebrit","/women","/beauty","/food","/travel","/cars","/entertainment"]
AR = "\u0621-\u064A"
RX = re.compile(r"(?<![%s])(?:و|ب|ل|ف|ك)?(?:ال)?(?:%s)(?![%s])" % (AR, "|".join(map(re.escape, SPORT+MAGAZINE+UNVERIFIED)), AR))

def blocked(title, summ, link):
    if any(p in link.lower() for p in BAD_PATH): return True
    return bool(RX.search(title + " " + summ))

def classify(t):
    for c in ORDER:
        if any(k in t for k in KW[c]): return c
    return "me"

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

if __name__ == "__main__":
    items, seen = [], set()
    now = datetime.now(timezone.utc)
    for name, q in FEEDS:
        gn = name == "GN"
        url = GN(q) if gn else q
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
            root = ET.fromstring(urllib.request.urlopen(req, timeout=25).read())
        except Exception as e:
            print("FAIL", name, q[:40], e); continue
        for it in root.iter("item"):
            g = lambda k: (it.findtext(k) or "")
            title, link = clean(g("title")), g("link").strip()
            if not title or not link: continue
            src, summ = name, clean(g("description"))[:240]
            if gn:
                summ = ""
                if " - " in title: title, src = title.rsplit(" - ", 1)
            key = re.sub(r"\W+","",title)[:35]
            if key in seen: continue
            try: d = parsedate_to_datetime(g("pubDate"))
            except Exception: d = now
            if d.tzinfo is None: d = d.replace(tzinfo=timezone.utc)
            if now - d > timedelta(hours=48): continue
            if blocked(title, summ, link): continue
            seen.add(key)
            items.append({"t":title,"b":summ,"s":link,"src":src,"c":classify(title+" "+summ),
                          "img":img_of(it),"vid":video_of(it),"ts":int(d.timestamp())})
    items.sort(key=lambda x:-x["ts"])
    json.dump({"updated":int(time.time()),"items":items[:200]}, open("news.json","w",encoding="utf-8"), ensure_ascii=False)
    print("items:", len(items))
