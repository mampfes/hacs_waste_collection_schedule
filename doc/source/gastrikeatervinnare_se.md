# Gästrike Återvinnare

Support for schedules provided by [Gästrike Återvinnare](https://minasidor.gastrikeatervinnare.se/).

Source for Gästrike Återvinnare waste collection

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gastrikeatervinnare_se
      args:
        customer_number: CUSTOMER_NUMBER
        password: PASSWORD
        address: ADDRESS
```

### Configuration Variables

**customer_number**  
*(string) (required)*

**password**  
*(string) (required)*

**address**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gastrikeatervinnare_se
      args:
        customer_number: '!secret gastrikeatervinnare_se_customer_number'
        password: '!secret gastrikeatervinnare_se_password'
```

## How to get the source arguments

Gästrike Återvinnare no longer publishes collection days openly; they are shown on Mina sidor (https://minasidor.gastrikeatervinnare.se) after login. Enter the customer number and password you log in with there (BankID login is not supported: create a password via 'Glömt lösenord' on the login page). If the account has bins at several addresses, enter one as shown on Mina sidor, e.g. 'Storgatan 1, GÄVLE'; otherwise leave the address empty.
