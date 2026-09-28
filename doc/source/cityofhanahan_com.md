# Hanahan, SC

Regular curbside collection days from the [City of Hanahan household trash collection schedule](https://www.cityofhanahan.com/publicworks/page/household-trash-collection-schedule). The source reads the current city schedule when Home Assistant refreshes it.

The city publishes collection areas by name, without a complete public address-to-route lookup. Select the area that serves your home. The supported values are `Hanahan Proper`, `Tanner Plantation`, `Eagle Landing`, `Otranto`, `Spring Valley Mobile Home Park`, `Gold Cup Springs`, `North Rhett`, `Lakeview subdivision`, and `Tuesday household waste area`. The Tuesday area is only for the streets and street segments listed on the city's schedule page. If your home is in one of those areas, check the city's street boundaries before selecting it.

```yaml
waste_collection_schedule:
  sources:
    - name: cityofhanahan_com
      args:
        area: "Tanner Plantation"
```

The source returns household waste, brown trash, yard debris, metals, and electronic scrap. It projects the published weekly days for 12 weeks. [Holiday and emergency changes](https://www.cityofhanahan.com/publicworks/page/holiday-schedule-2026) are announced separately by the city and are not included.
