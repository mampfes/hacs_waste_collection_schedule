# KOM-LUB (Luboń, PL)

Support for schedules provided by [KOM-LUB](https://kom-lub.com.pl), the waste collection operator serving the Luboń municipality in Poland.

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
*(integer) (required)*
Your collection district number (1–7), corresponding to zones R I through R VII. Check the [street-to-district lookup page](https://kom-lub.com.pl/alfabetyczny-wykaz-ulic-i-rejony/) or your bin collection notice.

| Value | Zone  |
|-------|-------|
| 1     | R I   |
| 2     | R II  |
| 3     | R III |
| 4     | R IV  |
| 5     | R V   |
| 6     | R VI  |
| 7     | R VII |

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: kom_lub_com_pl
      args:
        district: 1
```

## How to get the source argument

1. Visit [https://kom-lub.com.pl/alfabetyczny-wykaz-ulic-i-rejony/](https://kom-lub.com.pl/alfabetyczny-wykaz-ulic-i-rejony/).
2. Find your street in the table — the district column will show R I, R II, … R VII.
3. Use the corresponding number (1–7) as the `district` argument.

Your district may also be printed on your bin collection notice.
