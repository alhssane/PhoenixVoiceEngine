"""
PhoenixVoiceEngine - Maqam Knowledge V1.0

This knowledge base is intentionally conservative.

Pitch-class interval sets are only a coarse 12-TET representation.
They are NOT treated as a complete representation of Arabic maqam,
because maqamat also depend on ajnas, melodic course (sayr),
cadential behavior, and performance practice.

The candidate engine therefore uses these profiles as weak evidence,
not as ground truth.
"""

MAQAM_KNOWLEDGE = {
    "RAST": {
        "family": "Rast",
        "root_jins": "Rast",
        "upper_jins": ["Upper Rast", "Nahawand"],
        "scale_pc_intervals_12tet": [0, 2, 4, 5, 7, 9, 11],
        "root_jins_12tet": [0, 2, 4, 5, 7],
        "upper_start_degree": 7,
    },
    "BAYATI": {
        "family": "Bayati",
        "root_jins": "Bayati",
        "upper_jins": ["Nahawand", "Rast"],
        "scale_pc_intervals_12tet": [0, 1, 3, 5, 7, 8, 10],
        "root_jins_12tet": [0, 1, 3, 5],
        "upper_start_degree": 5,
    },
    "HIJAZ": {
        "family": "Hijaz",
        "root_jins": "Hijaz",
        "upper_jins": ["Nahawand", "Rast"],
        "scale_pc_intervals_12tet": [0, 1, 4, 5, 7, 8, 10],
        "root_jins_12tet": [0, 1, 4, 5],
        "upper_start_degree": 5,
    },
    "NAHAWAND": {
        "family": "Nahawand",
        "root_jins": "Nahawand",
        "upper_jins": ["Hijaz", "Kurd"],
        "scale_pc_intervals_12tet": [0, 2, 3, 5, 7, 8, 11],
        "root_jins_12tet": [0, 2, 3, 5, 7],
        "upper_start_degree": 7,
    },
    "KURD": {
        "family": "Kurd",
        "root_jins": "Kurd",
        "upper_jins": ["Hijaz", "Nahawand"],
        "scale_pc_intervals_12tet": [0, 1, 3, 5, 7, 8, 10],
        "root_jins_12tet": [0, 1, 3, 5],
        "upper_start_degree": 5,
    },
    "AJAM": {
        "family": "Ajam",
        "root_jins": "Ajam",
        "upper_jins": ["Ajam"],
        "scale_pc_intervals_12tet": [0, 2, 4, 5, 7, 9, 11],
        "root_jins_12tet": [0, 2, 4, 5, 7],
        "upper_start_degree": 7,
    },
    "SIKAH": {
        "family": "Sikah",
        "root_jins": "Sikah",
        "upper_jins": ["Rast"],
        "scale_pc_intervals_12tet": [0, 1, 3, 5, 7, 8, 10],
        "root_jins_12tet": [0, 1, 3],
        "upper_start_degree": 5,
    },
    "SABA": {
        "family": "Saba",
        "root_jins": "Saba",
        "upper_jins": ["Hijaz", "Saba"],
        "scale_pc_intervals_12tet": [0, 1, 3, 4, 6, 7, 10],
        "root_jins_12tet": [0, 1, 3, 4],
        "upper_start_degree": 6,
    },
}