# Hedemora Energi

Support for schedules provided by [Hedemora Energi](https://www.hedemoraenergi.se/), serving Hedemora, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: hedemora_energi_se
      args:
        pickup_id: PICKUP_ID
```

Alternatively, the source can search for the pickup ID from an address:

```yaml
waste_collection_schedule:
    sources:
    - name: hedemora_energi_se
      args:
        address: ADDRESS
```

### Configuration Variables

**pickup_id**  
*(String) (optional)*

Hedemora Energi pickup ID. This is the recommended configuration because it skips address lookup.

**address**  
*(String) (optional)*

Address to search for. Required only when `pickup_id` is not provided. The address must match exactly one result.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: hedemora_energi_se
      args:
        pickup_id: "1392000"
```

```yaml
waste_collection_schedule:
    sources:
    - name: hedemora_energi_se
      args:
        address: Åsgatan 28
```

## How to get the source argument

Use `pickup_id` if you know it. Otherwise, enter your street address as shown in Hedemora Energi's fetch planner. If the address search returns multiple matches, use a more specific address or configure the source with `pickup_id`.
