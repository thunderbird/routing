# Routing Infrastructure Code

This directory contains Pulumi code for managing our high-level traffic routing.


## What Qualifies?

When does a DNS record belong under the control of this project as opposed to a more application-specific code repo?

- The record routes traffic to a publicly accessible endpoint intended for public use.
- The record does not pertain to traffic that exists internally within a single environment.

Two examples:

- A record that routes users to the frontend for Send **does belong here**.
- A record that tells Send in the `stage` environment how to contact the `stage` database **does not belong here** and instead belongs with the Send code.


## How It Works

This is a very simple Pulumi program that loops over a series of config entries under the `routing:dns` label and constructs `DnsRecord` resources using Cloudflare's Pulumi provider. The keys in this dict should map to inputs accepted by the [Cloudflare `DnsRecord` Resource](https://www.pulumi.com/registry/packages/cloudflare/api-docs/dnsrecord/#inputs).

There is also a `routing:zone_ids` option in which you can list domain names mapped to their Cloudflare zone IDs. This gives us a convenience feature in which the `zone_id` option of a `DnsRecord` may be set instead to a friendlier domain name listed in this table. This prevents your listing of records from using obscure IDs that make your config harder to understand. If you do not pass a matching domain name, the value provided will be passed through untouched.


## Importing a Record

If you need to bring a record under the control of this project, you will need to discover its Record ID. *To my awareness*, this is only visible in the web console by clicking a record's Edit button and then inspecting the HTML for the `<tr>` element that gets created there. This is unwieldy to say the least, and you are probably better off obtaining an API token with read permissions for the zone in question and asking the Cloudflare API about it.

The Zone ID can be obtained easily from the web console on the zone's DNS Overview page. If you prefer to find this with the API, try:

```bash
curl -X GET \
    -H 'Authorization: Bearer $API_TOKEN' \
    https://api.cloudflare.com/client/v4/zones
```

To get the records in that zone and their IDs, query for its `dns_records`:

```bash
curl -X GET \
    -H 'Authorization: Bearer $API_TOKEN' \
    https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records
```

The last piece of the puzzle is to obtain Pulumi's name for the resource. This is presented in the `Name` field when you run a `pulumi preview` which wants to create the record. It is also predictable, following this pattern: `cf-dnsrecord-$RECORD_NAME` where `$RECORD_NAME` is whatever you've called it in your config.

With all of this together, run an import command:

```bash
pulumi import cloudflare:index/dnsRecord:DnsRecord $RESOURCE_NAME $ZONE_ID/$RECORD_ID
```