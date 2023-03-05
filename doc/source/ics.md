# ICS / iCal

Add support for schedules from ICS / iCal files. Files can be either stored in a  local folder or fetched from a static URL. The waste type will be taken from the `summary` attribute.

This source has been successfully tested with the following service providers:

### Belgium

- [Limburg.net](https://www.limburg.net/afvalkalender) ([Example](#limburgnet))

### Germany

- [FES Frankfurt](https://www.fes-frankfurt.de/) ([Notes](#fes-frankfurt))
- [Müllabfuhr-Deutschland](https://www.muellabfuhr-deutschland.de/) ([Notes](#müllabfuhr-deutschland))

#### Baden-Württemberg

- [Abfallwirtschaftsamt Bodenseekreis](https://www.bodenseekreis.de/umwelt-landnutzung/abfallentsorgung-privat/termine/abfuhrkalender/) ([Notes](#abfallwirtschaftsamt-bodenseekreis))
- [Abfallwirtschaft Kreis Böblingen](https://www.lrabb.de/start/Service+_+Verwaltung/Abfuhrtermine.html)
- [Abfall Landkreis Stade](https://abfall.landkreis-stade.de/)
- [AVL Ludwigsburg](https://www.avl-ludwigsburg.de/) ([Example](#avl-ludwigsburg))
- [AWB Esslingen](https://www.awb-es.de/)

#### Bayern

- [AWM München](https://www.awm-muenchen.de) ([Notes](#awm-münchen))
- [Awista Starnberg](https://www.awista-starnberg.de/)
- [Gemeinde Zorneding](https://www.zorneding.de/Wohnen-Leben/Abfall-Energie-Wasser/M%C3%BCllkalender/index.php) ([Notes](#gemeinde-zorneding))

#### Brandenburg

- [Entsorgungsbetrieb Märkisch-Oderland](https://www.entsorgungsbetrieb-mol.de/de/tourenplaene.html) ([Example](#entsorgungsbetrieb-märkisch-oderland))

#### Hessen

- [Erlensee](https://sperrmuell.erlensee.de/?type=reminder) ([Example](#erlensee))
- [EAW Rheingau Taunus](https://www.eaw-rheingau-taunus.de/service/abfallkalender.html) ([Example](#eaw-rheingau-taunus))

#### Niedersachsen

- [Abfallkalender Zollernalbkreis](https://www.zollernalbkreis.de/landratsamt/aemter++und+organisation/Elektronischer+Abfallkalender) ([Example](#abfallkalender-zollernalbkreis))
- [Abfallkalender Osnabrück](https://nachhaltig.osnabrueck.de/de/abfall/muellabfuhr/muellabfuhr-digital/online-abfuhrkalender/) ([Example](#abfallkalender-osnabrück))
- [ZAH Zweckverband Abfallwirtschaft Hildesheim](https://www.zah-hildesheim.de/termine/#Abfuhrplan) ([Example](#abfallkalender-hildesheim))

#### Nordrhein-Westfalen

- [EDG Entsorgung Dortmund](https://www.edg.de/)

#### Rheinland-Pfalz

- [Zweckverband Abfallwirtschaft A.R.T. Trier](https://www.art-trier.de)
- Landkreis Vulkaneifel

#### Sachsen

- [ASR Chemnitz](https://www.asr-chemnitz.de/kundenportal/entsorgungskalender/)
- [Stadtreinigung Leipzig](https://www.stadtreinigung-leipzig.de/)
- [Entsorgungsgesellschaft Görlitz-Löbau-Zittau](https://www.abfall-eglz.de/abfallkalender.0.html) ([Notes](#entsorgungsgesellschaft-görlitz-löbau-zittau))

#### Schleswig Holstein

- [Lübeck Entsorgungsbetriebe](https://insert-it.de/BMSAbfallkalenderLuebeck)

#### Thüringen

- [Abfallwirtschaftsbetrieb Ilm-Kreis](https://aik.ilm-kreis.de/) ([Notes](#abfallwirtschaftsbetrieb-ilm-kreis))

### Sweden

- [NSR Nordvästra Skåne](https://nsr.se/privat/allt-om-din-sophamtning/nar-toms-mitt-karl/tomningskalender/)

### United States of America

- [ReCollect.net](https://recollect.net) ([Notes](#recollect))
- [Western Disposal Residential (Colorado)](https://www.westerndisposal.com/residential/) (Unofficial, [Notes](#western-disposal-colorado))

### United Kingdom

- [South Cambridgeshire](https://www.scambs.gov.uk/recycling-and-bins/find-your-household-bin-collection-day/) ([Notes](#south-cambridgeshire))
- [London Borough of Bromley](https://recyclingservices.bromley.gov.uk/waste) (Unofficial)

***

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: URL
        file: FILE
        offset: OFFSET
        method: METHOD
        params: PARAMS
        year_field: YEAR_FIELD
        regex: REGEX
        split_at: SPLIT_AT
        version: 2
        verify_ssl: VERIFY_SSL
        headers: HEADERS
```

### Configuration Variables

**url**  
*(string) (optional)*

URL to ICS / iCal file. File will be downloaded using a HTTP GET request.

If the original url contains the current year (4 digits including century), this can be replaced by the wildcard `{%Y}` (see example below).

You have to specify either `url` or `file`!

**file**  
*(string) (optional)*

Local ICS / iCal file name. Can be used instead of `url` for local files.

You have to specify either `url` or `file`!

Notes:

- Some users have reported that on their installation, only local files below the folder `config/www` are accessible by the system. Therefore place the ics file there.
- If you are using relative paths (like in the example below), the path depends on which working directory your Home Assistant instance is running on. And this might depend on the installation method (core vs supervisor vs OS vs ...). Therefore check the log output, it tells you the current working directory.

  This example should work for HAOS based installations:

  ```yaml
  # file location: config/www/calendar.ics
  waste_collection_schedule:
    sources:
      - name: ics
        args:
          file: "www/calendar.ics"
  ```

**offset**  
*(int) (optional, default: `0`)*

Offset in days which will be added to every start time. Can be used if the start time of the events in the ICS file are ahead of the actual date.

**method**  
*(string) (optional, default: `GET`)*

Method to send the URL `params`.

Need to be `GET` or `POST`.

**params**  
*(dict) (optional, default: None)*

Dictionary, list of tuples or bytes to send in the query string for the HTTP request.

This gets

- urlencoded and either attached to the raw URL when GET method is used.
- send with `Content-Type: application/x-www-form-urlencoded` and an automatically generated `Content-Length` header as POST method HTTP body.

Only used if `url` is specified, not used for `file`.

**year_field**  
*(string) (optional, default: None)*

Field in params dictionary to be replaced with current year (4 digits including century).

**regex**  
*(string) (optional, default: None)*

Regular expression used to remove needless text from collection types.

See also example below.

**split_at**  
*(string) (optional, default: None)*

Delimiter to split event summary into individual collection types. If your service puts multiple collections types which occur at the same day into a single event, this option can be used to separate the collection types again.

**version**  
*(integer) (optional, default: 2)*

Selects the underlying ICS file parser:

- version: 1 uses `recurring_ical_events`
- version: 2 uses `icalevents`

**verify_ssl**  
*(boolean) (optional, default: True)*

Allows do disable SSL certificate checks in case the HTTPS server of your service provider is misconfigured and therefore doesn't send intermediate certificates. Unlike browsers, python doesn't support automatic fetching of missing intermediates.

Set this option to `False` if you see the following warning in the logs:

`[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate`.

**headers**  
*(dict) (optional, default: empty dict)*

Add custom headers to HTTP request, e.g. `referer`. By default, the `user-agent` is already set to `Mozilla/5.0 (Windows NT 10.0; Win64; x64)`.

See also [example](#custom-headers) below.

## Examples and Notes

***

### Local file

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        file: "test.ics"
```

***

### Custom Headers

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: "https://abc.com"
        headers:
          referer: special-referer
```

***

### A.R.T. Trier - Zweckverband Abfallwirtschaft

#### Landkreis Vulkaneifel

Go to the website: [art-trier.de](https://www.art-trier.de/eo/cms?_bereich=artikel&_aktion=suche_rubrik&idrubrik=1003&_sortierung=info3_asc_info4_asc&info1=54578&info2=)

select your Postal code.

Select your reminder to:
Wann möchten Sie erinnert werden?        Am Abfuhrtag
Um wie viel Uhr möchten Sie erinnert werden?     06:00 Uhr

Select the Button: Kalender (ICS) Importieren.
Window opens with the .ics link like this:
webcal://abfallkalender.art-trier.de/ics-feed/"Postleitzahl"_"Ort"_"Erinnerungstag-hier_0"_"Erinnerungs_Uhrzeit-hier_0600"

webcal://abfallkalender.art-trier.de/ics-feed/54578_basberg_0-1800.ics

Remove the beginning webcal and set instead a https!

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.art-trier.de/ics-feed/54578_basberg_0-0600.ics

sensor:
  - platform: waste_collection_schedule
    name: restmuell
    details_format: upcoming
    count: 4
    value_template: '{{value.types|join(" + ")}} in {{value.daysTo}} Tag(en)'
    date_template: '{{value.date.strftime("%d.%m.%Y")}}'
    types:
      - 'A.R.T. Abfuhrtermin: Restmüll'

  - platform: waste_collection_schedule
    name: altpapier
    details_format: upcoming
    count: 4
    value_template: '{{value.types|join(" + ")}} in {{value.daysTo}} Tag(en)'
    date_template: '{{value.date.strftime("%d.%m.%Y")}}'
    types:
      - 'A.R.T. Abfuhrtermin: Altpapier'

  - platform: waste_collection_schedule
    name: gelber_sack
    details_format: upcoming
    count: 4
    value_template: '{{value.types|join(" + ")}} in {{value.daysTo}} Tag(en)'
    date_template: '{{value.date.strftime("%d.%m.%Y")}}'
    types:
      - 'A.R.T. Abfuhrtermin: Gelber Sack'

  - platform: waste_collection_schedule
    name: tonnenbutton
    count: 4
    value_template: '{{value.types|join(", ")}}|{{value.daysTo}}|{{value.date.strftime("%d.%m.%Y")}}|{{value.date.strftime("%a")}}'  
```

### Landkreis Trier-Saarburg

Landkreis Trier-Saarburg has Gelber Sack and Altpapier combined, which causes the above for Landkreis Vulkaneifel to fail to parse the .ics file.

The following will parse the .ics file properly:

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://abfallkalender.art-trier.de/ics-feed/54311_trierweiler_0-0600.ics
sensor:
  - platform: waste_collection_schedule
    name: restmuell
    details_format: upcoming
    count: 4
    value_template: '{{value.types|join(" + ")}} in {{value.daysTo}} Tag(en)'
    date_template: '{{value.date.strftime("%d.%m.%Y")}}'
    types:
      - 'A.R.T. Abfuhrtermin: Restmüll'
  - platform: waste_collection_schedule
    name: altpapier
    details_format: upcoming
    count: 4
    value_template: '{{value.types|join(" + ")}} in {{value.daysTo}} Tag(en)'
    date_template: '{{value.date.strftime("%d.%m.%Y")}}'
    types:
      - 'A.R.T. Abfuhrtermin: Altpapier & Gelber Sack'
  - platform: waste_collection_schedule
    name: tonnenbutton
    count: 4
    value_template: '{{value.types|join(", ")}}|{{value.daysTo}}|{{value.date.strftime("%d.%m.%Y")}}|{{value.date.strftime("%a")}}'  
```

***

### AVL Ludwigsburg

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: "https://kundenportal.avl-lb.de/WasteManagementLudwigsburg/WasteManagementServiceServlet?ApplicationName=Calendar&SubmitAction=sync&StandortID=950230001&AboID=8188&Fra=BT;RT;PT;LT;GT"
        offset: 0
```

***

### Abfallwirtschaftsamt Bodenseekreis

Go to the [service provider website](https://www.bodenseekreis.de/umwelt-landnutzung/abfallentsorgung-privat/termine/abfuhrkalender/) and select location and desired waste types. Afterwards an iCal calendar export is provided. Simply take this URL and replace the year with "{%Y}" and use this URL within the configuration.

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.bodenseekreis.de/umwelt-landnutzung/abfallentsorgung-privat/termine/abfuhrkalender/export/{%Y}/salem/salem-i/1,4,5,16,7,8,10,6/ics/
      customize:
        - type: Restmüll 2-wöchentlich
          alias: Restmüll
          icon: mdi:trash-can
        - type: Bioabfall 2-wöchentlich
          alias: Bioabfall
          icon: mdi:flower-outline
        - type: Papier 4-wöchentlich
          alias: Papierabfall
          icon: mdi:trash-can-outline
        - type: Gelber Sack
          icon: mdi:recycle
```

***

### Gemeinde Zorneding

Go to the [service provider website](https://www.zorneding.de/Wohnen-Leben/Abfall-Energie-Wasser/M%C3%BCllkalender/index.php) and select location and desired waste types. Afterwards an iCal calendar export is provided. Simply click on download and visit the Download URL afterwards. Simply take this URL and use this URL within the configuration.

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.zorneding.de/output/options.php?ModID=48&call=ical&&pois=3094.81&alarm=13
      customize:
        - type: Restabfall
          alias: Restmüll
          icon: mdi:trash-can
        - type: BIO
          alias: Bioabfall
          icon: mdi:flower-outline
        - type: Altpapier
          alias: Papierabfall
          icon: mdi:trash-can-outline
        - type: Gelber Sack
          icon: mdi:recycle

sensor:
  - platform: waste_collection_schedule
    name: Restmüll
    details_format: upcoming
    count: 4
    value_template: '{% if value.daysTo == 0 %}Heute{% elif value.daysTo == 1 %}Morgen{% else %}in {{value.daysTo}} Tagen{% endif %}'
    date_template: '{{value.date.strftime("%d.%m.%Y")}}'
    types:
      - 'Restabfall'
      - 'Restmüll'

  - platform: waste_collection_schedule
    name: Altpapier
    details_format: upcoming
    count: 4
    value_template: '{% if value.daysTo == 0 %}Heute{% elif value.daysTo == 1 %}Morgen{% else %}in {{value.daysTo}} Tagen{% endif %}'
    date_template: '{{value.date.strftime("%d.%m.%Y")}}'
    types:
      - 'Altpapier'
      - 'Papierabfall'

  - platform: waste_collection_schedule
    name: Gelber_Sack
    details_format: upcoming
    count: 4
    value_template: '{% if value.daysTo == 0 %}Heute{% elif value.daysTo == 1 %}Morgen{% else %}in {{value.daysTo}} Tagen{% endif %}'
    date_template: '{{value.date.strftime("%d.%m.%Y")}}'
    types:
      - 'Gelber Sack'

  - platform: waste_collection_schedule
    name: Bioabfall
    details_format: upcoming
    count: 4
    value_template: '{% if value.daysTo == 0 %}Heute{% elif value.daysTo == 1 %}Morgen{% else %}in {{value.daysTo}} Tagen{% endif %}'
    date_template: '{{value.date.strftime("%d.%m.%Y")}}'
    types:
      - 'BIO'
      - 'Bioabfall'
```

***

### Abfallkalender Zollernalbkreis

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: "https://www.abfallkalender-zak.de",
        params:
            city: 2,3,4
            street: 3
            types[]:
              - restmuell
                gelbersack
                papiertonne
                biomuell
                gruenabfall
                schadstoffsammlung
                altpapiersammlung
                schrottsammlung
                weihnachtsbaeume
                elektrosammlung
            go_ics: Download
        year_field: year
```

***

### Abfallkalender Osnabrück

```yaml
# include in configuration.yaml
waste_collection_schedule:
   sources:
     - name: ics
       args:
         # go to https://nachhaltig.osnabrueck.de/de/abfall/muellabfuhr/muellabfuhr-digital/online-abfuhrkalender/ and search you correct destrict
         url: "https://geo.osnabrueck.de/osb-service/abfuhrkalender/?bezirk=10"
         offset: 0
       customize:
         - type: OSB Biomüll
           alias: Biomüll
           icon: mdi:flower-outline
         - type: OSB Gelber Sack
           alias: GelberSack
           icon: mdi:recycle
         - type: OSB Restmüll
           alias: Restmüll
           icon: mdi:trash-can
         - type: OSB Altpapier
           alias: Altpapier
           icon: mdi:trash-can-outline
   fetch_time: "04:23"
   day_switch_time: "09:30"

# include in sensors.yaml
- platform: waste_collection_schedule
  name: AbfallRestmuell
  details_format: "upcoming"
  value_template: '{% if value.daysTo == 0 %}Heute{% elif value.daysTo == 1 %}Morgen{% else %}in {{value.daysTo}} Tagen{% endif %}'
  types:
    - Restmüll
- platform: waste_collection_schedule
  name: AbfallPapierTonne
  details_format: "upcoming"
  value_template: '{% if value.daysTo == 0 %}Heute{% elif value.daysTo == 1 %}Morgen{% else %}in {{value.daysTo}} Tagen{% endif %}'
  types:
    - Altpapier
- platform: waste_collection_schedule
  name: AbfallGelberSack
  details_format: "upcoming"
  value_template: '{% if value.daysTo == 0 %}Heute{% elif value.daysTo == 1 %}Morgen{% else %}in {{value.daysTo}} Tagen{% endif %}'
  types:
    - GelberSack
- platform: waste_collection_schedule
  name: AbfallBiotonne
  details_format: "upcoming"
  value_template: '{% if value.daysTo == 0 %}Heute{% elif value.daysTo == 1 %}Morgen{% else %}in {{value.daysTo}} Tagen{% endif %}'
  types:
    - Biomüll
- platform: waste_collection_schedule
  name: AbfallRestmuellnext
  details_format: "upcoming"
  value_template: 'am: {{value.date.strftime("%d.%m.%Y")}}'
  types:
    - Restmüll
- platform: waste_collection_schedule
  name: AbfallPapierTonnenext
  details_format: "upcoming"
  value_template: 'am: {{value.date.strftime("%d.%m.%Y")}}'
  types:
    - Altpapier
- platform: waste_collection_schedule
  name: AbfallGelberSacknext
  details_format: "upcoming"
  value_template: 'am: {{value.date.strftime("%d.%m.%Y")}}'
  types:
    - GelberSack
- platform: waste_collection_schedule
  name: AbfallBiotonnenext
  details_format: "upcoming"
  value_template: 'am: {{value.date.strftime("%d.%m.%Y")}}'
  types:
    - Biomüll
- platform: waste_collection_schedule
  name: AbfallNaechster
  details_format: "upcoming"
  value_template: ' {{ value.daysTo }} '
```

***

### Abfallkalender Hildesheim

Go to the website: [ZAH Hildesheim](https://www.zah-hildesheim.de/termine/#Abfuhrplan)

Push the button "Inhalt laden" to load the content of hildesheim.abfuhrkalender.de.

Step 1: Select your town.  
Step 2: Select yout district.  
Step 3: Select your street.  

In the next step the calendar for the current year is displayed. Right-Click on "Export Kalender" and copy the URL of the calendar. The URL should look like this

https://hildesheim.abfuhrkalender.de/ICalendar/Index.aspx?year=2023&streetID=9999

The streetID (9999 is only an example) represents your address. Replace the the Year with {%Y} and use the URL within the configuration.

```yaml
# include in configuration.yaml
waste_collection_schedule:
  sources:
    - name: ics
      calendar_title: Abfallkalender Hildesheim
      args:
        url: "https://hildesheim.abfuhrkalender.de/ICalendar/Index.aspx?year={%Y}&streetID=9999"
      customize:
        - type: 'Abfuhr Altpapier'
          alias: 'Altpapier'
          icon: mdi:package-variant
        - type: 'Abfuhr Altpapier (verschoben)'
          alias: 'Altpapier (verschoben)'
          icon: mdi:package-variant
        - type: 'Abfuhr Biomüll'
          alias: 'Biomüll'
          icon: mdi:bio
        - type: 'Abfuhr Biomüll (verschoben)'
          alias: 'Biomüll (verschoben)'
          icon: mdi:bio
        - type: 'Abfuhr Gelbe Tonne'
          alias: 'Gelbe Tonne'
          icon: mdi:recycle
        - type: 'Abfuhr Gelbe Tonne (verschoben)'
          alias: 'Gelbe Tonne (verschoben)'
          icon: mdi:recycle
        - type: 'Abfuhr Restmüll (14tägige Abfuhr)'
          alias: 'Restmüll 2-wöchig'
          icon: mdi:trash-can-outline
        - type: 'Abfuhr Restmüll (14tägige Abfuhr) (verschoben)'
          alias: 'Restmüll 2-wöchig (verschoben)'
          icon: mdi:trash-can-outline
        - type: 'Abfuhr Restmüll (14tägige und vierwöchentliche Abfuhr'
          alias: 'Restmüll 2-/4-wöchig'
          icon: mdi:trash-can-outline
        - type: 'Abfuhr Restmüll (14tägige und vierwöchentliche Abfuhr (verschoben)'
          alias: 'Restmüll 2-/4-wöchig (verschoben)'
          icon: mdi:trash-can-outline
```
```yaml
# include in sensors.yaml
- platform: waste_collection_schedule
  name: Abfall_Altpapier
  details_format: upcoming
  count: 4
  value_template: '{% if value.daysTo == 0 %}Heute{% elif value.daysTo == 1 %}Morgen{% else %}in {{value.daysTo}} Tagen (am {{value.date.strftime("%d.%m.%Y")}}){% endif %}' 
  date_template: '{{value.date.strftime("%d.%m.%Y")}}'
  types: 
    - 'Altpapier'
    - 'Altpapier (verschoben)'

- platform: waste_collection_schedule
  name: Abfall_Biomuell
  details_format: upcoming
  count: 4
  value_template: '{% if value.daysTo == 0 %}Heute{% elif value.daysTo == 1 %}Morgen{% else %}in {{value.daysTo}} Tagen (am {{value.date.strftime("%d.%m.%Y")}}){% endif %}'
  date_template: '{{value.date.strftime("%d.%m.%Y")}}'
  types: 
    - 'Biomüll'
    - 'Biomüll (verschoben)'

- platform: waste_collection_schedule
  name: Abfall_GelbeTonne
  details_format: upcoming
  count: 4
  value_template: '{% if value.daysTo == 0 %}Heute{% elif value.daysTo == 1 %}Morgen{% else %}in {{value.daysTo}} Tagen (am {{value.date.strftime("%d.%m.%Y")}}){% endif %}'
  date_template: '{{value.date.strftime("%d.%m.%Y")}}'
  types: 
    - 'Gelbe Tonne'
    - 'Gelbe Tonne (verschoben)'

- platform: waste_collection_schedule
  name: Abfall_Restmuell_2W
  details_format: upcoming
  count: 4
  value_template: '{% if value.daysTo == 0 %}Heute{% elif value.daysTo == 1 %}Morgen{% else %}in {{value.daysTo}} Tagen (am {{value.date.strftime("%d.%m.%Y")}}){% endif %}'
  date_template: '{{value.date.strftime("%d.%m.%Y")}}'
  types: 
    - 'Restmüll 2-wöchig'
    - 'Restmüll 2-wöchig (verschoben)'

- platform: waste_collection_schedule
  name: Abfall_Restmuell_2u4W
  details_format: upcoming
  count: 4
  value_template: '{% if value.daysTo == 0 %}Heute{% elif value.daysTo == 1 %}Morgen{% else %}in {{value.daysTo}} Tagen (am {{value.date.strftime("%d.%m.%Y")}}){% endif %}'
  date_template: '{{value.date.strftime("%d.%m.%Y")}}'
  types: 
    - 'Restmüll 2-/4-wöchig'
    - 'Restmüll 2-/4-wöchig (verschoben)'

- platform: waste_collection_schedule
  name: Abfall_Benachrichtigung
  details_format: upcoming
  count: 4
  value_template: '{% if value.daysTo == 0 %}Heute{% elif value.daysTo == 1 %}Morgen{% else %}in {{value.daysTo}} Tagen (am {{value.date.strftime("%d.%m.%Y")}}){% endif %}'
  date_template: '{{value.date.strftime("%d.%m.%Y")}}'

- platform: waste_collection_schedule
  name: Abfall_Benachrichtigung_Typ
  details_format: upcoming
  count: 4
  value_template: '{{value.types|join(", ")}}'
  date_template: '{{value.date.strftime("%d.%m.%Y")}}'
```

***

### EAW Rheingau Taunus

1. Find your ICS link via the <eaw_rheingau-taunus.de> web page
2. Remove the cHash attribute

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: "https://www.eaw-rheingau-taunus.de/abfallsammlung/abfuhrtermine/feed.ics?tx_vierwdeaw_garbagecalendarics%5Baction%5D=ics&tx_vierwdeaw_garbagecalendarics%5Bcontroller%5D=GarbageCalendar&tx_vierwdeaw_garbagecalendarics%5Bstreet%5D=38"
        split_at: ","
```

***

### ReCollect

To get the URL, search your address in the recollect form of your home town, click "Get a calendar", then "Add to iCal". Finally, the URL under "Subscribe to calendar" is your ICS calendar link:

```url
webcal://recollect.a.ssl.fastly.net/api/places/BCCDF30E-578B-11E4-AD38-5839C200407A/services/208/events.en.ics?client_id=6FBD18FE-167B-11EC-992A-C843A7F05606
```

Strip the client ID and change the protocol to https, and you have a valid ICS URL.

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: "https://recollect.a.ssl.fastly.net/api/places/BCCDF30E-578B-11E4-AD38-5839C200407A/services/208/events.en.ics"
        split_at: "\\, [and ]*"
```

***

### Entsorgungsgesellschaft Görlitz-Löbau-Zittau

Remove the year from the generated URL to always get the current year.

***

### Lübeck Entsorgungsbetriebe

Go to the [service provider website](https://insert-it.de/BMSAbfallkalenderLuebeck) and select location. Right click iCalendar and copy link address. Simply insert this URL  and replace the current year with {%Y}.

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      calendar_title: Müllabfuhr-Lübeck
      args:
        url: "https://insert-it.de/BMSAbfallkalenderLuebeck/Main/Calender?bmsLocationId=XXXXX&year={%Y}"
#          ^^^Paste your URL under here^^^                                        ^^^Replace Year with {%Y} ^^^
      customize:
        - type: 'Leerung: PPK'
          alias: Papiermüll
        - type: "Leerung: Bioabfall"
          alias: Biomüll
        - type: 'Leerung: Restabfall'
          alias: Restmüll

sensor:
- platform: waste_collection_schedule
  name: "Papiermüll"
  details_format: appointment_types
  types: 
    - Papiermüll

- platform: waste_collection_schedule
  name: "Biomüll"
  details_format: appointment_types
  types: 
    - Biomüll

- platform: waste_collection_schedule
  name: "Restmüll"
  details_format: appointment_types
  types: 
    - Restmüll
```

***

### Müllabfuhr-Deutschland

You need to find the direct ics export link for your region, e.g. [Weimarer Land, Bad Berka](https://portal.muellabfuhr-deutschland.de/api-portal/mandators/194/cal/location/c0edd112-7b48-4b84-b2ed-314ca741c774/pickups/ics?year=2022&fractionIds=194003&fractionIds=194001&fractionIds=194002&appointmentStart=0600&appointmentEnd=0700&reminderMinutes=20).

Known districts:

- [Landkreis Hildburghausen](https://portal.muellabfuhr-deutschland.de/hildburghausen)
- [Landkreis Wittenberg](https://portal.muellabfuhr-deutschland.de/wittenberg)
- [Burgenlandkreis](https://portal.muellabfuhr-deutschland.de/burgenlandkreis)
- [Dessau-Rosslau](https://portal.muellabfuhr-deutschland.de/dessau-rosslau)
- [Weimarer Land](https://portal.muellabfuhr-deutschland.de/weimarer-land)
- [Landkreis Sömmerda](https://portal.muellabfuhr-deutschland.de/soemmerda)
- [Saalekreis](https://portal.muellabfuhr-deutschland.de/saalekreis)

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://portal.muellabfuhr-deutschland.de/api-portal/mandators/194/cal/location/c0edd112-7b48-4b84-b2ed-314ca741c774/pickups/ics?fractionIds=12004&fractionIds=12006&fractionIds=12001&fractionIds=12003&fractionIds=12002&year={%Y}
      calendar_title: Abfallwirtschaft Weimarer Land
      customize:
        - type: "Biotonne (Bad Berka)"
          alias: "Biotonne"
```

***

### AWM München

1. Find your ICS export link via the AWM web page
2. Remove the cHash attribute
3. Replace current year with `{%Y}`

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: "https://www.awm-muenchen.de/entsorgen/abfuhrkalender?tx_awmabfuhrkalender_abfuhrkalender%5Bhausnummer%5D=2&tx_awmabfuhrkalender_abfuhrkalender%5Bleerungszyklus%5D%5BB%5D=1%2F2%3BG&tx_awmabfuhrkalender_abfuhrkalender%5Bleerungszyklus%5D%5BP%5D=1%2F2%3BU&tx_awmabfuhrkalender_abfuhrkalender%5Bleerungszyklus%5D%5BR%5D=001%3BG&tx_awmabfuhrkalender_abfuhrkalender%5Bsection%5D=ics&tx_awmabfuhrkalender_abfuhrkalender%5Bsinglestandplatz%5D=false&tx_awmabfuhrkalender_abfuhrkalender%5Bstandplatzwahl%5D=true&tx_awmabfuhrkalender_abfuhrkalender%5Bstellplatz%5D%5Bbio%5D=70114566&tx_awmabfuhrkalender_abfuhrkalender%5Bstellplatz%5D%5Bpapier%5D=70114566&tx_awmabfuhrkalender_abfuhrkalender%5Bstellplatz%5D%5Brestmuell%5D=70114566&tx_awmabfuhrkalender_abfuhrkalender%5Bstrasse%5D=Freimanner%20Bahnhofstr.&tx_awmabfuhrkalender_abfuhrkalender%5Byear%5D={%Y}}"
        version: 1
```

***

### Erlensee

Just replace the street number (8 in the example below) with the number of your street. You can find the right number if you inspect the street drop-down list [here](https://sperrmuell.erlensee.de/?type=reminder).

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: "https://sperrmuell.erlensee.de/?type=reminder"
        method: POST
        params:
          street: 8
          eventType[]:
            - 27
            - 23
            - 19
            - 20
            - 21
            - 24
            - 22
            - 25
            - 26
          timeframe: 23
          download: ical
```

***

### Entsorgungsbetrieb Märkisch-Oderland

Go [here](https://www.entsorgungsbetrieb-mol.de/de/tourenplaene.html), enter your address and select the collection types you want to include. Then click the "Exportieren" link and copy the url. Replace the year with `{%Y}`.

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://mol.wastebox.gemos-management.de/Gemos/WasteBox/Frontend/TourSchedule/Raw/Name/{%Y}/List/123456/2664,2665,2666,2668,2669,2670,2671/Print/ics/Default/Abfuhrtermine.ics
        version: 2
      calendar_title: "Müllabfuhr"
      customize:
        - type: Hausmüllbehälter
          alias: Restmüll
          icon: mdi:trash-can
        - type: Gelber Sack
          icon: mdi:recycle-variant
        - type: Papiertonne
          icon: mdi:package-variant
        - type: Papiercontainer
          icon: mdi:package-variant
        - type: Biotonne
          icon: mdi:leaf
        - type: Grünabfall
          icon: mdi:forest
        - type: Schadstoffmobil
          icon: mdi:bottle-tonic-skull
        - type: Weihnachtsbaum
          icon: mdi:pine-tree
```

***

### Limburg.net

This tool works for all municipalities of the province of Limburg and the municipality of Diest.

Find your ICS export link via the calendar page - enter your address so that the system can look up the necessary data for your city and street to construct the URL.

Generating the URL on the site of Limburg.net is the simplest.

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://limburg.net/api-proxy/public/kalender-download/ical/72030?straatNummer=66536&huisNummer=1&toevoeging=&includeAllEventTypes=1&eventTypes[]=14&eventTypes[]=22&eventTypes[]=23&eventTypes[]=26&eventTypes[]=27&eventTypes[]=29
```

You can also compose the URL yourself. You need the following elements for this:

1. the nis-code of your municipality: query the api with the name of your municipality;  example: <https://limburg.net/api-proxy/public/afval-kalender/gemeenten/search?query=Peer>

    ```json
    [{"nisCode":"72030","naam":"Peer"}]
    ```

2. the number of your street: query the api with the nis-code of your municipality and the name of your street  
example: <https://limburg.net/api-proxy/public/afval-kalender/gemeente/72030/straten/search?query=Zuidervest>

    ```json
    [{"nummer":"66536","naam":"Zuidervest"}]
    ```

3. your housenumber

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: "https://limburg.net/api-proxy/public/kalender-download/ical/72030"
        method: GET
        params:
          straatNummer: 66536
          huisNummer: 1
          includeAllEventTypes: 1
          eventTypes[]:
            - 14
            - 22
            - 23
            - 26
            - 27
            - 29
```

***

### Western Disposal Colorado

*Unofficial calendar* maintained by burkemw3@gmail.com

[online calendar view](https://calendar.google.com/calendar/embed?src=gn2i5lqgobo5deb6p7j69l9aq8%40group.calendar.google.com&ctz=America%2FDenver)

```yaml
sensor:
  - platform: waste_collection_schedule
    name: Trash Recycling # whatever you want the UI to show. Consider adding a similar prefix for both sensors so they get sorted together, "Trash" in this case
    types:
      - Recycling # matches alias in waste_collection_schedule below
  - platform: waste_collection_schedule
    name: Trash Compost
    types:
      - Compost

waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://calendar.google.com/calendar/ical/gn2i5lqgobo5deb6p7j69l9aq8%40group.calendar.google.com/public/basic.ics
      customize:
        - type: Wednesday E Compost # from calendar event name
          alias: Compost # matches type in sensor configuration above
        - type: Wednesday E Recycling
          alias: Recycling
```

***

### South Cambridgeshire

To use this you need to idenfify your Unique Property Reference Number (UPRN). There are a couple of ways of doing this:

1. The easiest way to discover your UPRN is by using https://www.findmyaddress.co.uk/ and entering in your address details.

   Or

2. By looking at the URLs generated by the South Cambs web site:

   1. Go to [South Cambs Bin Collections](https://www.scambs.gov.uk/recycling-and-bins/find-your-household-bin-collection-day/)
   2. Enter your post code, then select your address from the dropdown. The results page will show your collection schedule.
   3. Your UPRN is the collection of digits at the end of the URL, for example: *scambs.gov.uk/recycling-and-bins/find-your-household-bin-collection-day/#id=`10008079869`*
   4. The iCal collection schedule can then be obtained using: *refusecalendarapi.azurewebsites.net/calendar/ical/`10008079869`*

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://refusecalendarapi.azurewebsites.net/calendar/ical/10008079869
        version: 2

sensor:
  - platform: waste_collection_schedule
    source_index: 0
    name: SouthCambsBins  # Change this to whatever you want the UI to display
    details_format: appointment_types
    date_template: '{{value.date.strftime("%A %d %B %Y")}}'  # date format becomes 'Tuesday 1 April 2022'
```

***

### London Borough of Bromley

The Bromley council has a simple way to generate an iCal. All you need is the URL

- Go to [Bromley Bin Collection](https://recyclingservices.bromley.gov.uk/waste)
- Enter your post code, then select your address from the dropdown. The results page will show your collection schedule.
- Your unique code can be found in the URL, eg: *recyclingservices.bromley.gov.uk/waste/`6261994`*
- You can either use the following link and replace your ID, or copy the link address on the "Add to you calendar" link: <https://recyclingservices.bromley.gov.uk/waste/6261994/calendar.ics>

Note:

- This has been designed to break each bin collection into different sensors.
- This was created at a property that has a garden waste subscription. You may need to amit that from the code
- This display number of days until collection. Replace `value_template` with `date_template: '{{value.date.strftime("%A %d %B %Y")}}'` to display date of collection

```yaml
#Waste Collection - London Borough of Bromley

waste_collection_schedule:
  sources:
    - name: ics
      customize:
        - type: Food Waste collection
          alias: Food Waste
        - type: Garden Waste collection
          alias: Garden Waste
        - type: Mixed Recycling (Cans, Plastics & Glass) collection
          alias: Mixed Recycling
        - type: Non-Recyclable Refuse collection
          alias: General Waste
        - type: Paper & Cardboard collection
          alias: Cardboard
      args:
        url: YOUR_URL
        version: 2
  ```

***

### Regular Expression

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        file: waste.ics
        regex: "Abfuhr: (.*)"
```

Removes the needless prefix "Abfuhr: " from the waste collection type.

***

### FES Frankfurt

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.fes-frankfurt.de/abfallkalender/<your-id>.ics
        split_at: " \/ "
        regex: "(.*)\\s+\\|"
```

***

### Abfallwirtschaftsbetrieb Ilm-Kreis

Go to the [service provider website](https://aik.ilm-kreis.de/Abfuhrtermine/) and select location and street. Selection of desired waste types is optional. Afterwards an iCal calendar export is provided. Download it and find the download URL. Some parameters of the URL can be ommited. (e.g. `kat`, `ArtID`, `alarm`)

Important: The base url of the provider's website `https://aik.ilm-kreis.de` needs to be set as a [custom header](#custom-headers) `referer`. Otherwise you'll get an HTTP 403 error.

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: "https://aik.ilm-kreis.de/output/options.php?ModID=48&call=ical&=&ArtID[0]=1.1&ArtID[1]=1.4&ArtID[2]=1.2&pois=3053.562&kat=1,&alarm=0"
        headers:
          referer: "https://aik.ilm-kreis.de"
      calendar_title: Abfuhrtermine Witzleben
```
