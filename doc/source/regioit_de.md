# RegioIT.de / AbfallNavi

NOTE: THIS SOURCE IS DEPRECATED! Use [Abfallnavi.de](./abfallnavi_de.md) instead!

Support for schedules provided by [RegioIT.de](https://www.regioit.de). The official service uses the name **AbfallNavi** instead.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: regio_it
      args:
        kalender: KALENDER
        ort: ORT
        strasse: STRASSE
        hnr: HNR
        fraktion:
          - 1
          - 2
          - 3
```

### Configuration Variables

**kalender**<br>
*(string) (required)*

**ort**<br>
*(string) (required)*

**strasse**<br>
*(integer) (required)*

**hnr**<br>
*(integer or None) (required)*

**fraktion**<br>
*(list of integer) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: regio_it
      args:
        kalender: lin
        ort: Lindlar
        strasse: 53585
        hnr: None
        fraktion:
          - 0
          - 1
          - 4
          - 11
```

## How to get the source arguments

### Simple Variant: Use wizard script

There is a script with an interactive command line interface which generates the required source configuration:

[https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/package/wizard/regioit_de.py](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/package/wizard/regioit_de.py).

Just run this script from a shell and answer the questions.

### Hardcore Variant: Extract arguments from website

Another way get the source arguments is to us a (desktop) browser with developer tools, e.g. Google Chrome:

1. Open your county's `AbfallNavi` homepage, e.g. [https://www.lindlar.de/buergerinfo-und-service/abfallentsorgung.html](https://www.lindlar.de/buergerinfo-und-service/abfallentsorgung.html).
2. Enter your data, but don't click on `ical-Export` so far!
3. Right click on `ical-Export` and select `Inspect` (Ctrl + Shift + I) to open the Developer Tools.
4. The marked entry on the right hand side (in the `Elements` tab) show the link behind the `ical-Export` button which contains all required arguments.

Example:

`<a _ngcontent-iun-45="" class="btn btn-primary" target="_blank" href="http://abfallkalender.regioit.de/kalender-lin/downloadfile.jsp?format=ics&amp;jahr=2020&amp;ort=Lindlar&amp;strasse=53585&amp;fraktion=0&amp;fraktion=2&amp;fraktion=3&amp;fraktion=4&amp;fraktion=5&amp;fraktion=6&amp;fraktion=7&amp;fraktion=8&amp;fraktion=9">ical-Export</a>`

- kalender = `lin`, see ...kalender-**lin**/downloadfile.jsp...
- ort = `Lindlar`
- strasse = `53585`
- hnr is missing, therefore use None instead
- fraktion = 0, 2, 3, 4, 5, 6, 7, 8, 9
