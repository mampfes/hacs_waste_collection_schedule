# Pendle Borough Council

Support for schedules provided by [Pendle Borough Council](https://www.pendle.gov.uk/binday), serving Pendle, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: pendle_gov_uk
      args:
        postcode: POSTCODE
        address: ADDRESS
        garden_waste_bin: true
        future_collection_dates: true
```

### Configuration Variables

**postcode**  
*(string) (required)*

**address**  
*(string) (required)*

**garden_waste_bin**  
*(boolean) (optional, default: false)*  
Set to `true` when the property has a green garden waste bin collected with the blue and brown bins.

**future_collection_dates**  
*(boolean) (optional, default: false)*  
Generate future collection dates from the returned schedule.

**collection_zone**  
*(string) (optional)*  
Only needed if Pendle returns multiple collection zones for the selected address.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: pendle_gov_uk
      args:
        postcode: BB9 7LJ
        address: PENDLE LEISURE TRUST, 1, MARKET STREET, NELSON
        garden_waste_bin: false
        future_collection_dates: true
```

## How to get the source argument

Go to [Pendle Borough Council bin collection day](https://www.pendle.gov.uk/binday), enter your postcode, and use the address text returned by the council.

If Home Assistant reports multiple matching collection zones for the address, set `collection_zone` to one of the suggested values.
