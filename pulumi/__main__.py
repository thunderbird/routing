#!/bin/env python3

import boto3
import pulumi
import pulumi_cloudflare as cloudflare

from enum import Enum


__boto3_clients = {}


def boto3_client(service: str, region_name: str = None):
    if service not in __boto3_clients:
        __boto3_clients[service] = boto3.client(service, region_name=region_name)
    return __boto3_clients[service]


class AwsLoadBalancerRecordTarget:
    def __init__(self, arn: str):
        self.arn = arn

    def target(self) -> str:
        elbv2 = boto3_client('elbv2')
        response = elbv2.describe_load_balancers(LoadBalancerArns=[self.arn])
        load_balancers = response.get('LoadBalancers', [])
        if len(load_balancers) == 0:
            raise ValueError(f'Could not get load balancer {self.arn}')
        return load_balancers[0]['DNSName']


class RecordTargetKind(Enum):
    LOAD_BALANCER = AwsLoadBalancerRecordTarget


# Localize some config options
stack = pulumi.get_stack()
config = pulumi.Config()
zone_ids = config.get_object('zone_ids')


records = {}
for record_id, dns_config in config.get_object('dns', {}).items():
    record_config = dns_config.get('record')
    target_config = dns_config.get('target')

    # Pull the target class out of the enum based on the provided "kind"
    record_target_kind = (
        dict(RecordTargetKind.__members__.items()).get(target_config.pop('kind').upper()).value
    )

    # Use that kind of RecordTarget to determine the correct DNS record content
    target_value = record_target_kind(**target_config).target()
    record_config['content'] = target_value

    # If the zone_id field (required by the DnsRecord resource) is an entry in our zone_ids table
    # then do the substitution. If not, assume the user wants to pass the value in literally.
    zone_name = record_config.pop('zone_id')
    record_config['zone_id'] = zone_ids[zone_name] if zone_name in zone_ids else zone_name

    records[record_id] = cloudflare.DnsRecord(
        f'cf-dnsrecord-{record_id}-{stack}',
        **record_config,
    )
