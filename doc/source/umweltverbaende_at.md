# Die NÖ Umweltverbände

Support for many of the schedules provided by [Die NÖ Umweltverbände](https://www.umweltverbaende.at/) for Lower Austria.

## Configuration Variables

```yaml
waste_collection_schedule:
  sources:
    - name: umweltverbaende_at
      args:
        district: DISTRICT_ARG
        municipal: MUNICIPAL/RAYON
```

**district**  
*(string) (required)*

Lower Austrian district, see table below for valid DISTRICT_ARG

**muncipal**  
*(string) (required)*

Municipal within the district for which the collection schedule is required. The municipal should be spelt as it appears on the Abholtermine page. There is no need to include the "Marktgemeinde", "Gemeinde", or "Stadtgeminde" text.

For Stadt Krems, the district is divided into 12 Rayon, so supply your Rayon name for the municipal arg. For example: _Rehberg (Rayon 30)_ would be `Rehberg`, whereas _Innenstadt 2 (Rayon 200)_ would be `Innenstadt 2`


## Examples

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
| Tulln | tulln | [link](https://tulln.umweltverbaende.at/?kat=32) |
| Waidhofen/Thaya | waidhofen | [link](https://waidhofen.umweltverbaende.at/?kat=32) |
| Zwettl | zwettl | [link](https://zwettl.umweltverbaende.at/?kat=32) |


## Missing Districts

Amstetten, Laa/Thaya, Neunkirchen, Stadt St. Pölten and Wiener Neustadt serve their waste collection scheduled from local municipality web sites using different back-ends and aren't supported by this script.