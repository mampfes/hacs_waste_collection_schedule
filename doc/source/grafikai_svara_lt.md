# Kauno švara

Support for schedules provided by [Kauno švara](https://svara.lt).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: grafikai_svara_lt
      args:
        region: CITY
        street: STREET_NAME
        house_number: HOUSE_NUMBER
        district: DISTRICT
        waste_object_ids:
          - WASTE_OBJECT_ID
```

### Configuration Variables

**region**<br>
*(string) (required)*

**street**<br>
*(string) (required)*

**house_number**<br>
*(string) (required)*

**district**<br>
*(string) (optional)*

**waste_object_ids**<br>
*(list) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: grafikai_svara_lt
      args:
        region: Kauno m. sav.
        street: Demokratų g.
        house_number: 7
        district: DISTRICT
        waste_object_ids:
          - 101358
          - 100858
          - 100860
```

## How to get the source arguments

Visit the [Grafikai](http://grafikai.svara.lt) page and search for your address.  The arguments should exactly match the following table below. To include waste object id's at search results page, copy url from "Atsisiųsti" button and take "wasteObjectId" parameter.

| Parameter name in grafikai.svara.lt | Argument in yaml |
|-------------------------------------|------------------|
| Regionas                            | region            |
| Gatvė                               | street             |
| Namo nr.                            | house_number             |
| Seniūnija                           | district             |
