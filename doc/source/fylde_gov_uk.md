# Fylde Council

Support for schedules provided by [Fylde Council](https://waste.fylde.gov.uk/), serving the Borough of Fylde, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: fylde_gov_uk
      args:
        email: EMAIL_ADDRESS
        password: PASSWORD
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER (optional)
```

### Configuration Variables

**email**  
*(string) (required)*

The email address used to log in to the Fylde Waste Portal.

**password**  
*(string) (required)*

The password used to log in to the Fylde Waste Portal.

**uprn**  
*(string | int) (optional)*

Your Unique Property Reference Number. Only required if you have multiple properties registered on your waste portal account. If not provided, the schedule for the first property on your account will be used.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: fylde_gov_uk
      args:
        email: "your.email@example.com"
        password: "your_password"
```

Or, if you have multiple properties, supply the UPRN of the property you wish to target:

```yaml
waste_collection_schedule:
    sources:
    - name: fylde_gov_uk
      args:
        email: "your.email@example.com"
        password: "your_password"
        uprn: "100010402452"
```

## How to get your credentials

1. **Register for the Fylde Waste Portal**  
   Visit <https://waste.fylde.gov.uk/> and create an account if you haven't already.

2. **Add your property**  
   After logging in, you'll need to add your property to your account.

3. **Use your credentials**  
   Use the email address and password you registered with in the configuration above.

## Support for multiple properties
If you have multiple properties registered on your waste portal account, you can specify which property to fetch the schedule for using the `uprn` parameter.

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering your address details.
