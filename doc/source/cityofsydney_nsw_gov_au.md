# City of Sydney

Support for schedules provided by [City of Sydney](https://www.cityofsydney.nsw.gov.au), serving the City of Sydney local government area, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: cityofsydney_nsw_gov_au
      args:
        address: ADDRESS
        
```

### Configuration Variables

**address**  
*(String) (required)*

Street address with suburb (e.g. `17 Junction Street, Forest Lodge`).

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: cityofsydney_nsw_gov_au
      args:
        address: "17 Junction Street, Forest Lodge"
        
```

## How to get the source argument

Enter your street address including suburb, as it would appear on [City of Sydney's bin collection day lookup page](https://www.cityofsydney.nsw.gov.au/waste-recycling-services/find-my-bin-collection-day) (e.g. `17 Junction Street, Forest Lodge`).

If more than one property matches your address, the source will raise an error listing the possible matches — copy the exact match from that list into the `address` argument.

Note: this source only returns the next two upcoming collection dates for each bin type, matching what the official council widget provides.
