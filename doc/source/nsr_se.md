# NSR - Nordvästra Skånes Renhållnings AB

Support for schedules provided by [NSR](https://nsr.se), serving the municipalities of Bjuv, Båstad, Helsingborg, Höganäs, Åstorp, and Ängelholm in Skåne, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: nsr_se
      args:
        address: ADDRESS
```

### Configuration Variables

**address**
*(string) (required)*

The street name and house number, e.g. `Signestorpsvägen 1`. Do not include postal code.

If the same street name exists in multiple municipalities, append the city after a comma, e.g. `Storgatan 1, Ekeby`.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: nsr_se
      args:
        address: "Signestorpsvägen 1"
```

## How to find your address

Search for your address at the [NSR Tömningskalender](https://nsr.se/privat/allt-om-din-sophamtning/nar-toms-mitt-karl/tomningskalender/). Enter only the street name and number — not the postal code or city name.
