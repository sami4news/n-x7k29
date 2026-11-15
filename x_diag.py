# تشخيص طرق جلب X (الجولة 2): يطبع لكل طريقة رمز الرد وبداية ما رجع — لا يغيّر شيئًا
import urllib.request, urllib.error, sys, time, json
U = sys.argv[1] if len(sys.argv) > 1 else "taif_now"
BR = {"User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36", "Accept-Language": "ar,en;q=0.8"}
TB = {"User-Agent": "Twitterbot/1.0"}
GB = {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}
def go(nm, url, hd=BR, n=300, keys=False):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=hd), timeout=15)
        b = r.read(400000).decode("utf-8", "replace")
        extra = ""
        if keys:
            try:
                j = json.loads(b); extra = " مفاتيح=" + str(list(j.keys())[:8])
                st = j.get("results") or j.get("statuses") or j.get("tweets") or []
                extra += " منشورات=%d" % len(st) if isinstance(st, list) else ""
            except Exception: pass
        print("✅ %-26s %s حجم=%d%s | %s" % (nm, r.status, len(b), extra, b[:n].replace("\n", " ")))
    except urllib.error.HTTPError as e:
        print("❌ %-26s HTTP %s %s" % (nm, e.code, str(e.reason)[:40]))
    except Exception as e:
        print("❌ %-26s %s" % (nm, str(e)[:90]))
go("fx-v2-statuses", "https://api.fxtwitter.com/2/profile/%s/statuses" % U, keys=True)
go("fx-v2-statuses-b", "https://api.fxtwitter.com/2/profile/%s/statuses?count=20" % U, keys=True)
go("fx-profile-v2", "https://api.fxtwitter.com/2/profile/%s" % U, keys=True, n=200)
go("fx-profile-v1-keys", "https://api.fxtwitter.com/%s" % U, keys=True, n=100)
for i in range(3):
    go("synd-timeline-twitterbot#%d" % (i + 1), "https://syndication.twitter.com/srv/timeline-profile/screen-name/%s" % U, hd=TB, n=120)
    time.sleep(4)
go("synd-timeline-x-host", "https://syndication.x.com/srv/timeline-profile/screen-name/%s" % U, hd=TB, n=120)
go("synd-cdn-twimg-srv", "https://cdn.syndication.twimg.com/srv/timeline-profile/screen-name/%s" % U, hd=TB, n=120)
go("synd-cdn-timeline", "https://cdn.syndication.twimg.com/timeline/profile?screen_name=%s" % U, hd=TB, n=200)
go("x-googlebot", "https://x.com/%s" % U, hd=GB, n=120)
go("bing-news-rss", "https://www.bing.com/news/search?q=site%%3Ax.com+%s&format=rss" % U, n=200)
go("google-news-rss", "https://news.google.com/rss/search?q=site:x.com/%s&hl=ar&gl=SA&ceid=SA:ar" % U, n=200)
go("nitter-privacy-instance", "https://nitter.privacyredirect.com/%s/rss" % U, n=120)
go("nitter-catsarch", "https://nitter.catsarch.com/%s/rss" % U, n=120)
go("nitter-kareem", "https://nitter.kareem.one/%s/rss" % U, n=120)
go("nitter-1d4", "https://nitter.1d4.us/%s/rss" % U, n=120)
