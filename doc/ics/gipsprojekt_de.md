The city of Heidelberg retired the GIPS project the new source request is handeled in https://github.com/mampfes/hacs_waste_collection_schedule/issues/3248 See also the [press release](https://www.heidelberg.de/HD/Presse/25_06_2024++stadt+aktualisiert+den+online-abfallkalender_+alle+entsorgungstermine+auf+einen+blick.html)

Until this is resolved, you can configure the waste manually: 

1. GoTo https://abfallkalender.heidelberg.de/calendar and configure
2. Download "Digitaler Kalender" - should give you Abfallkalender.ics 
3. Place file here "/homeassistant/www/Abfallkalender.ics" (use File Editor addon) 
4. Configure, either yaml or GUI. Choose Germany, Heidelberg (ICS) and then use these settings: 
   - url: "http://localhost:8123/local/Abfallkalender.ics"
   - split_at: ","
