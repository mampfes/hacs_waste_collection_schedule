# Abfallwirtschaft Zollernalbkreis

Support for schedules provided by [https://www.abfallkalender-zak.de/](https://www.abfallkalender-zak.de/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_zollernalbkreis_de
      args:
        city: CITY
        street: STREET
        types:
          - "restmuell"
          - "gelbersack"
          - "papiertonne"
          - "biomuell"
          - "gruenabfall"
          - "schadstoffsammlung"
          - "altpapiersammlung"
          - "schrottsammlung"
          - "weihnachtsbaeume"
          - "elektrosammlung"
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(integer) (optional)*

**types**  
*(list of string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_zollernalbkreis_de
      args:
        city: "2,3,4"
        street: 3
        types:
          - "restmuell"
          - "gelbersack"
          - "papiertonne"
          - "biomuell"
          - "gruenabfall"
          - "schadstoffsammlung"
          - "altpapiersammlung"
          - "schrottsammlung"
          - "weihnachtsbaeume"
          - "elektrosammlung"
```

## How to get the source arguments

### Hardcore Variant: Extract arguments from website

Another way get the source arguments is to extract the arguments from the website using a (desktop) browser with developer tools, e.g. Google Chrome:

1. Open [https://www.abfallkalender-zak.de/](https://www.abfallkalender-zak.de/).
2. Enter your data, but don't click on "ICS Download" so far!
3. Open the Developer Tools (Ctrl + Shift + I) and open the `Network` tab.
4. Now click the "ICS Download" button.
5. You should see (amongst other's) one POST entry to Host https://www.abfallkalender-zak.de/ labeled `/` in the network recording.
6. Select `/` on the left hand side and click on Request on the right hand side.
7. At the `Form Data` you can find the values for `city` and `street` etc..
