# تحديث المجلات المستقل: يجلب أخبار أقسام المجلات وحدها (علوم، ثقافة، طبيعة، صحة، كتب، إسلام) ويكتب mag.json
# أخف وأسرع من التحديث العام: بلا صور ولا ترجمة ولا استضافة وسائط (تُضاف صورها في التحديث العام التالي)
import json, re, time, html, urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import fetch_news as F

def one(f):
    nm, qq = f[0], f[1]
    scc = F.MAGF.get(nm) or ("cul" if nm in F.CUL_SRC else ("sci" if nm in F.SCI_SRC else ""))
    if not scc: return []
    u = F.GN(qq, 3) if nm in F.MAGF else qq
    try: root = ET.fromstring(urllib.request.urlopen(urllib.request.Request(u, headers=F.UA), timeout=12).read())
    except Exception as e:
        print("FAIL", nm, str(qq)[:50], str(e)[:50]); return []
    out, now = [], datetime.now(timezone.utc)
    for el in list(root.iter("item")) + list(root.iter(F.ATOM + "entry")):
        isatom = el.tag.endswith("entry")
        g = (lambda k: F.atom_get(el, k)) if isatom else (lambda k: el.findtext(k) or "")
        title = html.unescape(g("title")).strip(); src = ""
        if nm in F.MAGF and " - " in title: title, src = title.rsplit(" - ", 1)
        if not src: src = nm if nm not in F.MAGF else ""
        title, src, link = title.strip(), src.strip(), (g("link") or "").strip()
        if len(title) < 20 or not link: continue
        d = F.parse_dt(g("pubDate"), now)
        if now - d > F.timedelta(hours=F.SC_HOURS) or d > now + F.timedelta(minutes=10): continue
        txt = title + " " + re.sub(r"<[^>]+>", " ", html.unescape(g("description")))[:300]
        if nm in F.SCI_MIX and (F.TECH_RX.search(txt) or F.TECH_NO.search(txt)): continue
        if F.SC_BAD.search(txt) or F.HARDBAN.search(txt) or F.UNVERIFIED_RX.search(txt) or (scc in F.MAG_BAD and F.MAG_BAD[scc].search(txt)): continue
        out.append({"t": title, "b": "", "s": link, "src": src, "c": scc, "tf": False, "gr": scc, "ts": int(d.timestamp()), "n": 1,
                    "srcs": [src], "imgs": [], "vids": [], "tr": F.trust(src, ""), "xl": 1 if nm in F.SCI_EN else 0, "mq": 1})
    return out

def main():
    feeds = [f for f in F.FEEDS if f[0] in F.MAGF or f[0] in F.CUL_SRC or f[0] in F.SCI_SRC or f[0] in F.SCI_EN]
    print("feeds:", len(feeds))
    with ThreadPoolExecutor(16) as ex: res = list(ex.map(one, feeds))
    seen, items = set(), []
    for it in sorted([x for r in res for x in r], key=lambda x: -x["ts"]):
        k = (it["gr"], re.sub(r"\W+", "", it["t"])[:45])
        if k in seen: continue
        seen.add(k); items.append(it)
    cnt, keep = {}, []
    for it in items:
        cnt[it["gr"]] = cnt.get(it["gr"], 0) + 1
        if cnt[it["gr"]] <= 30: keep.append(it)
    now = int(time.time())
    # ما أُثري سابقًا (وصف وصور وروابط حقيقية) يُعاد استعماله ولا يُجلب من جديد
    prev, imgchk = {}, {}
    for fn in ("news.json", "mag.json"):
        try:
            pj = json.load(open(fn, encoding="utf-8")); imgchk.update(pj.get("imgchk") or {})
            if fn == "mag.json":
                for x in pj.get("items", []): prev[x.get("g") or x["s"]] = x
        except Exception: pass
    for it in keep:
        o = prev.get(it["s"])
        if o and o.get("a"):
            for k in ("b", "bf", "imgs", "img", "vids", "vid", "u", "g", "s", "tr", "a", "dv", "pd", "pv", "auds", "fa"): 
                if k in o: it[k] = o[k]
    todo = [it for it in keep if not it.get("a")]
    deadline = time.time() + 150
    print("enrich:", len(todo), "of", len(keep))
    with ThreadPoolExecutor(12) as ex: list(ex.map(lambda it: F.enrich(it, deadline), todo))
    for it in keep:
        if not it.get("fa"): it["fa"] = now
    # فلتر الصور: غير لائق + وجه امرأة. إن تعذّر تحميل نموذج الفحص نحذف كل الصور احتياطًا (لا تُنشر صورة غير مفحوصة)
    try:
        ok = F._nsfw_model() is not None
    except Exception: ok = False
    if ok:
        try: F.filter_images(keep, imgchk, budget=110)
        except Exception as e: print("فلتر الصور فشل:", str(e)[:80]); ok = False
    if not ok:
        print("نموذج فحص الصور غير متاح: تُحذف الصور احتياطًا")
        for it in keep: it["imgs"] = []; it["img"] = ""; it["vids"] = []; it["vid"] = ""; it.pop("a", None)   # يُعاد إثراؤها حين يتوفر نموذج الفحص
    else:
        for it in keep:   # لا فيديوهات في هذا المسار السريع
            it["vids"] = []; it["vid"] = ""
    json.dump({"updated": now, "items": keep, "imgchk": imgchk}, open("mag.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("mag items:", {g: sum(1 for x in keep if x["gr"] == g) for g in F.MAGS})

if __name__ == "__main__": main()
