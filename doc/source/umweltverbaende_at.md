# Die NÖ Umweltverbände

Support for many of the schedules provided by [Die NÖ Umweltverbände](https://www.umweltverbaende.at/) for Lower Austria.

## Configuration Variables

```yaml
waste_collection_schedule:
  sources:
    - name: umweltverbaende_at
      args:
        district: DISTRICT_ARG
        municipal: MUNICIPAL
        town: TOWN
        plz: PLZ
        street: STREET
        hnr: HNR
        addition: ADDITION
        calendar: CALENDAR
        calendar_title_separator: CALENDAR_TITLE_SEPERATOR
        calendar_splitter: CALENDAR_SPLITTER
```

**district**  
*(string) (required)*

Lower Austrian district, see table below for valid DISTRICT_ARG


There are 2 kind of webistes supported. Service providers use one of them but not both.

### 1. New WordPress based websites.

This website has a blue header and only blue accenct colors. This one uses a lot more moder form for selection your address.

**municipal**
*(string) (optional)*

Not required for all districts. Only required if you need to select one on the Abholtermine page.

**town**
*(string) (optional)*

Not required for all districts. Only required if you need to select one on the Abholtermine page.

**plz**
*(string) (optional)*

Not required for all districts. Only required if you need to select one on the Abholtermine page.

**street**
*(string) (optional)*

Not required for all districts. Only required if you need to select one on the Abholtermine page.

**hnr**
*(string) (optional)*

Not required for all districts. Only required if you need to select one on the Abholtermine page.

**addition**
*(string) (optional)*

House number addition. Not required for all districts. Only required if you need to select one on the Abholtermine page.


### 2. Old websites

This website has a light blue header and uses green accent colors. The url contains something like `?kat=32` when you are not on the main page.

**muncipal**  
*(string) (optional)*

Municipal within the district for which the collection schedule is required. The municipal should be spelt as it appears on the Abholtermine page. There is no need to include the "Marktgemeinde", "Gemeinde", or "Stadtgeminde" text.

Is not needed for Stadt Krems you should provide a calendar for each Rayon.

*deprecated (still works for Stadt Krems)*:  
For Stadt Krems, the district is divided into 12 Rayon, so supply your Rayon name for the municipal arg. For example: _Rehberg (Rayon 30)_ would be `Rehberg`, whereas _Innenstadt 2 (Rayon 200)_ would be `Innenstadt 2`

**calendar**  
(string) (optional)

If you see multiple collection calendars for your municipal (different streets or Rayons), you can specify the calendar name here. The calendar name should be spelt as it appears on the Abholtermine page below `Kalenderansicht`.

**calendar_title_separator**  
(string) (optional | default: ":")

rarely needed, only works if `calendar` is set. This is the character that separates the calendar title from the collection dates. Like `Tour 1: Restmüll` (`:` is the separator which is the default value) or `Bisamberg Zone B, Restmüll 14-tägig` (`,` is the separator). You can see the text, the integration will use, at the Abholtermine page below `Kalenderansicht`

**calendar_splitter**  
(string) (optional)

rarely needed, only works if `calendar` is set. Only needed if multiple collections are shown in one line. This is the character that separates the collection times, that are listed in one line. Like `Bisamberg Zone B, Restmüll 14-tägig: Gelber Sack` (`:` is the separator) You can see the text, the integration will use, at the Abholtermine page below `Kalenderansicht`



## Examples


### New WordPress based websites

```yaml
waste_collection_schedule:
  sources:
    - name: umweltverbaende_at
      args:
        district: "gaenserndorf" # Gänserndorf
        municipal: "Marchegg" # Municipal

```

```yaml
waste_collection_schedule:
  sources:
    - name: umweltverbaende_at
      args:
        district: "waidhofen" # Waidhofen/Thaya
        municipal: "Kautzen" # Municipal
```

```yaml
waste_collection_schedule:
  sources:
    - name: umweltverbaende_at
      args:
        district: "hollabrunn" # Hollabrunn
        municipal: "Retz" # Municipal
        town: "Obernalb"
        street: "Zum weissen Engel"
```

```yaml
waaste_collection_schedule:
  sources:
    - name: umweltverbaende_at
      args:
        district: "krems" # Krems
        municipal: "Langenlois" # Municipal
        calendar: "Gobelsburg, Mittelberg, Reith, Schiltern, Zöbing" # Rayon
```

### Old websites

<!-- Example removed: Tulln no longer supported (no ICS/API available)
```yaml
waste_collection_schedule:
  sources:
    - name: umweltverbaende_at
      args:
        district: "tulln" # Tulln
        municipal: "Tulbing" # Municipal
        calendar: 
          - "Haushalte 2"
          - "Biotonne"
```
-->

*Advanced calendar options are needed*

```yaml
waste_collection_schedule:
  sources:
    - name: umweltverbaende_at
      args:
        district: "korneuburg" # Korneuburg
        municipal: "Bisamberg" # Municipal
        calendar: "Zone B" # Rayon
        calendar_title_separator: ","
        calendar_splitter: ":"
```

*Old Version*
```yaml
waste_collection_schedule:
  sources:
    - name: umweltverbaende_at
      args:
        district: "kermsstadt" # Stadt Krems
        municipal: "Rehberg" # Rayon
```


## DISTRICT_ARG Lookup

| Lower Austria District | DISTRICT_ARG | Municipalities/Rayons |
|-----|-----|-----|
| Bruck/Leitha | bruck | [link](https://bruck.umweltverbaende.at/?kat=32) |
| Baden | baden | [link](https://baden.umweltverbaende.at/?kat=32) |
| Gmünd | gmuend | [link](https://gmuend.umweltverbaende.at/?kat=32) |
| Gänserndorf | gaenserndorf | [link](https://gaenserndorf.umweltverbaende.at/?kat=32) |
| Hollabrunn | hollabrunn | [link](https://hollabrunn.umweltverbaende.at/?kat=32) |
| Horn | horn | [link](https://horn.umweltverbaende.at/?kat=32) |
| Klosterneuburg | klosterneuburg | [link](https://klosterneuburg.umweltverbaende.at/?kat=32) |
| Korneuburg | korneuburg | [link](https://korneuburg.umweltverbaende.at/?kat=32) |
| Krems | krems | [link](https://krems.umweltverbaende.at/?kat=32) |
| Stadt Krems | kremsstadt | [link](https://kremsstadt.umweltverbaende.at/?kat=32) |
| Lilienfeld | lilienfeld | [link](https://lilienfeld.umweltverbaende.at/?kat=32) |
| Mödling | moedling | [link](https://moedling.umweltverbaende.at/?kat=32) |
| Melk | melk | [link](https://melk.umweltverbaende.at/?kat=32) |
| Mistelbach | mistelbach | [link](https://mistelbach.umweltverbaende.at/?kat=32) |
| St. Pölten | stpoeltenland | [link](https://stpoeltenland.umweltverbaende.at/?kat=32) |
| Scheibbs | scheibbs | [link](https://scheibbs.umweltverbaende.at/?kat=32) |
| Schwechat | schwechat | [link](https://schwechat.umweltverbaende.at/?kat=32) |
| Waidhofen/Thaya | waidhofen | [link](https://waidhofen.umweltverbaende.at/?kat=32) |
| Zwettl | zwettl | [link](https://zwettl.umweltverbaende.at/?kat=32) |


## Missing Districts

Laa/Thaya, Neunkirchen, Tulln serve their waste collection scheduled from local municipality web sites using different back-ends and aren't supported by this script.

## Districts supported via generic ICS source
* [GDA Amstetten](/doc/ics/gda_gv_at.md)
* [Abfallwirtschaft der Stadt St. Pölten](/doc/ics/st-poelten_at.md)
