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
        city_part: "Sudé týdny"

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


The `city_part` can be set to "Sudé týdny" for areas serviced during even weeks or "Liché týdny" for areas serviced during odd weeks.


An empty `city_part` value retrieves all data from the dataset.