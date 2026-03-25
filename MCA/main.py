import browser_cookie3
import json

cj = browser_cookie3.chrome(domain_name="mca.gov.in")

cookies = []
for c in cj:
    cookies.append({
        "name": c.name,
        "value": c.value,
        "domain": c.domain,
        "path": c.path
    })

with open("mca_cookies.json", "w") as f:
    json.dump(cookies, f, indent=2)

print("✅ Cookies extracted")
