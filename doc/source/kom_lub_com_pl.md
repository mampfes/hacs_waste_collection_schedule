# KOM-LUB (Luboń, PL)

Support for schedules provided by [KOM-LUB (Luboń, PL)](https://kom-lub.com.pl/aktualny-harmonogram-wywozow/).

Scrapes waste collection schedule by district (1..7) from kom-lub.com.pl.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kom_lub_com_pl
      args:
        district: DISTRICT
```

### Configuration Variables

**district**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: kom_lub_com_pl
      args:
        district: 1
```

## How to get the source arguments

Enter your district number (1–7). Your district (R I through R VII) is printed on your bin collection notice or can be found on the KOM-LUB website (https://kom-lub.com.pl).
