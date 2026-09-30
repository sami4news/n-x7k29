import json, re, time, urllib.request, html
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone, timedelta

FEEDS = [
 ("الجزيرة","https://www.aljazeera.net/aljazeerarss/a7c186be-1baa-4bd4-9d80-a84db769f779/73d0e1b4-532f-45ef-b135-bfdb83b6f7b8"),
 ("BBC عربي","https://feeds.bbci.co.uk/arabic/rss.xml"),
 ("سكاي نيوز عربية","https://www.skynewsarabia.com/web/rss"),
 ("العربية","https://www.alarabiya.net/feed/rss2/ar.xml"),
 ("الشرق الأوسط","https://aawsat.com/feed"),
]
KW = {
 "urgent": ["عاجل","حصري"],
 "war": ["غزة","حرب","قصف","غارة","صاروخ","هجوم","الحوثي","أوكرانيا","جيش","معارك","مسيّرة","مسيرة","إسرائيل","لبنان","إيران"],
 "sa": ["السعود","الرياض","جدة","مكة","المدينة المنورة","ولي العهد","خادم الحرمين","نيوم","الدمام","أبها","واس"],
 "eco": ["نفط","أسهم","الذهب","اقتصاد","بورصة","الدولار","أوبك","تضخم","الفائدة","أرباح","استثمار","سوق"],
}
ORDER = ["urgent","war","sa","eco"]


# ===== فلاتر الاستبعاد =====
SPORT = ["مباراة","مباريات","كأس","دوري","هدف","منتخب","الهلال","النصر","الاتحاد السعودي","الأهلي","كرة","لاعب","لاعبي","بطولة","رياضة","رياضي","مدرب","ميسي","رونالدو","ريال مدريد","برشلونة","ليفربول","مانشستر","تشيلسي","أرسنال","الفورمولا","جائزة البحرين الكبرى","سباق","التنس","أولمبي","الميركاتو","انتقال اللاعب","يويفا","فيفا","الدوري الإنجليزي","الدوري السعودي","دوري أبطال","خليجي","نجم سابق","حارس مرمى","مهاجم"]
MAGAZINE = ["مشاهير","نجمة","نجم الغناء","فنانة","فنان","مسلسل","فيلم","سينما","موضة","أزياء","عارضة","جمال","رجيم","ريجيم","وصفة","أبراج","حظك","برج","ديكور","ماكياج","مطبخ","سياحة","سفر","عروض","خصم","تخفيضات","إعلان","برعاية","محتوى مدفوع","نمط حياة","طريقة","فوائد","أسرار","لن تصدق","صادم","فضيحة","تريند","ترند","حفل زفاف","طلاق","خطوبة","انفصال","زواج"]
UNVERIFIED = ["شائعة","شائعات","يُشاع","يشاع","مزعوم","مزعومة","تسريبات","تسريب","غير مؤكد","غير مؤكدة","حسب مصادر لم","زعم","زعمت","ادعاء","مدعيا","مدعيًا","نفي","تكذيب","فبركة","مفبرك"]
BAD_PATH = ["/sport","/sports","riyada","/lifestyle","/fann","/art/","/celebrit","/women","/beauty","/food","/travel","/cars","/tech-gadgets","/entertainment","/culture/"]

def blocked(title, summ, link):
    t = title + " " + summ
    l = link.lower()
    if any(p in l for p in BAD_PATH): return True
    return any(k in t for k in SPORT + MAGAZINE + UNVERIFIED)

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
            u = el.get("url")
            t = el.get("type","")
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

items, seen = [], set()
now = datetime.now(timezone.utc)
for name, url in FEEDS:
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        root = ET.fromstring(urllib.request.urlopen(req, timeout=25).read())
    except Exception as e:
        print("FAIL", name, e); continue
    for it in root.iter("item"):
        g = lambda k: (it.findtext(k) or "")
        title, link = clean(g("title")), g("link").strip()
        if not title or not link or link in seen: continue
        try: d = parsedate_to_datetime(g("pubDate"))
        except Exception: d = now
        if d.tzinfo is None: d = d.replace(tzinfo=timezone.utc)
        if now - d > timedelta(hours=48): continue
        summ = clean(g("description"))[:240]
        if blocked(title, summ, link): continue
        seen.add(link)
        items.append({"t":title,"b":summ,"s":link,"src":name,"c":classify(title+" "+summ),
                      "img":img_of(it),"vid":video_of(it),"ts":int(d.timestamp())})
items.sort(key=lambda x:-x["ts"])
json.dump({"updated":int(time.time()),"items":items[:150]}, open("news.json","w",encoding="utf-8"), ensure_ascii=False)
print("items:", len(items))
