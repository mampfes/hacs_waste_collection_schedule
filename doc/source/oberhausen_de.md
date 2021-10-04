# Oberhausen.de / Stadt Oberhausen

Support for schedules provided by [Oberhausen.de](https://www.oberhausen.de) (Stadt Oberhausen / WBO / SBO) located in Northrhine-Westfalia, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: oberhausen_de
      args:
        street: street name
```

### Configuration Variables

**street**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: oberhausen_de
      args:
        street: Max-Plank-Ring
        
        # on large streets please check the available sections by supplying
        # just the street name on https://www.oberhausen.de/abfallkalender
        # and add more characters to make the request unique.
        #
        # eg. "Mülheimer Straße" gives:
        #  - Mülheimer Straße 1-299, 2-324
        #  - Mülheimer Straße 321-439,326-438
        #
        # Either use the full string "Mülheimer Straße 1-299, 2-324" or at least
        # as many characters to make a distinct choice, eg. the following would
        # be sufficient: 
        # street: Mülheimer Straße 1
```

Use `sources.customize` to filter or rename the waste types:

```yaml
waste_collection_schedule:
  sources:
    - name: oberhausen_de
      args:
        street: Max-Planck-Ring
      calendar_title: Abfallkalender
      customize:
        # rename types to shorter name
        - type: Blaue Papiertonne
          alias: Papiertonne
        - type: Hausmüll, grüner Deckel
          alias: Hausmüll
        - type: Gelber Sack / Gelbe Tonne
          alias: Gelbe Tonne
        
        # hide unwanted types
        - type: Hausmüll, blauer Deckel
          show: false
        - type: Hausmüll, roter Deckel
          show: false
        - type: Biotonne
          show: false
```
