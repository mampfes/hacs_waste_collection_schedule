# Abfallkalender Würzburg

Support for schedules provided by [Abfallkalender Würzburg](https://www.wuerzburg.de/themen/umwelt-verkehr/vorsorge-entsorgung/abfallkalender/32208.Abfallkalender.html), serving the City of Würzburg.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wuerzburg_de
      args:
        district: ADDRESS
        street: STREET
```

### Configuration Variables

**district** and **street** can be used independently, only **one** is required. If set, priority will be given to **street**.

**district**  
*(string) (required)* - if *street* is empty

**street**  
*(string) (required)* - if *district* is empty

## Example

Both examples will yield the same result.

```yaml
waste_collection_schedule:
  sources:
    - name: wuerzburg_de
      args:
        district: "Altstadt"
```

```yaml
waste_collection_schedule:
  sources:
    - name: wuerzburg_de
      args:
        street: "Juliuspromenade"
```

## How to get the source argument

The source argument is either district or street as displayed in the web form at [Abfallkalender Würzburg](https://www.wuerzburg.de/themen/umwelt-verkehr/vorsorge-entsorgung/abfallkalender/32208.Abfallkalender.html). Exact match is required.
