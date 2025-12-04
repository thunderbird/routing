#!/bin/env python3

import pulumi
import pulumi_cloudflare as cloudflare


# Localize some config options
stack = pulumi.get_stack()
config = pulumi.Config()
protect = config.get_bool('protect', False)
zone_ids = config.get_object('zone_ids')


for record_id, record_config in config.get_object('dns', {}).items():
    # If the zone_id field (required by the DnsRecord resource) is an entry in our zone_ids table
    # then do the substitution. If not, assume the user wants to pass the value in literally.
    zone_name = record_config.pop('zone_id')
    record_config['zone_id'] = zone_ids[zone_name] if zone_name in zone_ids else zone_name

    cloudflare.DnsRecord(
        f'cf-dnsrecord-{record_id}-{stack}',
        **record_config,
        opts=pulumi.ResourceOptions(protect=protect),
    )
