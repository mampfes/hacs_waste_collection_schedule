# Newcastle City Council

Support for schedules provided by [Newcastle City Council](https://community.newcastle.gov.uk/my-neighbourhood/)

**Note**: Collection schedule will only show the next date, not all future dates

**Deprecation notice**: Newcastle City Council has retired the `community.newcastle.gov.uk` bin
lookup that this source depends on. It now always returns an empty result. The council has
moved bin collection information to [ReCollect](https://new.newcastle.gov.uk/recycling-waste/check-your-bin-collection-day)
(area `NewcastleUponTyneUK`). Please switch to the shared [ReCollect ICS source](ics.md) instead
— see [doc/ics/recollect.md](../ics/recollect.md) for setup instructions.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: newcastle_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**  
*(string) (required)*

This is required to unambiguously identify the property.

## Example using UPRN

```yaml
waste_collection_schedule:
    sources:
    - name: newcastle_gov_uk
      args:
        uprn: 74023685
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
