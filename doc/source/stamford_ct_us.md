# City of Stamford, CT

```yaml
waste_collection_schedule:
  sources:
    - name: stamford_ct_us
      args:
        street: "Parker Ave"
```

Use the [public garbage and recycling lookup](https://stamfordapps.org/garbagerecycling/default.asp) to find your street.

- `street`: Street name without house number, for example `Parker Ave` or `Washington Blvd`.
- `house_number` (optional): Required when collection days vary by house-number range.

The source reads both the recycling and garbage tables and returns 26 weekly dates per applicable service. The council's `ALL` range works with or without a house number. Numbered ranges retain their odd/even restrictions; an explicit no-pickup entry omits that service. Ambiguous streets and required house numbers return suggestions.

## BaseSource migration

Configuration argument names stay unchanged. Waste types now use canonical, localised names; update filters, automations and customisations using the former labels.
