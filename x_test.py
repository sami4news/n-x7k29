# اختبار حسابات X فقط (لا يغيّر الأخبار): يجرّب كل حساب في x_accounts.txt ويطبع النتيجة في سجل التشغيل
import sys, time
sys.argv = ["x"]
import fetch_news as F

ok = 0
rows = []
for nm, ch, fl in F.x_accounts():
    user = ch[2:]
    t0 = time.time()
    try:
        root = F.fetch_x(nm, user, fl)
        its = list(root.iter("item"))
        last = its[0].findtext("pubDate") if its else "-"
        first = (its[0].findtext("title") or "")[:50] if its else ""
        rows.append("✅ %-18s %-6s منشورات=%-3d أحدثها=%s | %s" % (user, F.X_STAT.get(user, "?"), len(its), last[:19], first)); ok += 1
    except Exception as e:
        rows.append("❌ %-18s %s" % (user, str(e)[:70]))
print("\n".join(rows))
print("\nالنتيجة: نجح %d من %d حسابًا" % (ok, len(rows)))
print("خوادم Nitter المعطّلة:", sorted(F._X_DEAD))
sys.exit(0)
