class ArabicMaqamDatabase:

    VERSION = "1.0.0"

    MAQAMS = {
        "bayati": {
            "primary_jins": "bayati",
            "microtones": True,
        },
        "hussaini": {
            "primary_jins": "hussaini",
            "microtones": True,
        },
        "sikah": {
            "primary_jins": "sikah",
            "microtones": True,
        },
        "huzam": {
            "primary_jins": "huzam",
            "microtones": True,
        },
        "rast": {
            "primary_jins": "rast",
            "microtones": True,
        },
        "hijaz": {
            "primary_jins": "hijaz",
            "microtones": True,
        },
        "saba": {
            "primary_jins": "saba",
            "microtones": True,
        },
        "nahawand": {
            "primary_jins": "nahawand",
            "microtones": False,
        },
        "kurd": {
            "primary_jins": "kurd",
            "microtones": False,
        },
        "ajam": {
            "primary_jins": "ajam",
            "microtones": False,
        },
    }

    def get_maqams(self):

        return list(
            self.MAQAMS.keys()
        )

    def get_details(
        self,
        maqam_name,
    ):

        return self.MAQAMS.get(
            maqam_name.lower()
        )

    def count(self):

        return len(
            self.MAQAMS
        )