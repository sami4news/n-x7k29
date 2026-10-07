import json, re, time, urllib.request, html, os, io, struct, hashlib
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
 # المدينة المنورة
 ("GT","المدينة المنورة"),
 ("GT","أمانة المدينة المنورة"),
 ("GT","إمارة منطقة المدينة المنورة"),
 ("GT","المسجد النبوي"),
 # اليمن
 ("GN","اليمن"),
 ("GN","عدن"),
 ("GN","صنعاء"),
 # دول الخليج
 ("GN","دول الخليج"),
 ("GN","الإمارات"),
 ("GN","قطر"),
 ("GN","الكويت"),
 ("GN","البحرين"),
 ("GN","سلطنة عمان"),
 # العالم
 ("GN","أخبار العالم"),
 ("GN","أمريكا الصين روسيا"),
 ("GN","أوروبا"),
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
# اتفاق الطائف اللبناني وما يتصل به ليس من أخبار مدينة الطائف
NOT_TAIF = re.compile(r"اتفاق الطائف|وثيقة الطائف|مؤتمر الطائف|لبنان|لبناني|اللبناني|اللبنانية|بيروت|نواف سلام|حزب الله|سلام:")
TAIF_RX = re.compile(r"(?<![\u0621-\u064A])(?:و|ب|ل|ف|ك)?(?:ال)?(?:طائف|الهدا|الحوية|ثقيف)(?![\u0621-\u064A])")
ORDER = ["urgent","wx","war","sa","eco","me"]
KW["me"] = POL + ["العالم","أمريكا","الأمريكي","الصين","الصيني","روسيا","الروسي","أوروبا","الأوروبي","الاتحاد الأوروبي","اليابان","الهند","كوريا","بريطانيا","فرنسا","ألمانيا","الناتو","الأمم المتحدة","مجلس الأمن","واشنطن","موسكو","بكين","لندن","باريس","كندا","أستراليا","البرازيل","باكستان","أفغانستان"]
# ---- الأقسام التفصيلية (gr) ----
def _w(words): return re.compile(r"(?<![\u0621-\u064A])(?:و|ب|ل|ف|ك)?(?:ال)?(?:%s)(?![\u0621-\u064A])" % "|".join(words))
MADINA_RX = re.compile(r"المدينة المنورة|المدينه المنوره|مسجد قباء|المسجد النبوي|الحرم النبوي|الروضة الشريفة|مطار الأمير محمد بن عبدالعزيز|أمانة المدينة|إمارة منطقة المدينة|أمير منطقة المدينة|جامعة طيبة|هيئة تطوير المدينة|زوار المدينة|(?<![\u0621-\u064A])(?:و|ب|ل|ف|ك)?(?:ال)?(?:ينبع|العلا|طيبة)(?![\u0621-\u064A])")
YEMEN_RX = _w(["اليمن","يمني","يمنية","اليمني","اليمنية","عدن","صنعاء","مأرب","تعز","الحديدة","حضرموت","المكلا","شبوة","سقطرى","الحوثي","الحوثيين","الحوثيون","المجلس الانتقالي","مجلس القيادة الرئاسي","العليمي","غروندبرغ"])
GULF_RX = _w(["الإمارات","الإماراتي","الإماراتية","أبوظبي","دبي","الشارقة","قطر","القطري","القطرية","الدوحة","الكويت","الكويتي","الكويتية","البحرين","البحريني","المنامة","سلطنة عمان","عُمان","عمان السلطنة","مسقط","العماني","الخليج","الخليجي","الخليجية","دول الخليج","مجلس التعاون","التعاون الخليجي"])
SA_RX = _w(["السعودية","السعودي","السعودية","المملكة","الرياض","جدة","مكة","المدينة المنورة","ولي العهد","خادم الحرمين","الملك سلمان","محمد بن سلمان","نيوم","الدمام","أبها","الطائف","تبوك","القصيم","الأحساء","جازان","نجران","حائل","الجوف","عرعر","سكاكا","الباحة","الخبر","الظهران","واحة","وزارة الداخلية السعودية","ديوان المظالم","المظالم","الشرقية","المنطقة الشرقية","مجلس الوزراء","مجلس الشورى","الديوان الملكي","المسجد الحرام","الحرمين","الحرم المكي","الحج","العمرة","المطوفين","هيئة الأمر بالمعروف","الأمن العام","الدفاع المدني","وزارة الحج","وزارة الصحة","وزارة التعليم","وزارة الإعلام","وزارة العدل","وزارة الشؤون الإسلامية","أمير منطقة","أمير الرياض","سدايا","الهيئة العامة","وكالة الأنباء السعودية","رؤية 2030","صندوق الاستثمارات","الأمير فيصل بن","الأمير سعود بن","الأمير خالد بن","الأمير محمد بن","الأمير عبدالعزيز بن","أمير الشرقية","وزير العدل","وزير الداخلية","وزير الصحة","وزير التعليم","وزير الإعلام","وزير الحج","وزير الرياضة","وزير الاستثمار","وزير الطاقة","وزير المالية","وزير الحرس الوطني","الحرس الوطني","هيئة الرقابة","هيئة الزكاة","الزكاة والضريبة","جامعة الملك","جامعة الأميرة","جامعة الإمام","المؤسسة العامة"])
ME_RX = _w(["غزة","فلسطين","فلسطيني","الفلسطينيين","إسرائيل","إسرائيلي","لبنان","سوريا","سوري","دمشق","العراق","بغداد","إيران","إيراني","طهران","الأردن","عمّان","مصر","القاهرة","ليبيا","السودان","تونس","الجزائر","المغرب","تركيا","أنقرة","الضفة","القدس","رام الله","حماس","حزب الله","هرمز","البحر الأحمر","الجامعة العربية","الشرق الأوسط","العربي","العربية","عربي"])
GR_ORDER = ["urgent","wx","war","sa","eco","me"]
def group_of(text, cat, tf):
    """قسم الخبر (حصري): الطائف > المدينة > عاجل > أرصاد > اليمن > الخليج > حروب > اقتصاد > السعودية > الشرق الأوسط > العالم"""
    if tf: return "taif"
    if MADINA_RX.search(text) and not NOT_TAIF.search(text): return "madina"
    if cat in ("urgent","wx"): return cat
    if YEMEN_RX.search(text): return "yemen"
    if GULF_RX.search(text) and not SA_RX.search(text): return "gulf"
    if cat in ("war","eco","sa"): return cat
    if SA_RX.search(text): return "sa"
    return "me" if ME_RX.search(text) else "world"
GR_RANK = ["taif","madina","urgent","wx","yemen","gulf","war","eco","sa","me","world"]
def gr_rank(g): return GR_RANK.index(g) if g in GR_RANK else 99

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
    t = html.unescape(re.sub(r"<[^>]+>", " ", s or ""))
    t = re.sub(r"<[^>]*>?", " ", t)            # وسوم مُهرّبة أو مقطوعة
    t = re.sub(r"https?://\S+|(?:%[0-9A-Fa-f]{2}){2,}\S*", " ", t)   # روابط وبقايا ترميز
    return re.sub(r"\s+", " ", t).strip()

# ===================== الوسائط: صور وفيديو =====================
import gzip, threading
from urllib.parse import urljoin, urlparse

try:   # اختياري: فكّ روابط أخبار جوجل المشفّرة للوصول إلى صفحة الخبر الأصلية (تُثبَّت في ملف update.yml)
    from googlenewsdecoder import gnewsdecoder
except Exception:
    gnewsdecoder = None

UA = {"User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36",
      "Accept": "text/html,application/xhtml+xml,*/*;q=0.8", "Accept-Language": "ar,en;q=0.7"}
JUNK_IMG = re.compile(r"(logo|icon|favicon|sprite|avatar|placeholder|blank|pixel|spacer|1x1|loader|emoji|watermark|"
                      r"default[-_]?(share|image|og|thumb)|no[-_]?image|\.svg|\.gif|\.ico)(\b|[-_./?]|$)", re.I)
UA_FB = "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)"
UA_TW = "Twitterbot/1.0"
GN_HOSTS = ("news.google.com", "google.com/rss", "lh3.googleusercontent.com")

def http_get(url, limit=600_000, timeout=10, ua=None):
    hd = dict(UA)
    if ua: hd["User-Agent"] = ua
    req = urllib.request.Request(url, headers=hd)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw, ctype, final = r.read(limit), r.headers.get("Content-Type", ""), r.geturl()
    if raw[:2] == b"\x1f\x8b":
        try: raw = gzip.decompress(raw)
        except Exception: pass
    m = re.search(r"charset=([\w-]+)", ctype, re.I)
    enc = m.group(1) if m else None
    if not enc:
        m = re.search(rb'<meta[^>]+charset=["\']?([\w-]+)', raw[:6000], re.I)
        enc = m.group(1).decode("ascii", "ignore") if m else "utf-8"
    try: return raw.decode(enc, "replace"), final
    except LookupError: return raw.decode("utf-8", "replace"), final

def abs_url(u, base):
    u = html.unescape((u or "").strip().replace("\\/", "/").replace("\\u0026", "&"))
    if not u or u.startswith(("data:", "blob:", "javascript:")): return ""
    if u.startswith("//"): u = "https:" + u
    u = urljoin(base, u)
    return u if u.startswith("http") else ""

def good_img(u):
    if not u: return False
    p = urlparse(u)
    if any(h in u for h in GN_HOSTS): return False
    return not JUNK_IMG.search(p.path.lower())

def vkind(u, hint=""):
    l = u.lower()
    if re.search(r"\.mp4(\?|#|$)", l) or "mp4" in hint.lower(): return "mp4"
    if ".m3u8" in l: return "hls"
    if "youtube.com" in l or "youtu.be" in l: return "yt"
    return "embed"

def _json_walk(o, imgs, vids):
    if isinstance(o, list):
        for x in o: _json_walk(x, imgs, vids)
    elif isinstance(o, dict):
        t = o.get("@type"); t = " ".join(t) if isinstance(t, list) else str(t or "")
        if "VideoObject" in t:
            for k in ("contentUrl", "embedUrl", "url"):
                if isinstance(o.get(k), str): vids.append(o[k])
        for k, v in o.items():
            if k in ("image", "thumbnailUrl", "thumbnail", "primaryImageOfPage"):
                for x in (v if isinstance(v, list) else [v]):
                    if isinstance(x, str): imgs.append(x)
                    elif isinstance(x, dict) and isinstance(x.get("url"), str): imgs.append(x["url"])
            else:
                _json_walk(v, imgs, vids)

def media_from_html(h, base):
    """يستخرج (صور، فيديوهات) من صفحة الخبر: og/twitter/JSON-LD/وسوم الفيديو/أول صور المقال"""
    head = h[:250_000]
    metas = []
    for tag in re.findall(r"<meta\b[^>]*>", head, re.I):
        k = re.search(r'(?:property|name|itemprop)\s*=\s*["\']([^"\']+)["\']', tag, re.I)
        c = re.search(r'content\s*=\s*["\']([^"\']*)["\']', tag, re.I)
        if k and c: metas.append((k.group(1).lower(), html.unescape(c.group(1))))
    mv = lambda *keys: [c for k, c in metas if k in keys and c]
    imgs, vids = [], []
    ld_img, ld_vid = [], []
    for blk in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', head, re.I | re.S):
        try: _json_walk(json.loads(blk.strip()), ld_img, ld_vid)
        except Exception: pass
    cand_imgs = ld_img[:1] + mv("og:image", "og:image:url", "og:image:secure_url") + mv("twitter:image", "twitter:image:src") + ld_img[1:3]
    m = re.search(r'<link[^>]+rel=["\']image_src["\'][^>]*href=["\']([^"\']+)', head, re.I)
    if m: cand_imgs.append(m.group(1))
    # أول صور داخل المقال (بعد العنوان الرئيسي)
    body = h[h.lower().find("<h1"):][:120_000] if "<h1" in h.lower() else h[:120_000]
    for tag in re.findall(r"<img\b[^>]*>", body, re.I)[:25]:
        w = re.search(r'\bwidth=["\']?(\d+)', tag, re.I)
        if w and int(w.group(1)) < 200: continue
        src = (re.search(r'data-(?:src|original|lazy-src)=["\']([^"\']+)', tag, re.I) or re.search(r'\bsrc=["\']([^"\']+)', tag, re.I))
        ss = re.search(r'srcset=["\']([^"\']+)', tag, re.I)
        u = src.group(1) if src else ""
        if ss:   # أكبر نسخة في srcset
            best = max(((float(re.sub(r"[^\d.]", "", p.split()[-1]) or 0) if len(p.split()) > 1 else 0, p.split()[0]) for p in ss.group(1).split(",") if p.strip()), default=(0, ""))
            u = best[1] or u
        if u: cand_imgs.append(u)
        if len(cand_imgs) > 14: break
    if len([c for c in cand_imgs if c]) < 2:   # مواقع تعتمد على JavaScript: الصور داخل بيانات JSON في الصفحة
        flat0 = h[:600_000].replace("\\/", "/").replace("\\u0026", "&")
        cand_imgs += re.findall(r'https?://[^"\'\s<>\\]+?\.(?:jpe?g|png|webp)(?:\?[^"\'\s<>\\]*)?', flat0)[:12]
    seen = set()
    for u in cand_imgs:
        u = abs_url(u, base)
        k = u.split("?")[0]
        if good_img(u) and k not in seen:
            seen.add(k); imgs.append(u)
        if len(imgs) >= 4: break
    # فيديو
    vt = " ".join(mv("og:video:type")) + " " + " ".join(mv("twitter:player:stream:content_type"))
    cv = mv("og:video:secure_url", "og:video:url", "og:video", "twitter:player:stream", "twitter:player") + ld_vid
    for tag in re.findall(r"<(?:video|source)\b[^>]*>", head + h[len(head):][:350_000], re.I):
        for a in re.findall(r'(?:src|data-src|data-video|data-mp4)=["\']([^"\']+)', tag, re.I): cv.append(a)
    flat = h.replace("\\/", "/")
    cv += re.findall(r'https?://[^"\'\s<>\\]+?\.(?:mp4|m3u8)(?:\?[^"\'\s<>\\]*)?', flat)[:8]
    for yt in re.findall(r'(?:youtube(?:-nocookie)?\.com/embed/|youtu\.be/|youtube\.com/watch\?v=)([\w-]{11})', flat)[:2]:
        cv.append("https://www.youtube.com/watch?v=" + yt)
    og_urls = {abs_url(c, base) for c in mv("og:video:secure_url", "og:video:url", "og:video")}
    og_mp4 = "mp4" in vt.lower()
    out, seenv = [], set()
    for u in cv:
        u = abs_url(u, base)
        if not u or u in seenv or re.search(r"\.(jpg|jpeg|png|webp)(\?|$)", u, re.I): continue
        seenv.add(u); out.append({"u": u, "k": vkind(u, "mp4" if (og_mp4 and u in og_urls) else "")})
    rank = {"mp4": 0, "hls": 1, "yt": 2, "embed": 3}
    out.sort(key=lambda v: rank[v["k"]])
    return imgs, out[:4]

# --- من عناصر RSS نفسها ---
def img_of(it):
    for el in it.iter():
        tag = el.tag.split("}")[-1]
        if tag in ("content", "thumbnail", "enclosure"):
            u, t, md = el.get("url"), el.get("type", ""), el.get("medium", "")
            if u and not t.startswith("video") and md != "video" and not re.search(r"\.(mp4|m3u8)(\?|$)", u, re.I):
                if tag != "enclosure" or t.startswith("image") or re.search(r"\.(jpe?g|png|webp)(\?|$)", u, re.I):
                    return u
    raw = html.unescape(ET.tostring(it, encoding="unicode"))
    for m in re.finditer(r'<img[^>]+src=["\']([^"\']+)', raw):
        if good_img(m.group(1)): return html.unescape(m.group(1))
    return ""

def video_of(it):
    for el in it.iter():
        u = el.get("url") or ""
        if u and (el.get("type", "").startswith("video") or el.get("medium") == "video" or re.search(r"\.mp4(\?|$)", u, re.I)):
            return u
    return ""

# --- فكّ رابط أخبار جوجل ---
_DEC = threading.Semaphore(3)
def resolve_gn_http(link):
    """احتياط: بعض روابط جوجل القديمة تحوّل مباشرة إلى الناشر"""
    try:
        req = urllib.request.Request(link + ("&" if "?" in link else "?") + "oc=5", headers=UA)
        with urllib.request.urlopen(req, timeout=10) as r:
            fin = r.geturl(); body = r.read(300_000).decode("utf-8", "replace")
        if "google." not in urlparse(fin).netloc: return fin
        m = re.search(r'data-n-au=["\']([^"\']+)', body)
        if m: return html.unescape(m.group(1))
    except Exception:
        pass
    return ""

def resolve_gn(link):
    if "news.google.com" not in link: return ""
    if gnewsdecoder is None: return resolve_gn_http(link)
    with _DEC:
        for kw in ({"interval": None, "timeout": 10}, {"interval": None}):
            try:
                r = gnewsdecoder(link, **kw)
                if isinstance(r, dict) and r.get("success"): return r["decoded_url"]
                break
            except TypeError: continue
            except Exception: break
    return resolve_gn_http(link)

def enrich(it, deadline):
    """يكمّل الخبر: رابط المصدر الحقيقي + الصور + الفيديو. نتائجه تُحفظ فلا تُعاد في كل تشغيل"""
    if time.time() > deadline: return
    link = it.get("g") or it["s"]
    it["a"] = it.get("a", 0) + 1
    real = it.get("u") or ""
    if "news.google.com" in link and not real:
        real = resolve_gn(link)
        if real: it["u"] = real
    page = real or ("" if "news.google.com" in link else link)
    rss_img = it.get("img") or ""
    imgs, vids = [], []
    if page:
        for ua in (None, UA_FB, UA_TW):   # بعض المواقع تحجب المتصفح من الخوادم لكن تسمح لزاحفات المعاينة (فيسبوك/تويتر)
            try:
                h, final = http_get(page, ua=ua)
                imgs, vids = media_from_html(h, final or page)
                it.pop("err", None)
                if imgs: break
            except Exception as e:
                it["err"] = str(e)[:60]
    if rss_img and rss_img.split("?")[0] not in [x.split("?")[0] for x in imgs]: imgs.append(rss_img)
    if it.get("vid") and it["vid"] not in [v["u"] for v in vids]: vids.insert(0, {"u": it["vid"], "k": vkind(it["vid"])})
    it["imgs"], it["vids"] = imgs[:4], vids[:4]
    it["img"] = imgs[0] if imgs else ""
    mp4 = [v["u"] for v in vids if v["k"] == "mp4"]
    it["vid"] = mp4[0] if mp4 else ""
    if real:
        it["g"], it["s"] = link, real
        it["tr"] = max(it.get("tr", 0), trust_dom(urlparse(real).netloc))


# ===================== تنزيل الوسائط وحفظها (تُنشر على فرع media في GitHub) =====================
try:
    from PIL import Image
except Exception:
    Image = None

MEDIA_DIR = os.environ.get("MEDIA_DIR", "media_wt")
MIN_SIDE = 160              # أصغر ضلع مقبول للصورة (كان 250): نتساهل قليلًا لنزيد الأخبار المصوّرة
MAX_RATIO = 3.8             # أوسع نسبة مقبولة (نستبعد الشرائط الإعلانية)
MAX_IMG_BYTES = 8_000_000
MAX_VID_BYTES = 18_000_000  # jsDelivr لا يخدم ملفًا أكبر من 20MB
MAX_STORED_VIDEOS = 10
MEDIA_BUDGET = 160_000_000  # الحد الأعلى لمجموع المحفوظ

def fid(prefix, url, ext):
    return "%s_%s.%s" % (prefix, hashlib.md5(url.encode("utf-8")).hexdigest()[:14], ext)

def fetch_bytes(url, limit, timeout=12, referer=""):
    h = dict(UA)
    h["Accept"] = "*/*"
    if referer: h["Referer"] = referer
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout) as r:
        cl = r.headers.get("Content-Length")
        if cl and cl.isdigit() and int(cl) > limit: raise ValueError("too big")
        data = r.read(limit + 1)
    if len(data) > limit: raise ValueError("too big")
    return data

def mp4_dims(data):
    """أبعاد الفيديو من صندوق tkhd في ملف mp4 (بلا حاجة إلى ffprobe)"""
    def boxes(buf, a, b):
        i = a
        while i + 8 <= b:
            size, typ = struct.unpack(">I4s", buf[i:i + 8]); hdr = 8
            if size == 1: size = struct.unpack(">Q", buf[i + 8:i + 16])[0]; hdr = 16
            elif size == 0: size = b - i
            if size < hdr: return
            yield typ, i + hdr, min(i + size, b)
            i += size
    try:
        for t1, a1, b1 in boxes(data, 0, len(data)):
            if t1 != b"moov": continue
            for t2, a2, b2 in boxes(data, a1, b1):
                if t2 != b"trak": continue
                for t3, a3, b3 in boxes(data, a2, b2):
                    if t3 != b"tkhd": continue
                    off = a3 + (76 if data[a3] == 0 else 88)
                    w, h = struct.unpack(">II", data[off:off + 8])
                    w, h = w >> 16, h >> 16
                    if w and h: return w, h
    except Exception:
        pass
    return 0, 0

def img_dims(d):
    """(الامتداد، (العرض، الارتفاع)) من ترويسة الصورة مباشرة — احتياط إن لم تتوفر مكتبة Pillow"""
    try:
        if d[:8] == b"\x89PNG\r\n\x1a\n": return "png", struct.unpack(">II", d[16:24])
        if d[:3] == b"\xff\xd8\xff":
            i = 2
            while i + 9 < len(d):
                if d[i] != 0xFF: i += 1; continue
                m = d[i + 1]
                if m in (0xD8, 0x01) or 0xD0 <= m <= 0xD7: i += 2; continue
                ln = struct.unpack(">H", d[i + 2:i + 4])[0]
                if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):
                    h, w = struct.unpack(">HH", d[i + 5:i + 9]); return "jpg", (w, h)
                i += 2 + ln
        if d[:4] == b"RIFF" and d[8:12] == b"WEBP":
            t = d[12:16]
            if t == b"VP8X": return "webp", (int.from_bytes(d[24:27], "little") + 1, int.from_bytes(d[27:30], "little") + 1)
            if t == b"VP8 ": w, h = struct.unpack("<HH", d[26:30]); return "webp", (w & 0x3fff, h & 0x3fff)
            if t == b"VP8L":
                b = struct.unpack("<I", d[21:25])[0]; return "webp", ((b & 0x3fff) + 1, ((b >> 14) & 0x3fff) + 1)
    except Exception:
        pass
    return None, (0, 0)

def save_image_raw(url, referer=""):
    try: data = fetch_bytes(url, MAX_IMG_BYTES, referer=referer)
    except Exception: return None, "fail"
    ext, (w, h) = img_dims(data)
    if not ext or not w or not h: return None, "fail"
    if min(w, h) < MIN_SIDE or max(w, h) / max(1, min(w, h)) > MAX_RATIO: return None, "small"
    fname = fid("i", url, ext); path = os.path.join(MEDIA_DIR, fname)
    if not os.path.exists(path):
        tmp = "%s.%d.part" % (path, threading.get_ident())
        try:
            with open(tmp, "wb") as f: f.write(data)
            os.replace(tmp, path)
        except Exception:
            return None, "fail"
    return {"t": "i", "f": fname, "o": url, "w": w, "h": h, "b": len(data)}, "ok"

def save_image(url, referer=""):
    """يعيد (مدخل الوسائط أو None، الحالة: ok/small/fail). يصغّر العريض جدًا ويحوّله JPEG"""
    if Image is None: return save_image_raw(url, referer)
    try:
        data = fetch_bytes(url, MAX_IMG_BYTES, referer=referer)
        im = Image.open(io.BytesIO(data)); im.load()
    except Exception:
        return None, "fail"
    w, h = im.size
    if min(w, h) < MIN_SIDE or max(w, h) / max(1, min(w, h)) > MAX_RATIO: return None, "small"
    fname = fid("i", url, "jpg"); path = os.path.join(MEDIA_DIR, fname)
    if not os.path.exists(path):
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA"); bg = Image.new("RGB", im.size, (255, 255, 255)); bg.paste(im, mask=im.split()[-1]); im = bg
        else:
            im = im.convert("RGB")
        if w > 1280: im = im.resize((1280, max(1, round(h * 1280 / w))), Image.LANCZOS)
        tmp = "%s.%d.part" % (path, threading.get_ident())
        try:
            im.save(tmp, "JPEG", quality=84, optimize=True, progressive=True); os.replace(tmp, path)
        except Exception:
            try: os.remove(tmp)
            except OSError: pass
            return None, "fail"
    with Image.open(path) as sv: w2, h2 = sv.size
    return {"t": "i", "f": fname, "o": url, "w": w2, "h": h2, "b": os.path.getsize(path)}, "ok"

def save_video(url, referer=""):
    try: data = fetch_bytes(url, MAX_VID_BYTES, timeout=30, referer=referer)
    except Exception: return None, "fail"
    if len(data) < 4_000: return None, "small"
    if data[4:8] == b"ftyp": ext, (w, h) = "mp4", mp4_dims(data)
    elif data[:4] == b"\x1a\x45\xdf\xa3": ext, (w, h) = "webm", (0, 0)
    else: return None, "fail"
    fname = fid("v", url, ext); path = os.path.join(MEDIA_DIR, fname)
    if not os.path.exists(path):
        tmp = "%s.%d.part" % (path, threading.get_ident())
        with open(tmp, "wb") as f: f.write(data)
        os.replace(tmp, path)
    return {"t": "v", "f": fname, "o": url, "w": w, "h": h, "b": len(data)}, "ok"

def build_media_for(it, bad, max_imgs, st):
    """يحوّل مرشّحات الصور/الفيديو لخبر واحد إلى مرفقات حقيقية محفوظة"""
    page = it.get("u") or it.get("s") or ""
    media, seen_hash, unverified = [], set(), None
    for u in it.get("imgs", [])[:5]:
        if len([m for m in media if m["t"] == "i"]) >= max_imgs: break
        if u.split("?")[0] in bad: st["placeholder"] += 1; continue
        m, status = save_image(u, page)
        if m:
            hh = hashlib.md5(open(os.path.join(MEDIA_DIR, m["f"]), "rb").read()).hexdigest()
            if hh in seen_hash: continue
            seen_hash.add(hh); media.append(m)
        elif status == "fail" and unverified is None:
            unverified = {"t": "i", "o": u}
    if unverified and not any(m["t"] == "i" for m in media):
        media.append(unverified); st["img_unverified"] += 1
    got_vid = False
    for v in it.get("vids", []):
        if v["k"] == "mp4" and not got_vid:
            m, status = save_video(v["u"], page)
            if m: media.append(m); got_vid = True; st["vid_saved"] += 1
            elif status == "fail": media.append({"t": "v", "o": v["u"]}); got_vid = True; st["vid_unverified"] += 1
        elif v["k"] == "yt" and not any(m["t"] == "y" for m in media):
            media.append({"t": "y", "o": v["u"]}); st["yt"] += 1
    it["media"] = media
    it["mt"] = it.get("mt", 0) + 1
    if media:
        first = next((m for m in media if m["t"] == "i"), None)
        if first: it["img"] = first["o"]

def build_media(items, budget=150):
    st = {"placeholder": 0, "img_unverified": 0, "vid_saved": 0, "vid_unverified": 0, "yt": 0}
    os.makedirs(MEDIA_DIR, exist_ok=True)
    cnt = {}
    for it in items:   # صورة تتكرر في 3 أخبار مختلفة غالبًا شعار الموقع لا صورة الخبر
        for u in {x.split("?")[0] for x in it.get("imgs", [])}: cnt[u] = cnt.get(u, 0) + 1
    bad = {u for u, c in cnt.items() if c >= 3}
    def needs(it):
        if "media" not in it: return bool(it.get("imgs") or it.get("vids"))
        return (not it["media"] and it.get("mt", 0) < 3 and (it.get("imgs") or it.get("vids")) and time.time() - it["ts"] < 86400)
    todo = [(i, it) for i, it in enumerate(items) if needs(it)]
    deadline = time.time() + budget
    if todo:
        from concurrent.futures import ThreadPoolExecutor
        def job(x):
            i, it = x
            if time.time() > deadline: return
            try: build_media_for(it, bad, 3 if i < 60 else 1, st)
            except Exception as e: it["err"] = ("media: " + str(e))[:60]
        with ThreadPoolExecutor(8) as ex: list(ex.map(job, todo))
    return st

def prune_media(items):
    """يبقي فقط ما تشير إليه الأخبار الحالية، ويضبط الحد الأعلى للحجم وعدد الفيديوهات"""
    if not os.path.isdir(MEDIA_DIR): return {"files": 0, "bytes": 0}
    def drop(m): m.pop("f", None); m["x"] = 1   # لم يعد مستضافًا (يبقى رابطه الأصلي)
    vids = sorted([(it["ts"], m) for it in items for m in it.get("media", []) if m["t"] == "v" and m.get("f")], key=lambda x: -x[0])
    for _, m in vids[MAX_STORED_VIDEOS:]: drop(m)
    def total():
        return sum(os.path.getsize(os.path.join(MEDIA_DIR, m["f"])) for it in items for m in it.get("media", []) if m.get("f") and os.path.exists(os.path.join(MEDIA_DIR, m["f"])))
    if total() > MEDIA_BUDGET:   # أولًا الفيديوهات الأقدم ثم الصور الثانوية الأقدم
        for _, m in sorted([(it["ts"], m) for it in items for m in it.get("media", []) if m["t"] == "v" and m.get("f")], key=lambda x: x[0]):
            if total() <= MEDIA_BUDGET: break
            drop(m)
        for it in sorted(items, key=lambda x: x["ts"]):
            for m in [m for m in it.get("media", []) if m["t"] == "i" and m.get("f")][1:]:
                if total() <= MEDIA_BUDGET: break
                drop(m)
    keep = {m["f"] for it in items for m in it.get("media", []) if m.get("f")}
    nfiles = nbytes = 0
    for fn in os.listdir(MEDIA_DIR):
        fp = os.path.join(MEDIA_DIR, fn)
        if not os.path.isfile(fp): continue
        if fn in keep: nfiles += 1; nbytes += os.path.getsize(fp)
        else: os.remove(fp)
    return {"files": nfiles, "bytes": nbytes}


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

TRUSTED_DOM = ("aljazeera.net", "aljazeera.com", "alarabiya.net", "alhadath.net", "skynewsarabia.com", "bbc.com", "bbc.co.uk",
               "aawsat.com", "france24.com", "okaz.com.sa", "sabq.org", "alriyadh.com", "alwatan.com.sa", "aleqt.com", "argaam.com",
               "reuters.com", "independentarabia.com", "asharq.com", "aa.com.tr", "alekhbariya.net", "arabnews.com", "saudigazette.com.sa",
               "almadina.com", "alyaum.com", "alqabas.com", "albayan.ae", "alkhaleej.ae", "dw.com", "cnn.com")

def trust_dom(dom):
    d = (dom or "").lower().split(":")[0]
    if d.startswith("www."): d = d[4:]
    if d == "gov.sa" or d.endswith(".gov.sa") or d.endswith(".edu.sa"): return 2
    if any(d == t or d.endswith("." + t) for t in TRUSTED_DOM): return 1
    return 0

def trust(name, dom=""):
    """2 = رسمي، 1 = موثوق، 0 = غير معروف (بالاسم، أو بنطاق الموقع إن عُرف)"""
    n = canon(name)
    if any(_m(n, k) for k in OFF_N): return 2
    r = 1 if any(_m(n, k) for k in TRU_N) else 0
    return max(r, trust_dom(dom))

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
        rep = max(g, key=lambda x: (x["tr"] * 3 + (0 if "news.google.com" in x["s"] else 2) + (2 if x["img"] else 0) + (1 if x["b"] else 0) + (1 if x["vid"] else 0), x["ts"]))
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
        it["gr"] = min((m["gr"] for m in g), key=gr_rank)
        it["tr"] = max(m["tr"] for m in g)
        it["n"] = len(seen_src)
        it["srcs"] = srcs[:8]
        it["alts"] = alts
        out.append(it)
    return out

RIY = timezone(timedelta(hours=3))
ATOM = "{http://www.w3.org/2005/Atom}"

def atom_get(it, k):
    if k == "link":
        ls = it.findall(ATOM + "link")
        for l in ls:
            if l.get("rel", "alternate") == "alternate" and l.get("href"): return l.get("href")
        return ls[0].get("href", "") if ls else ""
    if k == "pubDate": return it.findtext(ATOM + "published") or it.findtext(ATOM + "updated") or ""
    if k == "description": return it.findtext(ATOM + "summary") or it.findtext(ATOM + "content") or ""
    return it.findtext(ATOM + k) or ""

def parse_dt(s, now):
    try: d = parsedate_to_datetime(s)
    except Exception:
        try: d = datetime.fromisoformat(s.strip().replace("Z", "+00:00"))
        except Exception: d = now
    if d.tzinfo is None: d = d.replace(tzinfo=timezone.utc)
    return d

# مصادر مباشرة (RSS/Atom): تحمل الصور غالبًا في الخلاصة نفسها، فلا نعتمد على روابط جوجل المشفّرة.
# يكتشف الروبوت رابط الخلاصة تلقائيًا من الصفحة الرئيسية ويحفظه في news.json (feeds) ويعيد المحاولة دوريًا
DIRECT = [("رؤيا الإخباري", "royanews.tv"), ("صحيفة سبق الإلكترونية", "sabq.org"), ("واس", "spa.gov.sa"), ("عكاظ", "okaz.com.sa"),
          ("الرياض", "alriyadh.com"), ("جريدة المدينة", "al-madina.com"), ("اليوم", "alyaum.com"), ("الوطن", "alwatan.com.sa"),
          ("الاقتصادية", "aleqt.com"), ("أرقام", "argaam.com")]
KNOWN_FEED = {"royanews.tv": "https://royanews.tv/rss"}

def feed_ok(url):
    try:
        raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=15).read(2_500_000)
        root = ET.fromstring(raw)
        return bool(list(root.iter("item")) or list(root.iter(ATOM + "entry")))
    except Exception:
        return False

def discover(dom, cache):
    c = cache.get(dom) or {}
    if c and time.time() - c.get("t", 0) < (86400 if c.get("u") else 6 * 3600):
        return c.get("u", "")
    cands = [KNOWN_FEED[dom]] if dom in KNOWN_FEED else []
    for page in ("https://%s/" % dom, "https://www.%s/" % dom, "https://%s/rss" % dom):
        try:
            h, final = http_get(page, limit=400_000)
        except Exception:
            continue
        for t in re.findall(r"<link\b[^>]*>", h, re.I):
            if re.search(r'type=["\']application/(rss|atom)\+xml', t, re.I):
                hr = re.search(r'href=["\']([^"\']+)', t, re.I)
                if hr: cands.append(urljoin(final, html.unescape(hr.group(1))))
        for hr in re.findall(r'href=["\']([^"\'#]*(?:rss|feed|\.xml)[^"\'#]*)', h, re.I)[:8]:
            if not re.search(r"\.(jpe?g|png|webp|gif|css|js)(\?|$)", hr, re.I): cands.append(urljoin(final, html.unescape(hr)))
    base = "https://%s" % dom
    cands += [base + x for x in ("/rss", "/feed", "/rss.xml", "/feed/", "/rss/latest", "/rss/news", "/ar/rss")]
    seen, url = set(), ""
    for u in cands:
        if u in seen or "comment" in u.lower(): continue
        seen.add(u)
        if feed_ok(u): url = u; break
    cache[dom] = {"u": url, "t": int(time.time())}
    return url

def link_keys(it):
    ks = [it.get("g"), it.get("s"), it.get("u")] + [a.get("s") for a in it.get("alts", [])]
    return [k for k in ks if k]

def run(feeds=None, out="news.json", max_enrich=70, budget=150):
    use_direct = feeds is None
    feeds = list(feeds or FEEDS)
    cands, links = [], set()
    now = datetime.now(timezone.utc)
    try: old0 = json.load(open(out, encoding="utf-8"))
    except Exception: old0 = {}
    fcache = dict(old0.get("feeds") or {})
    if use_direct:
        from concurrent.futures import ThreadPoolExecutor
        def _safe(nd):
            try: return discover(nd[1], fcache)
            except Exception: return ""
        with ThreadPoolExecutor(5) as ex:
            urls = list(ex.map(_safe, DIRECT))
        for (nm, dom), u in zip(DIRECT, urls):
            if u: feeds.append((nm, u))
        print("direct feeds:", {dom: bool(u) for (nm, dom), u in zip(DIRECT, urls)})
    for name, q in feeds:
        gn = name in ("GN", "GT")
        url = (GN(q, 3) if name == "GT" else GN(q)) if gn else q
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            root = ET.fromstring(urllib.request.urlopen(req, timeout=25).read())
        except Exception as e:
            print("FAIL", name, q[:40], e); continue
        for it in list(root.iter("item")) + list(root.iter(ATOM + "entry")):
            atom = it.tag == ATOM + "entry"
            g = (lambda k, it=it: atom_get(it, k)) if atom else (lambda k, it=it: (it.findtext(k) or ""))
            title, link = clean(g("title")), g("link").strip()
            if not title or not link or link in links: continue
            src, summ = name, clean(g("description"))[:240]
            if gn:
                summ = ""
                if " - " in title: title, src = title.rsplit(" - ", 1)
            src = src.strip()
            if len(title) < 28 or "؟" in title or re.match(r"^\d+\s", title): continue
            d = parse_dt(g("pubDate"), now)
            tf = bool(TAIF_RX.search(title + " " + summ)) and not NOT_TAIF.search(title + " " + summ)
            txt = title + " " + summ
            g0 = None
            _m = bool(MADINA_RX.search(txt)) and not tf
            if now - d > timedelta(hours=72 if (tf or _m) else 48): continue
            if blocked(title, summ, link): continue
            cat = classify(txt)
            g0 = group_of(txt, cat, tf)
            if not cat and g0 in ("madina","gulf","yemen","me"): cat = "me"
            if not cat: continue
            if g0 == "world" and not cat: continue
            links.add(link)
            se = it.find("source")
            dom = urlparse(se.get("url", "")).netloc if (gn and se is not None) else ("" if gn else urlparse(link).netloc)
            cands.append({"t": title, "b": summ, "s": link, "src": src, "c": cat, "tf": tf, "gr": g0,
                          "img": img_of(it), "vid": video_of(it), "ts": int(d.timestamp()),
                          "tr": trust(src, dom), "sig": sig(title)})
    items = cluster(cands)
    items.sort(key=lambda x: -x["ts"])
    items = items[:300]

    # --- ما أُنجز في التشغيلات السابقة (الترقيم، الرابط الحقيقي، الوسائط) ---
    try: old = json.load(open(out, encoding="utf-8"))
    except Exception: old = {}
    old["items"] = (old.get("items") or []) + (old.get("held") or [])   # المحجوزة تنتظر صورتها
    idx = {}
    for o in old.get("items", []):
        for k in link_keys(o): idx.setdefault(k, o)
    for it in items:
        o = next((idx[k] for k in link_keys(it) if k in idx), None)
        if not o: continue
        for f in ("a", "u", "g", "imgs", "vids", "err", "media", "mt", "fs"):
            if f in o: it[f] = o[f]
        if o.get("g"):   # الخبر سبق فكّ رابطه: نحتفظ بالرابط الحقيقي
            it["s"], it["g"] = o["s"], o["g"]
        if "imgs" in o: it["img"], it["vid"] = o.get("img", ""), o.get("vid", "")

    # --- الاحتفاظ بالأخبار السابقة التي غابت عن المصادر (حتى لا تختفي من الأقسام) ---
    have = set()
    for it in items: have.update(link_keys(it))
    nowts = time.time(); kept = 0
    pool = [{"sig": sig(x["t"]), "ts": x["ts"], "k": norm(x["t"])} for x in items]   # لمنع تكرار الخبر نفسه برابط مختلف
    def dup(o):
        a = {"sig": sig(o["t"]), "ts": o["ts"], "k": norm(o["t"])}
        if any(a["k"] == q["k"] for q in pool): return a, True
        return a, any(same_story(a, q) for q in pool)
    for o in sorted(old.get("items", []), key=lambda x: -x.get("ts", 0)):
        if any(k in have for k in link_keys(o)): continue
        da, isdup = dup(o)
        if isdup: continue
        o["b"] = clean(o.get("b", ""))
        txt = (o.get("t", "") + " " + o.get("b", ""))
        tf0 = bool(TAIF_RX.search(txt)) and not NOT_TAIF.search(txt)
        g1 = group_of(txt, o.get("c"), tf0)
        if blocked(o.get("t", ""), o.get("b", ""), o.get("s", "")): continue
        keep_h = 168 if g1 in ("taif", "madina") else 96
        if nowts - o.get("ts", 0) > keep_h * 3600: continue
        o["tf"], o["gr"] = tf0, g1
        items.append(o); have.update(link_keys(o)); kept += 1; pool.append(da)
    items.sort(key=lambda x: -x["ts"])
    cnt = {}; trimmed = []
    for it in items:    # سقف لكل قسم حتى لا يكبر الملف
        g2 = it.get("gr") or it.get("c")
        cnt[g2] = cnt.get(g2, 0) + 1
        if cnt[g2] <= 70: trimmed.append(it)
    items = trimmed[:450]
    print("أخبار محتفظ بها من السابق:", kept)

    def needs(it):
        if it.get("a", 0) >= 3: return False
        if "imgs" not in it: return True
        gnl = "news.google.com" in (it.get("g") or it["s"])
        return (gnl and not it.get("u")) or (not it["imgs"] and time.time() - it["ts"] < 86400)
    todo = [i for i in items if needs(i)][:max_enrich]
    deadline = time.time() + budget
    if todo:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(10) as ex:
            list(ex.map(lambda i: enrich(i, deadline), todo))
    for it in items:   # ضمان وجود الحقول
        it.setdefault("imgs", [it["img"]] if it.get("img") else [])
        it.setdefault("vids", [{"u": it["vid"], "k": "mp4"}] if it.get("vid") else [])

    mst = build_media(items)
    pst = prune_media(items)
    if not items:
        if old.get("items"):   # حماية: إذا تعطلت المصادر كلها لا نفرّغ الموقع
            print("لا أخبار جديدة (تعطل المصادر؟) — أُبقي على الملف السابق"); return
    # --- الترقيم: يبدأ من 1 كل يوم (بتوقيت الرياض) ---
    today = datetime.now(RIY).strftime("%Y-%m-%d")
    # القسم الذي ينتمي إليه الخبر (الطائف قسم مستقل). الترقيم يحسبه الموقع نفسه بحسب ما يعرضه فعلًا
    seq = old.get("seq") or {}
    for it in items: it["gr"] = it.get("gr") or ("taif" if it.get("tf") else it["c"])
    # --- إحصاءات تشخيصية تظهر في الموقع ---
    stats = {}
    for it in items:
        st = stats.setdefault(it["src"], [0, 0, 0]); st[0] += 1; st[1] += 1 if it.get("imgs") else 0; st[2] += 1 if it.get("vids") else 0
    gn_items = [i for i in items if i.get("g") or "news.google.com" in i["s"]]
    info = {"decoder": gnewsdecoder is not None, "gn": len(gn_items), "gn_ok": sum(1 for i in gn_items if i.get("u")),
            "img": sum(1 for i in items if i.get("imgs")), "vid": sum(1 for i in items if i.get("vids")),
            "mp4": sum(1 for i in items if any(v["k"] == "mp4" for v in i.get("vids", []))), "total": len(items),
            "hosted_img": sum(1 for i in items for m in i.get("media", []) if m["t"] == "i" and m.get("f")),
            "hosted_vid": sum(1 for i in items for m in i.get("media", []) if m["t"] == "v" and m.get("f")),
            "yt": sum(1 for i in items for m in i.get("media", []) if m["t"] == "y"),
            "media_mb": round(pst["bytes"] / 1e6, 1), "mst": mst}
    top = dict(sorted(stats.items(), key=lambda kv: -kv[1][0])[:30])
    info["feeds"] = {k: bool(v.get("u")) for k, v in fcache.items()}
    # --- لا ننشر الخبر قبل أن تُجرَّب صورته: نحجزه بضع دقائق، فإن لم توجد له صورة نُشر بدونها ---
    nowts = int(time.time())
    held, shown = [], []
    for it in items:
        it.setdefault("fs", nowts)
        lim = 480 if (it.get("gr") == "urgent" or it.get("c") == "urgent") else 1080
        if (not it.get("imgs")) and nowts - it["fs"] < lim and nowts - it["ts"] < 86400: held.append(it)
        else: shown.append(it)
    print("محجوز بانتظار صورته:", len(held), "| منشور:", len(shown))
    info["held"] = len(held)
    items_all = items; items = shown
    json.dump({"updated": int(time.time()), "seq": seq, "feeds": fcache, "info": info, "stats": top, "items": items, "held": held},
              open(out, "w", encoding="utf-8"), ensure_ascii=False)
    print("candidates:", len(cands), "-> cards:", len(items), "| multi-source:", sum(1 for i in items if i["n"] > 1))
    print("hosted: images %(hosted_img)d | videos %(hosted_vid)d | youtube %(yt)d | %(media_mb)s MB | " % info, info["mst"])
    print("media: images %(img)d/%(total)d | videos %(vid)d (mp4 %(mp4)d) | google-news links resolved %(gn_ok)d/%(gn)d | decoder installed: %(decoder)s" % info)
    for src, (n, ni, nv) in list(top.items())[:12]:
        if ni < n: print("  بلا صورة:", src, "%d/%d" % (n - ni, n))

if __name__ == "__main__":
    run()
