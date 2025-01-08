# Bremerhavener Entsorgungsgesellschaft mbH

Support for schedules provided by [Bremerhavener Entsorgungsgesellschaft mbH](https://beg-bhv.de), serving Bremerhaven, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: beg_logistics_de
      args:
        street: STREET
        hnr: "HOUSE NUMBER"
        two_weeks: TWO_WEEKS
```

### Configuration Variables

**street**  
*(String) (required)*

**hnr**  
*(String | Integer) (required)*

**two_weeks**
*(Boolean) (optional|default=False)* 

weather to use 14 day collection schedule


## Example

```yaml
waste_collection_schedule:
    sources:
    - name: beg_logistics_de
      args:
        street: Hafenstraße, Bremerhaven
        hnr: "22"
```

```yaml
waste_collection_schedule:
    sources:
    - name: beg_logistics_de
      args:
        street: Hadeler Heide, Cuxhaven
        hnr: "22"
        two_weeks: True
```

## How to get the source argument

Find the parameter of your address using [https://kalender.beg-logistics.de/schedules/public](https://kalender.beg-logistics.de/schedules/public) and write them exactly like on the web page.
