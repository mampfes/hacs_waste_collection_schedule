# Shire of Dardanup

Dates come from the current waste guide linked on the [Find your bin day page](https://www.dardanup.wa.gov.au/our-services/waste-and-recycling/find-your-bin-day.aspx). The source reads the printed recycling/waste weeks and holiday replacements, up to 26 weeks ahead and within the published guide's dates.

## Configuration

```yaml
waste_collection_schedule:
  sources:
    - name: dardanup_wa_gov_au
      args:
        street: Hale Street
        service_area: Area 1
```

- **street** (optional): Street name without house number, or the townsite name as printed in the guide, e.g. `Burekup`, `Dardanup West` or `Ferguson Valley`.
- **service_area** (optional): `Area 1`, `Area 2`, `Dardanup and Burekup`, `Rural Area 1` or `Rural Area 2`. Select the guide page applying to your property. A street belonging to one urban area can infer this; streets spanning both areas require it.
- **collection_day** (optional): `Monday` to `Friday`. Overrides the street's weekday. Use with `service_area` if entering the weekday directly. For Ferguson Valley and Henty, enter the townsite as `street` and let the guide supply the separate waste and recycling weekdays.

Rural two-bin services have weekly general waste and fortnightly recycling, with no FOGO. Three-bin services have weekly FOGO and alternate recycling/general waste.

## Migration from the legacy source

Remove `recycling_in_even_week` and select `service_area` from the current guide. A permanent ISO-week parity rule gives incorrect dates across a 53-week year. Configurations still supplying the old argument receive an error explaining the change.

Waste types now use canonical, localised names. Update filters, automations and customisations using the former labels.

### Dardanup West

```yaml
waste_collection_schedule:
  sources:
    - name: dardanup_wa_gov_au
      args:
        street: Dardanup West
        service_area: Dardanup and Burekup
```
