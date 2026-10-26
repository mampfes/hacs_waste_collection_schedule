# Abfallkalender Würzburg (deprecated)

```yaml
waste_collection_schedule:
  sources:
    - name: wuerzburg_de
      args:
        district: "Altstadt"
        street: "Juliuspromenade"
```

This source remains **deprecated**. The [generic Würzburg ICS configuration](../ics/wuerzburg_de.md) is recommended for new configurations.

- `district` (optional): District name exactly as shown in the city calendar.
- `street` (optional): Street name exactly as shown in the city calendar.

Provide at least one. Street takes precedence when both are set. The city event API supplies the actual dates and collection image URLs for the next 365 days. Pictures are retained. Waste names now use canonical, localised categories; original provider labels are carried in descriptions where useful. Update filters and customisations using the former labels.
