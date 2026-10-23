# Royal Borough Of Greenwich

Support for schedules provided by [Royal Borough Of Greenwich](https://www.royalgreenwich.gov.uk/).

Source for services from the Royal Borough Of Greenwich

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: royalgreenwich_gov_uk
      args:
        post_code: POST_CODE
        house: HOUSE
        address: ADDRESS
```

### Configuration Variables

**post_code**  
*(string) (optional)*

**house**  
*(string) (optional)*

**address**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: royalgreenwich_gov_uk
      args:
        address: 25 - Tizzard Grove - London - SE3 9DH
```

## How to get the source arguments

Using a browser, go to [royalgreenwich.gov.uk](https://www.royalgreenwich.gov.uk/info/200171/recycling_and_rubbish/100/find_your_bin_collection_day). Find the collection day and the first bold text in the message below the search bar (right after "At" and before ":") is your address, use it as-is.
