# Chiemgau Recycling - Landkreis Rosenheim (Unofficial API)

Support for schedules provided by [Chiemgau Recycling](https://chiemgau-recycling.de), serving Landkreis Rosenheim, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: chiemgau_recycling_lk_rosenheim
      args:
        district: "Bruckmühl 2"
        
```

### Configuration Variables

**district**  
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: chiemgau_recycling_lk_rosenheim
      args:
        district: "Bruckmühl 2"
        
```

## How to get the source argument

Open [Chiemgau Recycling](https://chiemgau-recycling.de/#abfuhrplaene) and pick your district from the Landkreis Rosenheim PDF.