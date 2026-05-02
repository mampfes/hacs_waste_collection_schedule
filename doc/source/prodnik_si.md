# Prodnik

Support for schedules provided by [Prodnik](https://prodnik.si/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: prodnik_si
      args:
        customer_number: "YOUR_CUSTOMER_NUMBER"
        password: "YOUR_PASSWORD"
```

### Configuration Variables

**customer_number**  
*(string) (required)*

**password**  
*(string) (required)*

## How to get the source argument

**You need to have a registered account in [Prodnik self-service portal](https://e.prodnik.si/Registracija)!**
To register one, you need to get your customer and bill number from your bills, then complete the registration process.
