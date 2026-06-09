# Kirklees Council

Support for schedules provided by [Kirklees Council](https://www.kirklees.gov.uk),
served by the `my.kirklees.gov.uk` self-service portal.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: kirklees_gov_uk
      args:
        uprn: "83194785"
        postcode: "HD8 8NA"
```

### Configuration Variables

**uprn**  
*(string) (required)*

Unique Property Reference Number (UPRN) of the property. An easy way to discover
your UPRN is by going to <https://www.findmyaddress.co.uk/> and entering your
address details.

**postcode**  
*(string) (required)*

Postcode of the property.

**predict**  
*(boolean) (optional, default: `False`)*

Kirklees only returns the next collection date per bin type. With `predict: true`,
the source extrapolates a year of fortnightly dates from the next known date —
useful when consuming the data outside Home Assistant (e.g. exporting to a static
calendar). Home Assistant users typically don't need this, since the integration
refreshes nightly.

## Notes

This source uses the new `my.kirklees.gov.uk` JSON API. The previous source
scraped the now-defunct `kirklees.gov.uk/beta/your-property-bins-recycling/`
HTML pages and stopped working when Kirklees moved to their new portal.

**Breaking change:** the previous version accepted `door_num + postcode` and
optionally `uprn`. The new API requires `uprn` directly — `door_num` is no
longer accepted.
