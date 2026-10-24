# Perfect Waste

Support for schedules provided by [Perfect Waste](https://perfectwaste.dk).

Source for Danish municipalities using the Perfect Waste app.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: perfectwaste_dk
      args:
        municipality: MUNICIPALITY
        address: ADDRESS
```

### Configuration Variables

**municipality**  
*(string) (required)*

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: perfectwaste_dk
      args:
        municipality: Horsens
        address: "S\xF8ndermarken 10, 8752 \xD8stbirk"
```

## How to get the source arguments

Select your municipality and enter your address the way the Perfect Waste app writes it, e.g. "Søndermarken 10, 8752 Østbirk". If the address is ambiguous, the error message lists the matching addresses. Important: Perfect Waste only returns collection dates for addresses it already knows. If you get an error saying there are no collection dates stored for your address, add the address once in the Perfect Waste app (or your municipality's own Perfect Waste app) and then reload this source.
