# Winterthur

Support for schedules provided by [Winterthur](https://winterthur.ch/), serving Winterthur, Switzerland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: winterthur_ch
      args:
        street: STREET (Straße)
        
```

### Configuration Variables

**street**  
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: winterthur_ch
      args:
        street: Am Iberghang
```

## How to get the source argument

Find the parameter of your address using [https://m.winterthur.ch/index.php?apid=1066394](https://m.winterthur.ch/index.php?apid=1066394) and write them exactly like on the web page.
