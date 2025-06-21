-- Property
CREATE TABLE property (
    property_id  serial PRIMARY KEY,
    street text, city text, state char(2), zip text, unit text,
    beds smallint, baths smallint, sqft int, hoa_month numeric,
    UNIQUE (street, unit, city, state, zip)
);

-- Realtor
CREATE TABLE realtor (
    realtor_id  serial PRIMARY KEY,
    name text UNIQUE
);

-- Listing
CREATE TABLE listing (
    listing_id   serial PRIMARY KEY,
    property_id  int NOT NULL REFERENCES property,
    realtor_id   int NOT NULL REFERENCES realtor,
    date_added   date,
    mls_link     text,
    mls_id       text UNIQUE,
    mls_status   text,
    sent_to_clients boolean,
    investor_ok  boolean   -- copy of loan flag for fast filter
);

-- Loan (assumable)
CREATE TABLE loan (
    loan_id      serial PRIMARY KEY,
    property_id  int NOT NULL REFERENCES property,
    loan_type    text check (loan_type in ('FHA','VA','NVVA','Maybe_NVVA', 'CONV')),
    interest_rate numeric(5,3),
    balance       numeric(14,2),
    piti          numeric(12,2),
    loan_servicer text,
    investor_allowed boolean
);

-- Price history per listing
CREATE TABLE price_history (
    price_id    serial PRIMARY KEY,
    listing_id  int NOT NULL REFERENCES listing ON DELETE CASCADE,
    effective_date date default current_date,
    price numeric(12,2)
);

-- Analysis runs
CREATE TABLE analysis (
    analysis_id serial PRIMARY KEY,
    listing_id  int NOT NULL REFERENCES listing ON DELETE CASCADE,
    run_date    timestamptz default now(),
    url         text,
    roi_pass    boolean,
    run_complete boolean
);

-- Threaded responses / notes
CREATE TABLE response (
    response_id serial PRIMARY KEY,
    listing_id  int NOT NULL REFERENCES listing ON DELETE CASCADE,
    author      text,
    note_text   text,
    created_at  timestamptz default now()
);