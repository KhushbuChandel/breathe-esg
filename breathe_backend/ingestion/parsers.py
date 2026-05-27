import csv
import io
from decimal import Decimal
from datetime import datetime, date


# ── Emission factors (kg CO2e per unit) ──────────────────────────────────────
# Source: DEFRA 2023 / India GHG Platform
EMISSION_FACTORS = {
    'diesel_litre':     Decimal('2.6391'),   # kg CO2e per litre
    'petrol_litre':     Decimal('2.3153'),
    'lpg_kg':           Decimal('2.9830'),
    'electricity_kwh':  Decimal('0.7160'),   # India grid average 2023 (CEA)
    'flight_economy_km':   Decimal('0.1553'),
    'flight_business_km':  Decimal('0.4285'),
    'hotel_night':      Decimal('31.0000'),  # kg CO2e per room-night (DEFRA)
    'taxi_inr':         Decimal('0.0850'),   # rough: kg CO2e per INR spent
}

# Airport coordinates for distance calculation (lat, lon)
AIRPORT_COORDS = {
    'BOM': (19.0896, 72.8656),  # Mumbai
    'DEL': (28.5562, 77.1000),  # Delhi
    'BLR': (13.1986, 77.7066),  # Bangalore
    'MAA': (12.9941, 80.1709),  # Chennai
    'HYD': (17.2403, 78.4294),  # Hyderabad
    'LHR': (51.4700, -0.4543),  # London Heathrow
    'JFK': (40.6413, -73.7781), # New York JFK
    'DXB': (25.2532, 55.3657),  # Dubai
}

# SAP plant code → facility name lookup
PLANT_LOOKUP = {
    '1000': 'Head Office Mumbai',
    '2000': 'Factory Pune',
    '3000': 'Warehouse Delhi',
}

# SAP material → fuel type lookup
MATERIAL_LOOKUP = {
    'DIES001': ('diesel', 'L'),
    'PETT001': ('petrol', 'L'),
    'LPGG001': ('lpg',    'KG'),
}


def haversine_km(coord1, coord2):
    """Calculate great-circle distance between two (lat, lon) pairs in km."""
    import math
    lat1, lon1 = map(math.radians, coord1)
    lat2, lon2 = map(math.radians, coord2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 6371 * 2 * math.asin(math.sqrt(a))


def parse_sap_date(date_str):
    """SAP dates come as YYYYMMDD strings."""
    try:
        return datetime.strptime(date_str.strip(), '%Y%m%d').date()
    except Exception:
        return None


# ── SAP Parser ────────────────────────────────────────────────────────────────

def parse_sap(file_content: str) -> list[dict]:
    """
    Parse SAP flat file CSV export.
    Returns list of normalized emission record dicts.
    """
    results = []
    errors = []
    reader = csv.DictReader(io.StringIO(file_content))

    for i, row in enumerate(reader):
        try:
            matnr = row['MATNR'].strip()
            if matnr not in MATERIAL_LOOKUP:
                errors.append({'row': i+2, 'reason': f'Unknown material {matnr}'})
                continue

            fuel_type, sap_unit = MATERIAL_LOOKUP[matnr]
            raw_unit = row['MEINS'].strip()
            quantity = Decimal(row['MENGE'].strip())
            doc_date = parse_sap_date(row['BLDAT'])

            if not doc_date:
                errors.append({'row': i+2, 'reason': 'Invalid date'})
                continue

            # Unit normalization: SAP 'L' = litres, 'KG' = kg
            if raw_unit == 'L':
                norm_unit = 'litres'
                if fuel_type == 'diesel':
                    ef = EMISSION_FACTORS['diesel_litre']
                    ef_label = 'DEFRA 2023 - Diesel'
                else:
                    ef = EMISSION_FACTORS['petrol_litre']
                    ef_label = 'DEFRA 2023 - Petrol'
            elif raw_unit == 'KG':
                norm_unit = 'kg'
                ef = EMISSION_FACTORS['lpg_kg']
                ef_label = 'DEFRA 2023 - LPG'
            else:
                errors.append({'row': i+2, 'reason': f'Unknown unit {raw_unit}'})
                continue

            co2e = quantity * ef

            results.append({
                'source_row_id':        f"SAP-{row['MANDT']}-{i+2}",
                'scope':                'SCOPE_1',
                'category':             'FUEL_STATIONARY',
                'raw_quantity':         float(quantity),
                'raw_unit':             raw_unit,
                'raw_data':             dict(row),
                'normalized_quantity':  float(round(co2e, 4)),
                'normalized_unit':      'kg_co2e',
                'emission_factor_used': float(ef),
                'emission_factor_source': ef_label,
                'period_start':         doc_date.isoformat(),
                'period_end':           doc_date.isoformat(),
                'facility_name':        PLANT_LOOKUP.get(row['WERKS'].strip(), row['WERKS']),
                'country':              'India',
                'description':          f"{row['MAKTX'].strip()} - {quantity} {norm_unit} from {row['NAME1'].strip()}",
            })

        except Exception as e:
            errors.append({'row': i+2, 'reason': str(e)})

    return results, errors


# ── Utility Parser ─────────────────────────────────────────────────────────────

def parse_utility(file_content: str) -> tuple[list[dict], list[dict]]:
    """
    Parse utility portal CSV export (Green Button style).
    """
    results = []
    errors = []
    reader = csv.DictReader(io.StringIO(file_content))

    for i, row in enumerate(reader):
        try:
            kwh = Decimal(row['consumption_kwh'].strip())
            ef = EMISSION_FACTORS['electricity_kwh']
            co2e = kwh * ef

            period_start = date.fromisoformat(row['billing_period_start'].strip())
            period_end   = date.fromisoformat(row['billing_period_end'].strip())

            results.append({
                'source_row_id':        f"UTIL-{row['meter_id'].strip()}-{i+2}",
                'scope':                'SCOPE_2',
                'category':             'ELECTRICITY',
                'raw_quantity':         float(kwh),
                'raw_unit':             'kWh',
                'raw_data':             dict(row),
                'normalized_quantity':  float(round(co2e, 4)),
                'normalized_unit':      'kg_co2e',
                'emission_factor_used': float(ef),
                'emission_factor_source': 'CEA India Grid Emission Factor 2023',
                'period_start':         period_start.isoformat(),
                'period_end':           period_end.isoformat(),
                'facility_name':        row['facility_name'].strip(),
                'country':              'India',
                'description':          f"Electricity - {row['facility_name'].strip()} - {kwh} kWh ({row['tariff_code'].strip()})",
            })

        except Exception as e:
            errors.append({'row': i+2, 'reason': str(e)})

    return results, errors


# ── Travel Parser ──────────────────────────────────────────────────────────────

def parse_travel(file_content: str) -> tuple[list[dict], list[dict]]:
    """
    Parse Navan/Concur style travel export.
    Handles flights (with distance calc), hotels, and ground transport.
    """
    results = []
    errors = []
    reader = csv.DictReader(io.StringIO(file_content))

    for i, row in enumerate(reader):
        try:
            segment = row['segment_type'].strip().upper()
            travel_date = date.fromisoformat(row['travel_date'].strip())
            return_date_str = row.get('return_date', '').strip()
            return_date = date.fromisoformat(return_date_str) if return_date_str else travel_date

            if segment == 'FLIGHT':
                origin = row['origin'].strip().upper()
                dest   = row['destination'].strip().upper()

                # Calculate distance from airport codes
                if origin in AIRPORT_COORDS and dest in AIRPORT_COORDS:
                    dist_km = Decimal(str(round(haversine_km(
                        AIRPORT_COORDS[origin], AIRPORT_COORDS[dest]
                    ), 2)))
                else:
                    # Unknown airport — flag it but still record
                    dist_km = Decimal('0')

                cabin = row.get('cabin_class', 'ECONOMY').strip().upper()
                ef_key = 'flight_business_km' if cabin == 'BUSINESS' else 'flight_economy_km'
                ef = EMISSION_FACTORS[ef_key]
                co2e = dist_km * ef

                results.append({
                    'source_row_id':        f"TRV-{row['trip_id'].strip()}-FLT-{i+2}",
                    'scope':                'SCOPE_3',
                    'category':             'BUSINESS_TRAVEL_AIR',
                    'raw_quantity':         float(dist_km),
                    'raw_unit':             'km',
                    'raw_data':             dict(row),
                    'normalized_quantity':  float(round(co2e, 4)),
                    'normalized_unit':      'kg_co2e',
                    'emission_factor_used': float(ef),
                    'emission_factor_source': 'DEFRA 2023 - Aviation',
                    'period_start':         travel_date.isoformat(),
                    'period_end':           return_date.isoformat(),
                    'facility_name':        '',
                    'country':              'India',
                    'description':          f"Flight {origin}→{dest} ({cabin}) - {row['traveler_name'].strip()} - {dist_km} km",
                })

            elif segment == 'HOTEL':
                nights = int(row.get('nights', 1) or 1)
                ef = EMISSION_FACTORS['hotel_night']
                co2e = Decimal(str(nights)) * ef

                results.append({
                    'source_row_id':        f"TRV-{row['trip_id'].strip()}-HTL-{i+2}",
                    'scope':                'SCOPE_3',
                    'category':             'BUSINESS_TRAVEL_HOTEL',
                    'raw_quantity':         float(nights),
                    'raw_unit':             'nights',
                    'raw_data':             dict(row),
                    'normalized_quantity':  float(round(co2e, 4)),
                    'normalized_unit':      'kg_co2e',
                    'emission_factor_used': float(ef),
                    'emission_factor_source': 'DEFRA 2023 - Hotel Stay',
                    'period_start':         travel_date.isoformat(),
                    'period_end':           travel_date.isoformat(),
                    'facility_name':        row.get('hotel_name', '').strip(),
                    'country':              'India',
                    'description':          f"Hotel - {row.get('hotel_name','').strip()} - {nights} nights - {row['traveler_name'].strip()}",
                })

            elif segment == 'GROUND':
                amount = Decimal(row.get('amount', '0').strip() or '0')
                ef = EMISSION_FACTORS['taxi_inr']
                co2e = amount * ef

                results.append({
                    'source_row_id':        f"TRV-{row['trip_id'].strip()}-GRD-{i+2}",
                    'scope':                'SCOPE_3',
                    'category':             'BUSINESS_TRAVEL_GROUND',
                    'raw_quantity':         float(amount),
                    'raw_unit':             'INR',
                    'raw_data':             dict(row),
                    'normalized_quantity':  float(round(co2e, 4)),
                    'normalized_unit':      'kg_co2e',
                    'emission_factor_used': float(ef),
                    'emission_factor_source': 'Spend-based estimate - Ground Transport',
                    'period_start':         travel_date.isoformat(),
                    'period_end':           travel_date.isoformat(),
                    'facility_name':        '',
                    'country':              'India',
                    'description':          f"Ground transport ({row.get('vendor','Taxi').strip()}) - {row['traveler_name'].strip()}",
                })

        except Exception as e:
            errors.append({'row': i+2, 'reason': str(e)})

    return results, errors