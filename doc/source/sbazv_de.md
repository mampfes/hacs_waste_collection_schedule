# Südbrandenburgischer Abfallzweckverband

Support for schedules provided by [https://www.sbazv.de/](https://www.sbazv.de/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sbazv_de
      args:
        city: CITY
        district: DISTRICT
        street: STREET
```

### Configuration Variables

**city**<br>
*(string) (required)*

**district**<br>
*(string) (required)*

**street**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: sbazv_de
      args:
        city: "wildau"
        district: "wildau"
        street: "Ahornring"
```

## How to get the source arguments

### Hardcore Variant: Extract arguments from website

The way to get the source arguments is to extract them from the website using a (desktop) browser with developer tools, e.g. Google Chrome:

1. Open [https://www.sbazv.de/entsorgungstermine/restmuell-papier-gelbesaecke-laubsaecke-weihnachtsbaeume/](https://www.sbazv.de/entsorgungstermine/restmuell-papier-gelbesaecke-laubsaecke-weihnachtsbaeume/).
2. Enter your data and click on "Termine anzeigen"
3. Right-click on "Download als ICS Datei"
4. In the context menu click on "Copy link address" (or something similiar, depending on your browser).
5. Paste the copied string to a text editor. You can see the string to download your ics file now.
