"""US state abbreviations (50 states). DC and territories are map-only for now."""

US_STATE_ABBREVS = (
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
)

STATE_ABBREV_TO_NAME = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
}

# 2020 census apportionment (435 voting seats).
HOUSE_SEATS_BY_STATE = {
    "AL": 7, "AK": 1, "AZ": 9, "AR": 4, "CA": 52, "CO": 8, "CT": 5, "DE": 1,
    "FL": 28, "GA": 14, "HI": 2, "ID": 2, "IL": 17, "IN": 9, "IA": 4, "KS": 4,
    "KY": 6, "LA": 6, "ME": 2, "MD": 8, "MA": 9, "MI": 13, "MN": 8, "MS": 4,
    "MO": 8, "MT": 2, "NE": 3, "NV": 4, "NH": 2, "NJ": 12, "NM": 3, "NY": 26,
    "NC": 14, "ND": 1, "OH": 15, "OK": 5, "OR": 6, "PA": 17, "RI": 2, "SC": 7,
    "SD": 1, "TN": 9, "TX": 38, "UT": 4, "VT": 1, "VA": 11, "WA": 10, "WV": 2,
    "WI": 8, "WY": 1,
}

# Census FIPS state codes (for congressional district GeoJSON).
STATE_FIPS_TO_ABBREV = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT",
    "10": "DE", "11": "DC", "12": "FL", "13": "GA", "15": "HI", "16": "ID", "17": "IL",
    "18": "IN", "19": "IA", "20": "KS", "21": "KY", "22": "LA", "23": "ME", "24": "MD",
    "25": "MA", "26": "MI", "27": "MN", "28": "MS", "29": "MO", "30": "MT", "31": "NE",
    "32": "NV", "33": "NH", "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND",
    "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD",
    "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA", "54": "WV",
    "55": "WI", "56": "WY",
}

STATE_ABBREV_TO_FIPS = {abbrev: fips for fips, abbrev in STATE_FIPS_TO_ABBREV.items()}

# 2024 electoral vote apportionment (538 total).
ELECTORAL_VOTES_BY_STATE = {
    "AL": 9, "AK": 3, "AZ": 11, "AR": 6, "CA": 54, "CO": 10, "CT": 7, "DE": 3,
    "FL": 30, "GA": 16, "HI": 4, "ID": 4, "IL": 19, "IN": 11, "IA": 6, "KS": 6,
    "KY": 8, "LA": 8, "ME": 4, "MD": 10, "MA": 11, "MI": 15, "MN": 10, "MS": 6,
    "MO": 10, "MT": 4, "NE": 5, "NV": 6, "NH": 4, "NJ": 14, "NM": 5, "NY": 28,
    "NC": 16, "ND": 3, "OH": 17, "OK": 7, "OR": 8, "PA": 19, "RI": 4, "SC": 9,
    "SD": 3, "TN": 11, "TX": 40, "UT": 6, "VT": 3, "VA": 13, "WA": 12, "WV": 4,
    "WI": 10, "WY": 3,
}

TOTAL_ELECTORAL_VOTES = sum(ELECTORAL_VOTES_BY_STATE.values())
ELECTORAL_VOTES_TO_WIN = TOTAL_ELECTORAL_VOTES // 2 + 1

# Approximate 2020 census populations (used for electorate simulation).
STATE_POPULATION = {
    "AL": 5024279, "AK": 733391, "AZ": 7151502, "AR": 3011524, "CA": 39538223,
    "CO": 5773714, "CT": 3605944, "DE": 989948, "FL": 21538187, "GA": 10711908,
    "HI": 1455271, "ID": 1839106, "IL": 12812508, "IN": 6785528, "IA": 3190369,
    "KS": 2937880, "KY": 4505836, "LA": 4657757, "ME": 1362359, "MD": 6177224,
    "MA": 7029917, "MI": 10077331, "MN": 5706494, "MS": 2961279, "MO": 6154913,
    "MT": 1084225, "NE": 1961504, "NV": 3104614, "NH": 1377529, "NJ": 9288994,
    "NM": 2117522, "NY": 20201249, "NC": 10439388, "ND": 779094, "OH": 11799448,
    "OK": 3959353, "OR": 4237256, "PA": 13002700, "RI": 1097379, "SC": 5118425,
    "SD": 886667, "TN": 6910840, "TX": 29145505, "UT": 3271616, "VT": 643077,
    "VA": 8631393, "WA": 7705281, "WV": 1793716, "WI": 5893718, "WY": 576851,
}
