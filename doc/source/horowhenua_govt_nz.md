# Horowhenua District Council

Support for schedules provided by [Horowhenua District Council Kerbside Rubbish & Recycling Services](https://www.horowhenua.govt.nz/Services/Home-Property/Rubbish-Recycling/Kerbside-Rubbish-Recycling-Services).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: horowhenua_govt_nz
      args:
        post_code: POST_CODE
        town: TOWN
        street_name: STREET_NAME
        street_number: STREET_NUMBER
```

### Configuration Variables

**post_code**<br>
*(string) (required)*

**town**<br>
*(string) (required)*

**street_name**<br>
*(string) (required)*

**street_number**<br>
*(string) (required)*

## Example


```yaml
waste_collection_schedule:
  sources:
    - name: horowhenua_govt_nz
      args:
        post_code: 4814
        town: Foxton
        street_name: State Highway 1
        street_number: 18
```

## How to get the source arguments

Visit the [Horowhenua District Council Waste and Recycling - Check my rubbish and recycling collection dates](https://www.horowhenua.govt.nz/Services/Home-Property/Rubbish-Recycling/Check-my-rubbish-and-recycling-collection-date) page and search for your address. The arguments should exactly match the results shown for Post Code, Town, Street and number portion of the Property.
