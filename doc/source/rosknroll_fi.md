# RosknRoll Finland

Support for upcoming pick ups provided by [RosknRoll self-service portal](https://oma.rosknroll.fi/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: rosknroll_fi
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

**You need to have a registered account in RosknRoll's self-service portal!**
Register at https://oma.rosknroll.fi with your username and password, and use the same credentials here.
