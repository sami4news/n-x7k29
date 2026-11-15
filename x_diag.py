# تشخيص طرق جلب X: يطبع لكل طريقة رمز الرد وبداية ما رجع (لحساب واحد) — لا يغيّر شيئًا
import urllib.request, urllib.error, sys
U = sys.argv[1] if len(sys.argv) > 1 else "taif_now"
UA = {"User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36", "Accept-Language": "ar,en;q=0.8"}
TESTS = [
 ("syndication-timeline", "https://syndication.twitter.com/srv/timeline-profile/screen-name/%s?showReplies=false" % U),
 ("syndication-cdn", "https://cdn.syndication.twimg.com/timeline/profile?screen_name=%s&suppress_response_codes=true" % U),
 ("x.com-profile", "https://x.com/%s" % U),
 ("jina-reader", "https://r.jina.ai/https://x.com/%s" % U),
 ("fxtwitter-api", "https://api.fxtwitter.com/%s" % U),
 ("vxtwitter-api", "https://api.vxtwitter.com/%s" % U),
 ("rsshub", "https://rsshub.app/twitter/user/%s" % U),
 ("nitter.net-rss", "https://nitter.net/%s/rss" % U),
 ("xcancel-rss", "https://xcancel.com/%s/rss" % U),
 ("nitter.poast-rss", "https://nitter.poast.org/%s/rss" % U),
 ("nitter.privacydev-rss", "https://nitter.privacydev.net/%s/rss" % U),
 ("nitter.tiekoetter-rss", "https://nitter.tiekoetter.com/%s/rss" % U),
 ("bing-site-search", "https://www.bing.com/news/search?q=site%%3Ax.com%%2F%s&format=rss" % U),
]
for nm, url in TESTS:
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=12)
        b = r.read(3000).decode("utf-8", "replace").replace("\n", " ")
        print("✅ %-22s %s  نوع=%s  بداية: %s" % (nm, r.status, r.headers.get("content-type", "?")[:30], b[:160]))
    except urllib.error.HTTPError as e:
        print("❌ %-22s HTTP %s %s" % (nm, e.code, str(e.reason)[:40]))
    except Exception as e:
        print("❌ %-22s %s" % (nm, str(e)[:90]))
