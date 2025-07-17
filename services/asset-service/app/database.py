import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
import json

from .models import (
    Investment, InvestmentCreate, InvestmentUpdate, 
    Instrument, InstrumentCreate, InstrumentUpdate,
    PortfolioInvestmentSummary, InvestmentResponse
)


class DynamoDBService:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.investment_table = self.dynamodb.Table("portfolio-tracker-investments")
        # We'll use a separate table for instruments metadata if needed
        # For now, we'll store basic instrument info with investments
    
    def _serialize_investment(self, investment: Investment) -> dict:
        """Convert Investment model to DynamoDB format"""
        data = investment.model_dump()
        # Convert datetime to ISO string and date to string
        data['created_at'] = data['created_at'].isoformat()
        data['updated_at'] = data['updated_at'].isoformat()
        data['purchase_date'] = data['purchase_date'].isoformat()
        if data.get('last_updated'):
            data['last_updated'] = data['last_updated'].isoformat()
        
        # Convert enum to string
        data['instrument_type'] = data['instrument_type'].value if hasattr(data['instrument_type'], 'value') else str(data['instrument_type'])
        
        # Convert floats to Decimal for DynamoDB
        for field in ['quantity', 'purchase_price', 'current_value', 'gain_loss', 'gain_loss_percent']:
            if data.get(field) is not None:
                data[field] = Decimal(str(data[field]))
        
        if data.get('current_price') is not None:
            data['current_price'] = Decimal(str(data['current_price']))
        
        return data
    
    def _deserialize_investment(self, item: dict) -> Investment:
        """Convert DynamoDB item to Investment model"""
        # Convert ISO string back to datetime/date
        item['created_at'] = datetime.fromisoformat(item['created_at'])
        item['updated_at'] = datetime.fromisoformat(item['updated_at'])
        item['purchase_date'] = date.fromisoformat(item['purchase_date'])
        
        if item.get('last_updated'):
            item['last_updated'] = datetime.fromisoformat(item['last_updated'])
        
        # Convert Decimal back to float
        for field in ['quantity', 'purchase_price', 'current_value', 'gain_loss', 'gain_loss_percent']:
            if item.get(field) is not None:
                item[field] = float(item[field])
        
        if item.get('current_price') is not None:
            item['current_price'] = float(item['current_price'])
        
        return Investment(**item)
    
    async def create_investment(self, investment_data: InvestmentCreate) -> Investment:
        """Create a new investment"""
        investment = Investment(**investment_data.model_dump())
        
        try:
            self.investment_table.put_item(
                Item=self._serialize_investment(investment),
                ConditionExpression='attribute_not_exists(investment_id)'
            )
            return investment
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ValueError("Investment with this ID already exists")
            raise
    
    async def get_investment(self, investment_id: str) -> Optional[Investment]:
        """Get investment by ID"""
        try:
            response = self.investment_table.get_item(Key={'investment_id': investment_id})
            if 'Item' in response:
                return self._deserialize_investment(response['Item'])
            return None
        except ClientError as e:
            raise Exception(f"Error getting investment: {e}")
    
    async def get_investments(self, limit: int = 100) -> List[Investment]:
        """Get all investments with pagination"""
        try:
            response = self.investment_table.scan(Limit=limit)
            investments = []
            for item in response.get('Items', []):
                investments.append(self._deserialize_investment(item))
            return investments
        except ClientError as e:
            raise Exception(f"Error getting investments: {e}")
    
    async def get_investments_by_portfolio(self, portfolio_id: str) -> List[Investment]:
        """Get all investments for a specific portfolio using GSI"""
        try:
            response = self.investment_table.query(
                IndexName='portfolio-index',
                KeyConditionExpression=Key('portfolio_id').eq(portfolio_id)
            )
            investments = []
            for item in response.get('Items', []):
                investments.append(self._deserialize_investment(item))
            return investments
        except ClientError as e:
            raise Exception(f"Error getting investments for portfolio: {e}")
    
    async def get_investments_by_ticker(self, ticker_symbol: str) -> List[Investment]:
        """Get all investments for a specific ticker symbol"""
        try:
            response = self.investment_table.scan(
                FilterExpression=Attr('ticker_symbol').eq(ticker_symbol)
            )
            investments = []
            for item in response.get('Items', []):
                investments.append(self._deserialize_investment(item))
            return investments
        except ClientError as e:
            raise Exception(f"Error getting investments for ticker: {e}")
    
    async def update_investment(self, investment_id: str, investment_data: InvestmentUpdate) -> Optional[Investment]:
        """Update investment by ID"""
        try:
            # Get current investment
            current_investment = await self.get_investment(investment_id)
            if not current_investment:
                return None
            
            # Update only provided fields
            update_data = investment_data.model_dump(exclude_unset=True)
            if not update_data:
                return current_investment
            
            # Build update expression
            update_expression = "SET updated_at = :updated_at"
            expression_values = {':updated_at': datetime.utcnow().isoformat()}
            
            for key, value in update_data.items():
                if key == 'purchase_date':
                    # Handle date conversion
                    value = value.isoformat()
                elif key in ['quantity', 'purchase_price'] and value is not None:
                    # Convert float to Decimal
                    value = Decimal(str(value))
                
                update_expression += f", {key} = :{key}"
                expression_values[f':{key}'] = value
            
            response = self.investment_table.update_item(
                Key={'investment_id': investment_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ReturnValues='ALL_NEW'
            )
            
            return self._deserialize_investment(response['Attributes'])
        except ClientError as e:
            raise Exception(f"Error updating investment: {e}")
    
    async def delete_investment(self, investment_id: str) -> bool:
        """Delete investment by ID"""
        try:
            response = self.investment_table.delete_item(
                Key={'investment_id': investment_id},
                ReturnValues='ALL_OLD'
            )
            return 'Attributes' in response
        except ClientError as e:
            raise Exception(f"Error deleting investment: {e}")
    
    async def update_investment_price(self, investment_id: str, current_price: float) -> Optional[Investment]:
        """Update investment current price and calculate gains/losses"""
        try:
            investment = await self.get_investment(investment_id)
            if not investment:
                return None
            
            # Calculate current value and gains/losses
            current_value = investment.quantity * current_price
            cost_basis = investment.quantity * investment.purchase_price
            gain_loss = current_value - cost_basis
            gain_loss_percent = (gain_loss / cost_basis) * 100 if cost_basis > 0 else 0
            
            response = self.investment_table.update_item(
                Key={'investment_id': investment_id},
                UpdateExpression="""SET current_price = :current_price, 
                                       current_value = :current_value,
                                       gain_loss = :gain_loss,
                                       gain_loss_percent = :gain_loss_percent,
                                       last_updated = :last_updated,
                                       updated_at = :updated_at""",
                ExpressionAttributeValues={
                    ':current_price': Decimal(str(current_price)),
                    ':current_value': Decimal(str(current_value)),
                    ':gain_loss': Decimal(str(gain_loss)),
                    ':gain_loss_percent': Decimal(str(gain_loss_percent)),
                    ':last_updated': datetime.utcnow().isoformat(),
                    ':updated_at': datetime.utcnow().isoformat()
                },
                ReturnValues='ALL_NEW'
            )
            
            return self._deserialize_investment(response['Attributes'])
        except ClientError as e:
            raise Exception(f"Error updating investment price: {e}")
    
    async def get_portfolio_investment_summary(self, portfolio_id: str) -> PortfolioInvestmentSummary:
        """Get investment summary for a portfolio"""
        try:
            investments = await self.get_investments_by_portfolio(portfolio_id)
            
            investment_responses = [InvestmentResponse(**inv.model_dump()) for inv in investments]
            
            total_value = sum(inv.current_value for inv in investments)
            total_cost_basis = sum(inv.quantity * inv.purchase_price for inv in investments)
            total_gain_loss = total_value - total_cost_basis
            total_gain_loss_percent = (total_gain_loss / total_cost_basis * 100) if total_cost_basis > 0 else 0
            
            return PortfolioInvestmentSummary(
                portfolio_id=portfolio_id,
                investments=investment_responses,
                total_investments=len(investment_responses),
                total_value=total_value,
                total_cost_basis=total_cost_basis,
                total_gain_loss=total_gain_loss,
                total_gain_loss_percent=total_gain_loss_percent
            )
        except Exception as e:
            raise Exception(f"Error getting portfolio investment summary: {e}")
    
    async def get_unique_tickers(self) -> List[str]:
        """Get all unique ticker symbols from investments"""
        try:
            response = self.investment_table.scan(
                ProjectionExpression='ticker_symbol'
            )
            
            tickers = set()
            for item in response.get('Items', []):
                tickers.add(item['ticker_symbol'])
            
            return list(tickers)
        except ClientError as e:
            raise Exception(f"Error getting unique tickers: {e}")


# Global instance
db_service = DynamoDBService()