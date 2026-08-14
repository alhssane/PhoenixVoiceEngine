class AdvancedArabicMaqamDatabase:

    VERSION = "2.0.0"

    def get_maqamat(self):

        return {

            "rast": {

                "root": "C",

                "quarter_tones": [],

                "family": "rast",
            },

            "bayati": {

                "root": "D",

                "quarter_tones": [

                    {
                        "note": "E",
                        "cents": -50,
                    }
                ],

                "family": "bayati",
            },

            "bayati_husayni": {

                "root": "D",

                "quarter_tones": [

                    {
                        "note": "E",
                        "cents": -50,
                    }
                ],

                "family": "bayati",
            },

            "sikah": {

                "root": "E",

                "quarter_tones": [

                    {
                        "note": "E",
                        "cents": -50,
                    }
                ],

                "family": "sikah",
            },

            "sikah_hazzam": {

                "root": "E",

                "quarter_tones": [

                    {
                        "note": "E",
                        "cents": -50,
                    },

                    {
                        "note": "B",
                        "cents": -50,
                    }
                ],

                "family": "sikah",
            },

            "hijaz": {

                "root": "D",

                "quarter_tones": [],

                "family": "hijaz",
            },

            "hijaz_husayni": {

                "root": "D",

                "quarter_tones": [

                    {
                        "note": "B",
                        "cents": -50,
                    }
                ],

                "family": "hijaz",
            },

            "saba": {

                "root": "D",

                "quarter_tones": [

                    {
                        "note": "E",
                        "cents": -50,
                    }
                ],

                "family": "saba",
            },

            "kurd": {

                "root": "D",

                "quarter_tones": [],

                "family": "kurd",
            },

            "nahawand": {

                "root": "C",

                "quarter_tones": [],

                "family": "nahawand",
            },

            "ajam": {

                "root": "C",

                "quarter_tones": [],

                "family": "ajam",
            },
        }