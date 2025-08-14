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

  -- address / property
  p.street, p.unit, p.city, p.state, p.zip,
  p.beds, p.baths, p.sqft, p.hoa_month,

  -- listing
  l.date_added, l.mls_link, l.mls_status,
  l.equity_to_cover, l.sent_to_clients, l.investor_ok,

  -- realtor
  r.name AS realtor_name,

  -- loan
  lo.loan_type, lo.interest_rate, lo.balance, lo.piti,
  lo.loan_servicer, lo.investor_allowed,

  -- price
  lp.price AS asking_price,
  lp.effective_date AS asking_price_date,

  -- analysis
  la.url AS analysis_url,
  la.roi_pass,
  la.run_complete AS done_running_numbers,
  la.run_date AS analysis_run_date,

  -- price history
  COALESCE(ph_all.items, '[]'::json) AS price_history,
  COALESCE(resp_all.items, '[]'::json) AS responses

FROM listing l
JOIN property p ON p.property_id = l.property_id
JOIN realtor  r ON r.realtor_id = l.realtor_id
LEFT JOIN loan lo ON lo.property_id = p.property_id

LEFT JOIN LATERAL (
  SELECT ph.price, ph.effective_date
  FROM price_history ph
  WHERE ph.listing_id = l.listing_id
  ORDER BY ph.effective_date DESC, ph.price_id DESC
  LIMIT 1
) lp ON TRUE

LEFT JOIN LATERAL (
  SELECT a.url, a.roi_pass, a.run_complete, a.run_date
  FROM analysis a
  WHERE a.listing_id = l.listing_id
  ORDER BY a.run_date DESC, a.analysis_id DESC
  LIMIT 1
) la ON TRUE

LEFT JOIN LATERAL (
  SELECT json_agg(json_build_object(
           'price_id', ph.price_id,
           'effective_date', ph.effective_date,
           'price', ph.price
         )
         ORDER BY ph.effective_date DESC, ph.price_id DESC) AS items
  FROM price_history ph
  WHERE ph.listing_id = l.listing_id
) ph_all ON TRUE

LEFT JOIN LATERAL (
  SELECT json_agg(json_build_object(
           'response_id', resp.response_id,
           'author', resp.author,
           'note_text', resp.note_text,
           'created_at', resp.created_at
         )
         ORDER BY resp.created_at DESC, resp.response_id DESC) AS items
  FROM response resp
  WHERE resp.listing_id = l.listing_id
) resp_all ON TRUE

WHERE l.listing_id = :lid;
""")