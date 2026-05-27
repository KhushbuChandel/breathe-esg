# Sources — Breathe ESG Prototype

For each data source: what I researched, what I learned, what my sample
data looks like, and what would break in a real deployment.

---

## 1. SAP — Fuel & Procurement

**What I researched:**
SAP material document exports (transaction MB51), standard field names in
SAP MM module, IDoc format vs flat file, SAP internal unit codes (MEINS),
plant/company code structure (WERKS, BUKRS).

**What I learned:**
- SAP exports use German field abbreviations regardless of system language
  (MENGE = Menge = quantity, MEINS = Mengeneinheit = unit of measure)
- Dates are always YYYYMMDD with no separators
- Units are SAP-internal codes: L (litres), KG (kilograms), ST (pieces),
  M3 (cubic metres) — not human-readable
- Plant codes (WERKS) are 4-digit numbers that mean nothing without a
  client-specific lookup table
- Material numbers (MATNR) are client-defined — DIES001 is my invention;
  real clients might use anything

**What my sample data looks like:**
Six rows of fuel purchases across three plants (Mumbai HQ, Pune Factory,
Delhi Warehouse), two fuel types (diesel, petrol), one LPG purchase.
Dates in YYYYMMDD format, units in SAP codes, German field headers.

**What would break in real deployment:**
- Material numbers: we'd need the client's full material master extract
  to build the lookup table. Without it, unknown MATNRs are skipped.
- Plant codes: same — the WERKS→facility name lookup is hardcoded here.
- Multi-currency: if a plant purchases in USD and books in INR, the
  NETWR field has the local currency value and WAERS has the currency code.
  We ignore NETWR entirely (we don't need cost for carbon), but a finance
  integration would need FX conversion.
- IDoc format: some SAP configs only support IDoc XML export, which has
  a completely different structure and would need a separate parser.

---

## 2. Utility — Electricity

**What I researched:**
Green Button Data standard (US), MSEDCL and BSES portal export formats
(India), typical utility bill CSV structures, tariff code systems
(HT-I, HT-II, LT-II in Maharashtra), India grid emission factors from
Central Electricity Authority (CEA).

**What I learned:**
- Indian utilities (MSEDCL, BSES, BESCOM) all offer portal CSV exports
  but the column names differ by utility — there is no Indian equivalent
  of the US Green Button standard
- Billing periods rarely align with calendar months — a January bill might
  cover Dec 28 to Jan 29
- Industrial consumers (HT = High Tension) have separate demand charges
  (kW) and consumption charges (kWh) — only kWh matters for carbon
- India's grid emission factor from CEA 2023: 0.716 kg CO2e per kWh
  (varies by state grid but national average is standard for Scope 2)

**What my sample data looks like:**
Five rows across three facilities (Mumbai HQ, Pune Factory, Delhi Warehouse),
two utilities (MSEDCL, BSES), two billing months, realistic kWh values
for industrial consumers (45,000–135,000 kWh/month).

**What would break in real deployment:**
- Column name inconsistency: MSEDCL exports use different headers than
  BSES. We'd need utility-specific parsers or a column mapping config.
- PDF bills: many facilities teams only have PDF bills, not CSV exports.
  Parsing PDFs requires OCR and is fragile.
- Market-based vs location-based Scope 2: the GHG Protocol allows two
  methods. We implement location-based (grid average factor). Market-based
  requires the utility's actual energy certificate data.
- Missing months: if a facility forgets to upload February, there's no
  automatic gap detection.

---

## 3. Corporate Travel — Flights, Hotels, Ground

**What I researched:**
Navan (formerly TripActions) CSV export format, Concur Travel export
fields, IATA airport code database, DEFRA 2023 aviation emission factors
(economy vs business class), hotel emission factors, GHG Protocol
guidance on Scope 3 Category 6 (Business Travel).

**What I learned:**
- Travel platforms export one row per segment, not one row per trip —
  a trip with a flight, hotel, and taxi is three rows with the same trip_id
- Distances are almost never given — platforms provide origin/destination
  airport codes and the integrator must calculate distance
- Business class has a ~2.75x higher emission factor than economy because
  business seats take more physical space per passenger (radiative forcing)
- Hotel emission factors are per room-night, not per person — DEFRA 2023
  gives 31 kg CO2e per room-night as a global average
- Ground transport is the hardest: sometimes you get distance, sometimes
  just cost, sometimes neither

**What my sample data looks like:**
Six segments across four trips: domestic flights (BOM-DEL, BOM-BLR),
an international flight (DEL-LHR return in business class), a hotel stay
in Delhi, and a taxi. Realistic Indian corporate travel patterns.

**What would break in real deployment:**
- Unknown airport codes: our lookup table has 8 airports. Real deployments
  need the full IATA database (9,000+ airports). Unknown codes produce
  distance = 0 and should be auto-flagged.
- Connecting flights: we treat every flight as direct. DEL→LHR via DXB
  would be recorded as one DEL→LHR segment, undercounting emissions.
- Radiative forcing: aviation has a warming effect beyond CO2 (contrails,
  NOx). Some reporting frameworks apply an RF multiplier of 1.9x. We use
  DEFRA factors which already account for this, but it should be documented.
- Personal vs business travel: platforms sometimes include personal trips
  booked on corporate cards. No automated way to filter these.