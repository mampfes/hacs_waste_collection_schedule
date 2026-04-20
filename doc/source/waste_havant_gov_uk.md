# Havant Borough Council

Support for schedules provided by [Havant Borough Council](https://waste.havant.gov.uk/), serving Havant Borough Council, United Kingdom.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: waste_havant_gov_uk
      args:
        username: USERNAME
        password: PASSWORD
```

### Configuration Variables

**username**  
_(String) (required)_

**password**  
_(String) (required)_

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: waste_havant_gov_uk
      args:
        username: fred.bloggs@email.com
        password: super-secure-password-123
```

## How to get the source argument

Visit <https://waste.havant.gov.uk/> and register an account, you will be prompted to enter your address.
