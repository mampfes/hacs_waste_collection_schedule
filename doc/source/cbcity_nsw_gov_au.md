# City of Canterbury-Bankstown

```yaml
waste_collection_schedule:
  sources:
    - name: cbcity_nsw_gov_au
      args:
        address: "102 Crinan Street, Hurlstone Park 2193"
```

Find your property using the [council bin day finder](https://bindayfinder.azurewebsites.net).

- `address`: Full property address. Commas and NSW may be omitted; common street type abbreviations and unit addresses are accepted.

The source uses the public street dataset, retains its address-specific bin model and reads the cycle anchor from the current web application. It returns dates from today to the end of the year. Red bins map to general waste, yellow bins to recycling and green bins to organic waste. Ambiguous addresses return suggestions. Each fetch reads the current data rather than relying on the legacy source's month-long cache.

## BaseSource migration

Configuration argument names stay unchanged. Waste types now use canonical, localised names; update filters, automations and customisations using the former labels.
