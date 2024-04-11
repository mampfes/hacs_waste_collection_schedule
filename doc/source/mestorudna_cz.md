# Rudná u Prahy - Czech Republic

Support for schedules provided by [Městský úřad Rudná](https://www.rudnamesto.cz/), CZ.

Published data description - [https://www.mesto-rudna.cz/odpadovy-kalendar/data_readme.html](https://www.mesto-rudna.cz/odpadovy-kalendar/data_readme.html)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: mestorudna_cz
      args:
        city_part: CITY_PART
```

### Configuration Variables

**city_part**</br>
*(string)*

## Example
```yaml
waste_collection_schedule:
    sources:
    - name: mestorudna_cz
      args:
        city_part: "S"

sensor:
  - platform: waste_collection_schedule
    name: next_yard_collection
    types:
      - Svoz sběrných hnízd - papír
    details_format: appointment_types
```

#### How to find your `city_part`

Look at

[https://www.rudnamesto.cz/odpadovy-kalendar/d-193572](https://www.rudnamesto.cz/odpadovy-kalendar/d-193572)


city_part can be set to "S" for the North part of the city or "J" for the South part of the city.

An empty city_part value retrieves all data from the dataset.