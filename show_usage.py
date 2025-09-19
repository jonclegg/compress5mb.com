#!/usr/bin/env python3
"""
Show usage script for 5MB converter DynamoDB jobs.

Lists all conversion jobs from DynamoDB, newest first.
Requires boto3 and AWS credentials configured.

Usage: python3 show_usage.py
"""

import os
import boto3
from datetime import datetime


TABLE_NAME = "fivemb-website-dev-uploads-status"


###############################################################################

def main():
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    
    # List all tables to find the correct one
    dynamodb_client = boto3.client("dynamodb", region_name="us-east-1")
    tables = dynamodb_client.list_tables()
    print(f"Available DynamoDB tables: {tables['TableNames']}")
    
    # Check if our table exists or find a similar one
    target_table = None
    for table_name in tables['TableNames']:
        if 'uploads-status' in table_name:
            target_table = table_name
            break
    
    if not target_table:
        print(f"No table containing 'uploads-status' found.")
        print(f"This likely means the serverless stack hasn't been deployed yet.")
        print(f"Available tables: {tables['TableNames']}")
        print(f"\nTo deploy the stack, run: serverless deploy")
        print(f"Once deployed, the table name should be: {TABLE_NAME}")
        return 0
    
    print(f"Using table: {target_table}")
    table = dynamodb.Table(target_table)
    
    try:
        response = table.scan()
        items = response["Items"]
        
        while "LastEvaluatedKey" in response:
            response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response["Items"])
        
        items.sort(key=lambda x: int(x.get("updated_at", 0)), reverse=True)
        
        print(f"Found {len(items)} jobs in DynamoDB:")
        print("-" * 120)
        
        for item in items:
            upload_key = item.get("upload_key", "")
            state = item.get("state", "unknown")
            updated_at = int(item.get("updated_at", 0))
            source = item.get("source", "")
            output = item.get("output", "")
            error = item.get("error", "")
            
            timestamp = datetime.fromtimestamp(updated_at).strftime("%Y-%m-%d %H:%M:%S") if updated_at else "unknown"
            
            filename = ""
            if upload_key:
                parts = upload_key.split("/")
                if len(parts) >= 3:
                    filename = parts[-1]
            
            status_display = state
            if error:
                status_display += f" ({error})"
            
            print(f"{timestamp:<20} {state:<12} {filename:<50} {upload_key}")
            if output:
                print(f"{'':20} {'':12} Output: {output}")
            if error:
                print(f"{'':20} {'':12} Error: {error}")
            print()
            
    except Exception as e:
        print(f"Error scanning DynamoDB table: {e}")
        return 1
    
    return 0


###############################################################################

if __name__ == "__main__":
    exit(main())
