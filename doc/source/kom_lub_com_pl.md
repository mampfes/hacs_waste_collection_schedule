# kom-lub.com.pl

Support for schedules provided by [kom-lub.com.pl](https://kom-lub.com.pl/)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kom_lub_com_pl
      args:
        district: 1                 # Enter the number of region at kom-lub.com.pl/aktualny-harmonogram-wywozow/
```

### Configuration Variables

**district**  
*(number) (required)*

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: kom_lub_com_pl
      args:
        district: 1
```


```yaml
waste_collection_schedule:
  sources:
    - name: kom_lub_com_pl
      args:
        district: 2
```

## How to get the source argument

Open [kom-lub.com.pl](https://kom-lub.com.pl/alfabetyczny-wykaz-ulic-i-rejony/) and find your street and corresponding region.
