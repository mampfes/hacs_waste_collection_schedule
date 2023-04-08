# Affärsverken

Support for schedules provided by [Affärsverken](https://www.affarsverken.se/), Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: affarsverken_se
      args:
        address: ADDRESS
        
```

### Configuration Variables

**address**  
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: affarsverken_se
      args:
        address: Albatrossvägen 5, Ramdala
        
```

## How to get the source argument

Write you address exactly like on [https://www.affarsverken.se/avfallstjanster/hamtningstider/](https://www.affarsverken.se/avfallstjanster/hamtningstider/).
