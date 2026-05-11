# Fredrikstad kommune

Source for [Fredrikstad kommune](https://www.fredrikstad.kommune.no) waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: fredrikstad_no
      args:
        address: "Kanelveien 4"
```

### Configuration Variables

**address**
*(string) (required)*

Your street address as it appears on the [Fredrikstad tømmekalender](https://arcgis.fredrikstad.kommune.no/webapps/tommekalender/fredrikstad/) — typically street name and house number, e.g. `Kanelveien 4`.
