from sqlalchemy import text

BASE_LIST_SQL = """
WITH latest_price AS (
  SELECT DISTINCT ON (listing_id) listing_id, price
  FROM price_history
  ORDER BY listing_id, effective_date DESC
)
SELECT l.listing_id,
       p.street || ', ' || p.city || ', ' || p.state || ' ' || p.zip AS address,
       lp.price,
       lo.loan_type,
       l.mls_status,
       p.latitude AS lat,
       p.longitude AS lon
FROM   listing l
JOIN   property p  ON p.property_id  = l.property_id
JOIN   loan     lo ON lo.property_id = p.property_id
LEFT   JOIN latest_price lp ON lp.listing_id = l.listing_id
"""

ORDER_CLAUSE = " ORDER BY lp.price NULLS LAST "

DETAIL_SQL = text("""
SELECT l.listing_id,
       p.street || ', ' || p.city || ', ' || p.state || ' ' || p.zip AS address,
       lp.price,
       lo.loan_type,
       l.mls_status,

       p.beds, p.baths, p.sqft,
       lo.interest_rate, lo.balance, lo.piti,
       r.name AS realtor_name,
       l.date_added,
       l.mls_link
FROM   listing  l
JOIN   property p  ON p.property_id  = l.property_id
JOIN   loan     lo ON lo.property_id = p.property_id
JOIN   realtor  r  ON r.realtor_id   = l.realtor_id
LEFT   JOIN LATERAL (
     SELECT price
     FROM   price_history ph
     WHERE  ph.listing_id = l.listing_id
     ORDER  BY effective_date DESC
     LIMIT 1
) lp ON true
WHERE  l.listing_id = :lid;
""")