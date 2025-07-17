import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from typing import List, Optional
from datetime import datetime
import json

from .models import Customer, CustomerCreate, CustomerUpdate


class DynamoDBService:
    def __init__(self, table_name: str = "portfolio-tracker-customers"):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
    
    def _serialize_customer(self, customer: Customer) -> dict:
        """Convert Customer model to DynamoDB format"""
        data = customer.model_dump()
        # Convert datetime to ISO string
        data['created_at'] = data['created_at'].isoformat()
        data['updated_at'] = data['updated_at'].isoformat()
        return data
    
    def _deserialize_customer(self, item: dict) -> Customer:
        """Convert DynamoDB item to Customer model"""
        # Convert ISO string back to datetime
        item['created_at'] = datetime.fromisoformat(item['created_at'])
        item['updated_at'] = datetime.fromisoformat(item['updated_at'])
        return Customer(**item)
    
    async def create_customer(self, customer_data: CustomerCreate) -> Customer:
        """Create a new customer"""
        customer = Customer(**customer_data.model_dump())
        
        try:
            self.table.put_item(
                Item=self._serialize_customer(customer),
                ConditionExpression='attribute_not_exists(customer_id)'
            )
            return customer
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ValueError("Customer with this ID already exists")
            raise
    
    async def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get customer by ID"""
        try:
            response = self.table.get_item(Key={'customer_id': customer_id})
            if 'Item' in response:
                return self._deserialize_customer(response['Item'])
            return None
        except ClientError as e:
            raise Exception(f"Error getting customer: {e}")
    
    async def get_customers(self, limit: int = 100) -> List[Customer]:
        """Get all customers with pagination"""
        try:
            response = self.table.scan(Limit=limit)
            customers = []
            for item in response.get('Items', []):
                customers.append(self._deserialize_customer(item))
            return customers
        except ClientError as e:
            raise Exception(f"Error getting customers: {e}")
    
    async def update_customer(self, customer_id: str, customer_data: CustomerUpdate) -> Optional[Customer]:
        """Update customer by ID"""
        try:
            # Get current customer
            current_customer = await self.get_customer(customer_id)
            if not current_customer:
                return None
            
            # Update only provided fields
            update_data = customer_data.model_dump(exclude_unset=True)
            if not update_data:
                return current_customer
            
            # Build update expression
            update_expression = "SET updated_at = :updated_at"
            expression_values = {':updated_at': datetime.utcnow().isoformat()}
            
            for key, value in update_data.items():
                if key == 'address':
                    update_expression += f", address = :address"
                    expression_values[':address'] = value
                else:
                    update_expression += f", {key} = :{key}"
                    expression_values[f':{key}'] = value
            
            response = self.table.update_item(
                Key={'customer_id': customer_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ReturnValues='ALL_NEW'
            )
            
            return self._deserialize_customer(response['Attributes'])
        except ClientError as e:
            raise Exception(f"Error updating customer: {e}")
    
    async def delete_customer(self, customer_id: str) -> bool:
        """Delete customer by ID"""
        try:
            response = self.table.delete_item(
                Key={'customer_id': customer_id},
                ReturnValues='ALL_OLD'
            )
            return 'Attributes' in response
        except ClientError as e:
            raise Exception(f"Error deleting customer: {e}")
    
    async def get_customer_by_email(self, email: str) -> Optional[Customer]:
        """Get customer by email (scan operation)"""
        try:
            response = self.table.scan(
                FilterExpression='email = :email',
                ExpressionAttributeValues={':email': email}
            )
            
            items = response.get('Items', [])
            if items:
                return self._deserialize_customer(items[0])
            return None
        except ClientError as e:
            raise Exception(f"Error getting customer by email: {e}")


# Global instance
db_service = DynamoDBService()