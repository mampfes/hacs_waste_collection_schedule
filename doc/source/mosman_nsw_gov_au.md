# Mosman (New South Wales, Australia)

Support for schedules provided by [Mosman (New South Wales)](https://mosman.nsw.gov.au), serving Mosman Council Area, New South Wales, Australia.  

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: mosman_nsw_gov_au
      args:
        address: ADDRESS
        
```

### Configuration Variables

**address**  
*(String) (required)*

__Please check the details below on how to get this__

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: mosman_nsw_gov_au
      args:
        address: 12 Shadforth Street
        
```

## How to get the source argument

Go to [Council Website](https://mosman.nsw.gov.au/residents/waste-and-recycling/collection-dates) and start to type your address, then click the auto-fill.  Copy the full address that autofills and put it below.  Abbreviations (st etc) will give incorrect results - you *must* put the full auto-filled address.  If you see collection dates for today (incorrectly), this is almost always why.  
