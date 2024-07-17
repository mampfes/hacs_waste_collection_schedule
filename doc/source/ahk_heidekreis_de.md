# AHK Heidekreis

Support for schedules provided by [ahk-heidekreis.de](https://www.ahk-heidekreis.de/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ahk_heidekreis_de
      args:
        city: CITY
        postcode: POSTCODE
        street: STREET
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**city**  
_(string) (required)_

**postcode**  
_(string) (required)_

**street**  
_(string) (required)_

**house_number**  
_(string) (required)_

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ahk_heidekreis_de
      args:
        city: Munster
        postcode: 29633
        street: Wagnerstr.
        house_number: "10-18"
    - name: ahk_heidekreis_de
      args:
        city: Fallingbostel/Bad Fallingbostel
        postcode: "29683"
        street: Konrad-Zuse-Str.
        house_number: "4"
```

## How to get the source argument

Find the parameter of your address using [https://www.ahk-heidekreis.de/fuer-privatkunden/abfuhrzeiten.html](https://www.ahk-heidekreis.de/fuer-privatkunden/abfuhrzeiten.html), click on "Entsorgungskalender", use the address lookup and write them exactly like on the web page.
