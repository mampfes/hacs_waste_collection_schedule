# Fife Council

Support for schedules provided by [Fife Council](https://www.fife.gov.uk), serving Fife Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: fife_gov_uk
      args:
        uprn: "UPRN"
        
```

### Configuration Variables

**uprn**  
*(String | Integer) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: fife_gov_uk
      args:
        uprn: "320069189"
        
```

### How to find your `UPRN`

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
Otherwise you can inspect the web requests the Fife Council website makes when entering in your postcode and then selecting your address.

### A more complete example with a dashboard card

Here's a more complete example of the sources that adds pictures and shorter names to the types that come back from Fife's API:

```yaml
waste_collection_schedule:
  sources:
    - name: fife_gov_uk
      args:
        uprn: "320069189"
      customize:
        - type: "Food and Garden Waste / Brown Bin"
          alias: "Brown Bin"
          picture: https://www.binfactoryoutlet.co.uk/wp-content/uploads/2020/06/240L-Brown.jpg
        - type: "Landfill / Blue Bin"
          alias: "Blue Bin"
          picture: https://www.binfactoryoutlet.co.uk/wp-content/uploads/2020/06/240L-BLUE.jpg
        - type: "Paper and Cardboard / Grey Bin"
          alias: "Grey Bin"
          picture: https://www.binfactoryoutlet.co.uk/wp-content/uploads/2020/05/240L-ANTRACITE.jpg
        - type: "Cans and Plastics / Green Bin"
          alias: "Green Bin"
          picture: https://www.binfactoryoutlet.co.uk/wp-content/uploads/2020/06/240L-Green.jpg
  day_switch_time: "18:00"
  
```

Once you've done that, you can add sensors for each bin using just those short names:

```yaml
sensors:
  - platform: waste_collection_schedule
    name: Next Bin Collection
    add_days_to: true
  - platform: waste_collection_schedule
    name: Next Blue Bin Collection
    add_days_to: true
    types:
      - "Blue Bin"
  - platform: waste_collection_schedule
    name: Next Brown Bin Collection
    add_days_to: true
    types:
      - "Brown Bin"
  - platform: waste_collection_schedule
    name: Next Grey Bin Collection
    add_days_to: true
    types:
      - "Grey Bin"
  - platform: waste_collection_schedule
    name: Next Green Bin Collection
    add_days_to: true
    types:
      - "Green Bin"
    
 ```

And finally, you can use those sensors with an entity-filter card to produce a widget that shows a picture of the upcoming bin collections this week:

```yaml
type: entity-filter
entities:
  - sensor.next_blue_bin_collection
  - sensor.next_brown_bin_collection
  - sensor.next_grey_bin_collection
  - sensor.next_green_bin_collection
state_filter:
  - operator: regex
    value: \s(0|1|2|3|4|5|6)\s
card:
  type: glance
  show_name: false
  show_state: true
show_empty: false

```
