# MPGK Katowice

Support for schedules provided by [MPGK Katowice](https://www.mpgk.com.pl/).

Source for MPGK Katowice.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mpgk_com_pl
      args:
        street: STREET
        number: NUMBER
```

### Configuration Variables

**street**  
*(string) (required)*

**number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: mpgk_com_pl
      args:
        street: Warszawska
        number: 17
```
