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
        split_bins: SPLIT_BINS
        city: CITY
        street: STREET
        values: VALUES
```

### Configuration Variables

**municipality**  
*(string) (required)*

**split_bins**  
*(string) (optional)*

**city**  
*(string) (optional)*

**street**  
*(string) (optional)*

**values**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: affaldonline_dk
      args:
        municipality: aeroe
        city: "\xC6r\xF8sk\xF8bing"
        street: "N\xF8rregade|5970|\xC6r\xF8sk\xF8bing"
        values: "N\xF8rregade|1||||5970|\xC6r\xF8sk\xF8bing|4214342|448776|0"
```
