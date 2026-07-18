# Borough of Ho-Ho-Kus

Support for schedules provided by [Borough of Ho-Ho-Kus](https://www.hhkborough.com).

Source for the Borough of Ho-Ho-Kus, New Jersey, USA.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hohokus_nj_us
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
    - name: hohokus_nj_us
      args:
        district: District 1
```

## How to get the source arguments

Select your collection district (1 or 2). The borough collects yard waste on your two solid-waste days from 1 April to 31 October, and garbage once a week the rest of the year; the days and season are read from the borough schedule page.
