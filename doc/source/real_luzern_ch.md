# Real, Switzerland

Support for schedules provided by [real-luzern.ch](https://www.real-luzern.ch)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: real_luzern_ch
      args:
        municipality_id: YOUR_MUNICIPALITY_ID
        street_id: YOUR_STREET_ID
```

### Configuration Variables

**municipality_id**  
_(number) (required)_ The id of your municipality

**street_id**  
_(number) (optional)_
Larger municipalities (like Lucern) have a different schedule for every street.

## How to get the IDs

Open [Entsorgungsdaten Real](https://www.real-luzern.ch/abfall/sammeldienst/abfallkalender/). Select your municipality (and street if required).
The URL in your browser will change and add a query string in the form of `?gemId=1234&strId=5678`.

- Use the value of `gemId` (in this example `1234`) to set the `municipality_id`
- Use the value of `strId` (in this example `5678`) to set the `street_id`. This value is only required if you had to select a street.

## Examples

Location `Emmen` without street:

```yaml
waste_collection_schedule:
  sources:
    - name: real_luzern_ch
      args:
        municipality_id: 6
```

Location `Luzern - Heimatweg` with street:

```yaml
waste_collection_schedule:
  sources:
    - name: real_luzern_ch
      args:
        municipality_id: 13
        street_id: 766
```
