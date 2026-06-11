# Rueil-Malmaison

Support for schedules provided by [Rueil-Malmaison](https://www.rueil-malmaison.fr) via the [Hauts-de-Seine open data portal](https://opendata.hauts-de-seine.fr), serving Rueil-Malmaison, France.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: rueil_malmaison_fr
      args:
        lat: 48.8768
        lon: 2.1875
```

### Configuration Variables

**lat**
*(float) (required)*
Latitude of your address (WGS84). You can find this in your Home Assistant configuration under *Settings → System → General* or from a mapping service.

**lon**
*(float) (required)*
Longitude of your address (WGS84).

## Notes

Collection types returned:

| Type | Description |
|------|-------------|
| Ordures Ménagères | Household waste |
| Emballages | Packaging (plastics, metals) |
| Verre | Glass |
| Déchets Végétaux | Garden waste (seasonal: March–mid December) |
| Encombrants | Bulky items |
