# Kalundborg Kommune

Support for schedules provided by [Kalundborg Kommune](https://kalundborg.dk/), serving Kalundborg municipality, Denmark.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: kalundborg_dk
      args:
        id: See description
```

### Configuration Variables

**id**  
_(String) (required)_

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: kalundborg_dk
      args:
        id: "00006ac8-0002-0001-4164-647265737320"
```

## How to get the id

Go to the [Kalundborg Kommune Min Side](https://kalundborg.dk/) page and navigate to waste collection services. Log in to your account to find your container/address ID.

You will find your ID in URL i.e. : https://kalundborg.infovision.dk/public/address/00006ac8-0002-0001-4164-647265737320

The ID should be a UUID format like: `00006ac8-0002-0001-4164-647265737320`

Contact Kalundborg Kommune if you need help finding your specific ID.
