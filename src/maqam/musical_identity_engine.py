from typing import Any, Dict


class MusicalIdentityEngine:

    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.0"

    def _extract_tonic(self, tonic_data):

        return tonic_data.get("decision", {})

    def _extract_maqam(self, maqam_data):

        return maqam_data.get("decision", {})

    def _extract_jins(self, jins_data):

        return jins_data.get("decision", {})

    def analyze(
        self,
        tonic_data: Dict[str, Any],
        maqam_data: Dict[str, Any],
        jins_data: Dict[str, Any],
    ):

        tonic = self._extract_tonic(tonic_data)
        maqam = self._extract_maqam(maqam_data)
        jins = self._extract_jins(jins_data)

        tonic_decided = tonic.get("status") == "DECIDED"
        maqam_decided = maqam.get("status") == "DECIDED"
        jins_decided = jins.get("status") == "DECIDED"

        decided_count = sum(
            [
                tonic_decided,
                maqam_decided,
                jins_decided,
            ]
        )

        confidence_values = []

        for item in (tonic, maqam, jins):

            confidence = item.get("confidence")

            if isinstance(confidence, (int, float)):

                confidence_values.append(confidence)

        confidence = (
            sum(confidence_values) / len(confidence_values)
            if confidence_values
            else 0.0
        )

        if decided_count == 3:

            status = "DECIDED"

        elif decided_count > 0:

            status = "PARTIAL"

        else:

            status = "ABSTAIN"

        return {
            "version": self.VERSION,
            "feature_version": self.FEATURE_VERSION,
            "patch_version": self.PATCH_VERSION,
            "tonic": tonic,
            "maqam": maqam,
            "jins": jins,
            "musical_identity": {
                "status": status,
                "confidence": round(confidence, 6),
                "decided_components": decided_count,
                "total_components": 3,
            },
            "protection": {
                "tonic_modified": False,
                "maqam_modified": False,
                "jins_modified": False,
                "source_data_modified": False,
            },
        }