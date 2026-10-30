diff --git a/custom_components/waste_collection_schedule/waste_collection_schedule/source/fcc_group_eu.py b/custom_components/waste_collection_schedule/waste_collection_schedule/source/fcc_group_eu.py
index 260e604..f25fcf4 100644
--- a/custom_components/waste_collection_schedule/waste_collection_schedule/source/fcc_group_eu.py
+++ b/custom_components/waste_collection_schedule/waste_collection_schedule/source/fcc_group_eu.py
@@ -10,7 +10,7 @@ from waste_collection_schedule.exceptions import (
 )
 
 TITLE = "fcc Environment"
-DESCRIPTION = "Source for fcc Environment."
+DESCRIPTION = "Source for fcc Environment (VYLOŽ SMETI / MŮJODPAD apps)."
 URL = "https://www.fcc-group.eu/"
 TEST_CASES = {
     "Cífer J. Kubányiho": {
@@ -19,19 +19,72 @@ TEST_CASES = {
     },
     "Borinka Weekly": {"city": "Borinka", "frequency": "weekly"},
     "Cerová Monthly": {"city": "Cerová", "frequency": "monthly"},
+    "CZ Hejnice (by location)": {
+        "country": "cz",
+        "city": "Hejnice",
+        "location": "SKO - svoz středa, BIO - pondělí lichý týden",
+    },
+    "CZ Hejnice st big": {"country": "cz", "city": "hejnice_st_big_fryd"},
+    "CZ Hejnice st small": {"country": "cz", "city": "hejnice_st_small_fryd"},
+    "CZ Hejnice st 4x4": {"country": "cz", "city": "hejnice_st_4x4_fryd"},
+    "CZ Hejnice ct big": {"country": "cz", "city": "hejnice_ct_big_fryd"},
 }
 
 COUNTRY = "sk"
 
-
-ICON_MAP = {
-    "Komunálny": Icons.GENERAL_WASTE,
-    "Plasty": Icons.PLASTIC_PACKAGING,
-    "Papier": Icons.PAPER,
-    "Separovaný": Icons.RECYCLING,
+EXTRA_INFO = [
+    {
+        "title": "fcc Environment (VYLOŽ SMETI)",
+        "url": "https://www.fcc-group.eu/",
+        "country": "sk",
+        "default_params": {"country": "sk"},
+    },
+    {
+        "title": "FCC Česká republika (MŮJODPAD)",
+        "url": "https://www.fcc-group.eu/",
+        "country": "cz",
+        "default_params": {"country": "cz"},
+    },
+]
+
+PARAM_TRANSLATIONS = {
+    "en": {
+        "country": "Country (sk or cz)",
+        "city": "City",
+        "location": "Location",
+        "frequency": "Frequency",
+    },
+    "de": {
+        "country": "Land (sk oder cz)",
+        "city": "Ort",
+        "location": "Standort",
+        "frequency": "Häufigkeit",
+    },
 }
 
 
+# Matched as lowercase substrings of the waste title (SK and CZ apps).
+ICON_KEYWORDS: list[tuple[str, str]] = [
+    ("komun", Icons.GENERAL_WASTE),
+    ("směsn", Icons.GENERAL_WASTE),
+    ("sko", Icons.GENERAL_WASTE),
+    ("plast", Icons.PLASTIC_PACKAGING),
+    ("papier", Icons.PAPER),
+    ("papír", Icons.PAPER),
+    ("bio", Icons.ORGANIC),
+    ("sklo", Icons.GLASS),
+    ("separ", Icons.RECYCLING),
+]
+
+
+def get_icon(waste_type: str) -> str | None:
+    lower = waste_type.lower()
+    for keyword, icon in ICON_KEYWORDS:
+        if keyword in lower:
+            return icon
+    return None
+
+
 class City(TypedDict):
     locationId: int
     city: str
@@ -61,7 +114,10 @@ class CollecctionEntry(TypedDict):
     isMonthly: bool
 
 
-API_URL = "https://vylozsmeti.kabernet.sk/api/public"
+API_URLS = {
+    "sk": "https://vylozsmeti.kabernet.sk/api/public",
+    "cz": "https://mujodpad.kabernet.sk/api/public",
+}
 
 
 def cmp(a: str, b: str) -> bool:  # type: ignore[attr-defined]
@@ -74,6 +130,9 @@ FREQUENCIES: list[FREQUENCIES_LITERAL] = ["weekly", "biweekly", "monthly"]
 DEFAULT_FREQUENCY_MAP: dict[str, FREQUENCIES_LITERAL] = {
     "dvojtýždenne": "biweekly",
     "týždenne": "weekly",
+    "dvoutýdně": "biweekly",
+    "1x za 14 dní": "biweekly",
+    "týdně": "weekly",
     "": "weekly",
 }
 
@@ -84,7 +143,14 @@ class Source:
         city: str,
         location: str | None = None,
         frequency: FREQUENCIES_LITERAL | None = None,
+        country: Literal["sk", "cz"] = "sk",
     ):
+        country = (country or "sk").lower()  # type: ignore[assignment]
+        if country not in API_URLS:
+            raise SourceArgumentNotFoundWithSuggestions(
+                "country", country, list(API_URLS)
+            )
+        self._api_url: str = API_URLS[country]
         self._city: str = city
         self._location: str | None = location
         self._frequency: FREQUENCIES_LITERAL | None = frequency
@@ -98,7 +164,7 @@ class Source:
         self._waste_dict: dict[int, str] | None = None
 
     def fetch_city(self) -> City:
-        r = requests.get(API_URL + "/location", params={"includeLocations": "True"})
+        r = requests.get(self._api_url + "/location", params={"includeLocations": "True"})
         r.raise_for_status()
         data: list[City] = r.json()
         matches = []
@@ -137,7 +203,7 @@ class Source:
 
     def fetch_options(self, location_id: int) -> OptionsResult:
         r = requests.get(
-            API_URL + "/schedule/options", params={"locationId": location_id}
+            self._api_url + "/schedule/options", params={"locationId": location_id}
         )
         r.raise_for_status()
         data: OptionsResult = r.json()
@@ -185,7 +251,7 @@ class Source:
 
     def fetch_schedule(self, location_id: int, year: int) -> list[CollecctionEntry]:
         r = requests.get(
-            API_URL + "/schedule", params={"locationId": location_id, "year": year}
+            self._api_url + "/schedule", params={"locationId": location_id, "year": year}
         )
         r.raise_for_status()
         return r.json()
@@ -241,6 +307,6 @@ class Source:
                 continue
             waste_type = self._waste_dict[entry["wasteId"]]
             date = parse(entry["date"]).date()
-            icon = ICON_MAP.get(waste_type.split()[0])
+            icon = get_icon(waste_type)
             entries.append(Collection(date=date, t=waste_type, icon=icon))
         return entries
