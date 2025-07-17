import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
import json

from .models import Portfolio, PortfolioCreate, PortfolioUpdate, CustomerPortfolioSummary, PortfolioSummary


class DynamoDBService:
    def __init__(self, table_name: str = "portfolio-tracker-portfolios"):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
    
    def _serialize_portfolio(self, portfolio: Portfolio) -> dict:
        """Convert Portfolio model to DynamoDB format"""
        data = portfolio.model_dump()
        # Convert datetime to ISO string and enum to string
        data['created_at'] = data['created_at'].isoformat()
        data['updated_at'] = data['updated_at'].isoformat()
        data['type'] = data['type'].value if hasattr(data['type'], 'value') else str(data['type'])
        # Convert float to Decimal for DynamoDB
        data['total_value'] = Decimal(str(data['total_value']))
        return data
    
    def _deserialize_portfolio(self, item: dict) -> Portfolio:
        """Convert DynamoDB item to Portfolio model"""
        # Convert ISO string back to datetime
        item['created_at'] = datetime.fromisoformat(item['created_at'])
        item['updated_at'] = datetime.fromisoformat(item['updated_at'])
        # Convert Decimal back to float
        item['total_value'] = float(item['total_value'])
        return Portfolio(**item)
    
    async def create_portfolio(self, portfolio_data: PortfolioCreate) -> Portfolio:
        """Create a new portfolio"""
        portfolio = Portfolio(**portfolio_data.model_dump())
        
        try:
            self.table.put_item(
                Item=self._serialize_portfolio(portfolio),
                ConditionExpression='attribute_not_exists(portfolio_id)'
            )
            return portfolio
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ValueError("Portfolio with this ID already exists")
            raise
    
    async def get_portfolio(self, portfolio_id: str) -> Optional[Portfolio]:
        """Get portfolio by ID"""
        try:
            response = self.table.get_item(Key={'portfolio_id': portfolio_id})
            if 'Item' in response:
                return self._deserialize_portfolio(response['Item'])
            return None
        except ClientError as e:
            raise Exception(f"Error getting portfolio: {e}")
    
    async def get_portfolios(self, limit: int = 100) -> List[Portfolio]:
        """Get all portfolios with pagination"""
        try:
            response = self.table.scan(Limit=limit)
            portfolios = []
            for item in response.get('Items', []):
                portfolios.append(self._deserialize_portfolio(item))
            return portfolios
        except ClientError as e:
            raise Exception(f"Error getting portfolios: {e}")
    
    async def get_portfolios_by_customer(self, customer_id: str) -> List[Portfolio]:
        """Get all portfolios for a specific customer using GSI"""
        try:
            response = self.table.query(
                IndexName='customer-index',
                KeyConditionExpression=Key('customer_id').eq(customer_id)
            )
            portfolios = []
            for item in response.get('Items', []):
                portfolios.append(self._deserialize_portfolio(item))
            return portfolios
        except ClientError as e:
            raise Exception(f"Error getting portfolios for customer: {e}")
    
    async def update_portfolio(self, portfolio_id: str, portfolio_data: PortfolioUpdate) -> Optional[Portfolio]:
        """Update portfolio by ID"""
        try:
            # Get current portfolio
            current_portfolio = await self.get_portfolio(portfolio_id)
            if not current_portfolio:
                return None
            
            # Update only provided fields
            update_data = portfolio_data.model_dump(exclude_unset=True)
            if not update_data:
                return current_portfolio
            
            # Build update expression
            update_expression = "SET updated_at = :updated_at"
            expression_values = {':updated_at': datetime.utcnow().isoformat()}
            
            for key, value in update_data.items():
                if key == 'type':
                    # Handle enum conversion
                    value = value.value if hasattr(value, 'value') else str(value)
                update_expression += f", {key} = :{key}"
                expression_values[f':{key}'] = value
            
            response = self.table.update_item(
                Key={'portfolio_id': portfolio_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ReturnValues='ALL_NEW'
            )
            
            return self._deserialize_portfolio(response['Attributes'])
        except ClientError as e:
            raise Exception(f"Error updating portfolio: {e}")
    
    async def delete_portfolio(self, portfolio_id: str) -> bool:
        """Delete portfolio by ID"""
        try:
            response = self.table.delete_item(
                Key={'portfolio_id': portfolio_id},
                ReturnValues='ALL_OLD'
            )
            return 'Attributes' in response
        except ClientError as e:
            raise Exception(f"Error deleting portfolio: {e}")
    
    async def get_customer_portfolio_summary(self, customer_id: str) -> CustomerPortfolioSummary:
        """Get portfolio summary for a customer"""
        try:
            portfolios = await self.get_portfolios_by_customer(customer_id)
            
            portfolio_summaries = []
            total_value = 0.0
            
            for portfolio in portfolios:
                summary = PortfolioSummary(
                    portfolio_id=portfolio.portfolio_id,
                    name=portfolio.name,
                    type=portfolio.type,
                    total_value=portfolio.total_value,
                    investment_count=portfolio.investment_count,
                    created_at=portfolio.created_at
                )
                portfolio_summaries.append(summary)
                total_value += portfolio.total_value
            
            return CustomerPortfolioSummary(
                customer_id=customer_id,
                portfolios=portfolio_summaries,
                total_portfolios=len(portfolio_summaries),
                total_value=total_value
            )
        except Exception as e:
            raise Exception(f"Error getting customer portfolio summary: {e}")
    
    async def update_portfolio_value(self, portfolio_id: str, total_value: float, investment_count: int) -> Optional[Portfolio]:
        """Update portfolio total value and investment count"""
        try:
            response = self.table.update_item(
                Key={'portfolio_id': portfolio_id},
                UpdateExpression="SET total_value = :total_value, investment_count = :investment_count, updated_at = :updated_at",
                ExpressionAttributeValues={
                    ':total_value': Decimal(str(total_value)),
                    ':investment_count': investment_count,
                    ':updated_at': datetime.utcnow().isoformat()
                },
                ReturnValues='ALL_NEW'
            )
            
            if 'Attributes' in response:
                return self._deserialize_portfolio(response['Attributes'])
            return None
        except ClientError as e:
            raise Exception(f"Error updating portfolio value: {e}")


# Global instance
db_service = DynamoDBService()