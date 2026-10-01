# Affaldonline

Support for schedules provided by [Affaldonline](https://affaldonline.dk).

Gather waste collection schedules from Affaldonline

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: affaldonline_dk
      args:
        municipality: MUNICIPALITY
        values: VALUES
```

### Configuration Variables

**municipality**  
*(string) (required)*

**values**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: affaldonline_dk
      args:
        municipality: aeroe
        values: "N\xF8rregade|1||||5970|\xC6r\xF8sk\xF8bing|1228262|448776|0"
```

## How to get the source arguments

Open the address search of your waste company on the AffaldOnline platform, select your address and copy the raw `values` string of the address (pipe separated, e.g. `Nørregade|1||||5970|Ærøskøbing|1228262|448776|0`). Use the municipality key of your waste company as `municipality`.
