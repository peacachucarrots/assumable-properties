-- Property
CREATE TABLE IF NOT EXISTS property (
    property_id  serial PRIMARY KEY,
    street text, city text, state char(2), zip text, unit text,
    beds smallint, baths numeric(3,1), sqft int,
    hoa_amount numeric(12,2), hoa_frequency text
        CHECK (hoa_frequency IN ('Monthly','Quarterly','Semi-Annual','Annual')),
    latitude double precision, longitude double precision,
    UNIQUE (street, unit, city, state, zip)
);

-- Realtor
CREATE TABLE IF NOT EXISTS realtor (
    realtor_id  serial PRIMARY KEY,
    name text UNIQUE
);

-- Listing
CREATE TABLE IF NOT EXISTS listing (
    listing_id   serial PRIMARY KEY,
    property_id  int NOT NULL REFERENCES property,
    realtor_id   int NOT NULL REFERENCES realtor,
    date_added   date,
    mls_id       text,
    mls_link     text,
    mls_link_norm text GENERATED ALWAYS AS (COALESCE(mls_link, '')) STORED,
    mls_status   text,
    equity_to_cover numeric(12, 2),
    sent_to_clients boolean,
    CONSTRAINT listing_prop_realtor_link_unique
      UNIQUE (property_id, realtor_id, mls_link_norm)
);

-- Loan (assumable)
CREATE TABLE IF NOT EXISTS loan (
    loan_id      serial PRIMARY KEY,
    property_id  int NOT NULL UNIQUE REFERENCES property,
    loan_type    text check (loan_type in ('FHA','VA','NVVA','Maybe_NVVA', 'CONV')),
    interest_rate numeric(5,3),
    balance       numeric(14,2),
    piti          numeric(12,2),
    loan_servicer text,
    investor_allowed boolean
);

-- Price history per listing
CREATE TABLE IF NOT EXISTS price_history (
    price_id    serial PRIMARY KEY,
    listing_id  int NOT NULL REFERENCES listing ON DELETE CASCADE,
    effective_date date default current_date,
    price numeric(12,2)
);

-- Analysis runs
CREATE TABLE IF NOT EXISTS analysis (
    analysis_id  serial PRIMARY KEY,
    listing_id   int NOT NULL REFERENCES listing ON DELETE CASCADE,
    run_date     timestamptz default now(),
    url          text,
    url_norm     text GENERATED ALWAYS AS (COALESCE(url, '')) STORED,
    roi_category text,
    roi_pass     boolean,
    run_complete boolean
);

-- Threaded responses / notes
CREATE TABLE IF NOT EXISTS response (
    response_id serial PRIMARY KEY,
    listing_id  int NOT NULL REFERENCES listing ON DELETE CASCADE,
    author      text,
    note_text   text,
    created_at  timestamptz default now()
);