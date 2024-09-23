# Lobbe App

Support for schedules provided by [Lobbe App](https://lobbe.app/), serving multiple municipalities in Hessen and Nordrhein-Westfalen, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: lobbe_app
      args:
        state: STATE (Bundesland)
        city: CITY (Gemeinde)
        street: STREET (Straße)
        
```

### Configuration Variables

**state**  
*(String) (required)* should be `Hessen` or `Nordrhein-Westfalen`

**city**  
*(String) (required)*

**street**  
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: lobbe_app
      args:
        state: Hessen
        city: Diemelsee
        street: Am Breuschelt 
```

## How to get the source argument

Find the parameter of your address using [https://lobbe.app/](https://lobbe.app/) and write them exactly like on the web page.
