from pydantic import BaseModel


class DashboardSummary(BaseModel):
    deals_today: int
    excellent_deals: int
    monitored_products: int
    alerts_sent: int
    online_stores: int

