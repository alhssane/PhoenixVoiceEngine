class ArabicJinsEngine:

    VERSION = "1.0.0"

    def get_ajnas(self):

        return {

            "rast_jins": {

                "root": "C",

                "intervals": [
                    0,
                    4,
                    7,
                    10,
                ],
            },

            "bayati_jins": {

                "root": "D",

                "intervals": [
                    0,
                    3,
                    7,
                    10,
                ],
            },

            "sikah_jins": {

                "root": "E",

                "intervals": [
                    0,
                    3,
                    6,
                    10,
                ],
            },

            "hijaz_jins": {

                "root": "D",

                "intervals": [
                    0,
                    1,
                    5,
                    7,
                ],
            },

            "saba_jins": {

                "root": "D",

                "intervals": [
                    0,
                    3,
                    6,
                    8,
                ],
            },
        }

    def get_jins_names(self):

        return list(

            self.get_ajnas().keys()

        )