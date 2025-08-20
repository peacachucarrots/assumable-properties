def normalize_cols(cols):
    return [str(c).strip().replace("\n"," ").replace("\r"," ") for c in cols]

def match_column(cols, wanted_key):
    want = wanted_key.lower()
    for c in cols:
        if c.lower() == want:
            return c
    norm = {c: " ".join(c.lower().split()) for c in cols}
    for c, lc in norm.items():
        if lc == " ".join(wanted_key.lower().split()):
            return c
    token_map = {
        "date added": ["date","added"],
        "realtor name": ["realtor","agent","broker","name"],
        "mls listing link": ["mls","listing","link","url"],
        "property address": ["property","address","addr","street"],
        "type of assumable (fha, va, non veteran va)": ["type","assumable","va","fha","loan"],
        "assumable interest rate": ["rate","interest","assumable","apr"],
        "piti": ["piti","payment"],
        "asking price": ["price","asking","list"],
        "assumable loan balance": ["assumable","balance","loan","remaining","principal"],
        "equity to cover": ["equity"],
        "response from realtor/seller": ["response","remarks","realtor","seller","agent","comment","note","remarks"],
        "done running numbers?": ["done","numbers","complete","finished","calc","analy"],
        "does it pass roi number criteria?": ["roi","pass","criteria","investor","fha","va"],
        "sent to clients": ["sent","clients","emailed","notified","shared"],
        "link to property analysis": ["analysis","link","sheet","google","docs"],
        "beds": ["beds","br","bedrooms"],
        "baths": ["baths","ba","bathrooms"],
        "sqft": ["sqft","square feet","sf"],
        "hoa/month": ["hoa"],
        "mls status": ["mls","status"],
        "loan servicer": ["servicer","loan servicer"],
        "allow investor to assume the va loan?": ["investor","assume","va","allowed","permit"],
        "full response from amy": ["amy","response","note","comment"]
    }
    if wanted_key in token_map:
        req = token_map[wanted_key]
        for c in cols:
            lc = c.lower()
            if sum(1 for t in req if t in lc) >= max(2, len(req)-1):
                return c
    return None
