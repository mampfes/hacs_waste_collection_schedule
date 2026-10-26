# Grand Paris Sud Est Avenir (GPSEA)

```yaml
waste_collection_schedule:
  sources:
    - name: sudestavenir_fr
      args:
        commune: "Creteil"
        street: "Place du Grand Pavois"
        house_number: "1"
```

Use your address in the [GPSEA waste collection map](https://sudestavenir.fr/).

- `commune`: Your commune within GPSEA.
- `street`: Street name. French types such as Place/PL, Avenue/AV and Allée/ALL are accepted.
- `house_number`: House number, as shown in the map.

The public GEO Software map supplies the address-specific infosheet. Its weekly/fortnightly rules, ISO-week parity, date lists and seasonal ranges determine the dates. The year of explicitly dated lists/ranges comes from the calendar linked by that infosheet; those lists are not projected into the next year. Morning/afternoon descriptions are retained. Ambiguous matches raise an error with suggestions.

## BaseSource migration

Configuration argument names stay unchanged. Waste types now use canonical, localised names; update filters, automations and customisations using the former labels.
