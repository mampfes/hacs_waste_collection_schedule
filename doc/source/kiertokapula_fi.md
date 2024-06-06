# Kiertokapula Finland

Support for upcoming pick ups provided by [Kiertokapula self-service portal](https://asiakasnetti.kiertokapula.fi/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: kiertokapula_fi
      args:
        bill_number: "YOUR_BILL_NUMBER"
        password: "YOUR_PASSWORD"
```

### Configuration Variables

**bill_number**  
*(string) (required)*

**password**  
*(string) (required)*

## How to get the source argument

**You need to have a registered account in Kiertokapula's self-service portal!**
To register one, you need to get your customer number from your bills, and password is by default your home address. 
System will prompt you a password change, after you've done it, you have now registered your user and it's ready to be configured here.
