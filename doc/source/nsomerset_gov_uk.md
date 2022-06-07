# North Somerset Council

Support for schedules provided by [North Somerset Council](https://www.n-somerset.gov.uk/), serving Clevedon, Nailsea, Portishead and Weston super Mare, along with numerous villages.

If collection data is available for the address provided, it will return food, rubbish and recylcing waste collection dates.

<br />

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: nsomerset_gov_uk
      args:
        postcode: POSTCODE
        uprn:     UPRN
```   
### Configuration Variables

**postcode**<br>
*(string) (required)*

**uprn**<br>
*(string) (required)*
 
<br />

## Examples
#### Conifguration basic
```yaml
waste_collection_schedule:
    sources:
    - name: nsomerset_gov_uk
      args:
        postcode: BS231UJ
        uprn: 24009468
```
 
 #### Configuration detailed
 ```yaml
 waste_collection_schedule:
  sources:
    - name: nsomerset_gov_uk
      args:
        postcode: BS231UJ
        uprn: 24009468
      customize:
        - type: brown bin
          alias: Food
        - type: green bin
          alias: Recylcing
        - type: black bin
          alias: Rubbish
  fetch_time: "01:00"
  random_fetch_time_offset: 30
  day_switch_time: "10:00"
```

#### Sensors
```yaml
  - platform: waste_collection_schedule
    name: next_rubbish_collection
    types:
      - Rubbish
    add_days_to: true

  - platform: waste_collection_schedule
    name: next_recycling_collection
    types:
      - Recycling

  - platform: waste_collection_schedule
    name: next_food_collection
    types:
      - Food
```

<br />

## How to find your UPRN
An easy way to discover your Unique Property Reference Number (UPRN) is by going to [Find My Address](https://www.findmyaddress.co.uk/) and providng your address details. Otherwise you can inspect the source code on the [North Somerset waste collection](https://forms.n-somerset.gov.uk/Waste/CollectionSchedule) website after entering your postcode. 
