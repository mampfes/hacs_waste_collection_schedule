# Royal Borough Of Greenwich

Support for schedules provided by the [Royal Borough Of Greenwich](https://www.royalgreenwich.gov.uk/info/200171/recycling_and_rubbish/100/find_your_bin_collection_day).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: royalgreenwich_gov_uk
      args:
        post_code: POST_CODE
        house: HOUSE_NUMBER
        address: FULL_ADDRESS
```

### Configuration Variables

**address**
*(string) (optional)*

This is required if you do not supply any other options. (Using this removes the need to do an address look up web request)

**house**
*(string) (optional)*

This is required if you supply a Postcode.

**post_code**
*(string) (optional)*

This is required if you do not supply an Address. Single space between 1st and 2nd part of postcode is optional.

#### How to find your `FULL_ADDRESS`

An easy way to discover your full address is:

1. Go to <https://www.royalgreenwich.gov.uk/info/200171/recycling_and_rubbish/100/find_your_bin_collection_day>
1. Find your property and click "Search" button
1. First bold text in the message below the search bar (right after "At" and before ":") is your address, use it as-is.

## Example using FULL_ADDRESS

```yaml
waste_collection_schedule:
    sources:
    - name: royalgreenwich_gov_uk
      args:
        address: "32 - Glenlyon Road - London - SE9 1AJ"
```

## Example using Address lookup

```yaml
waste_collection_schedule:
    sources:
    - name: royalgreenwich_gov_uk
      args:
        post_code: "SE9 5AW"
        number: "11"
```
