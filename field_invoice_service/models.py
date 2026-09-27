from typing import List, Literal, Optional

from pydantic import BaseModel, Field


DispatchStatus = Literal["scheduled", "en_route", "completed", "canceled"]


class Customer(BaseModel):
    name: str
    email: str
    service_address: str


class DispatchRecord(BaseModel):
    status: DispatchStatus
    scheduled_date: str


class WorkOrderPhoto(BaseModel):
    caption: str
    image_url: str


class TechnicianFollowUp(BaseModel):
    summary: str
    recommend_return_visit: bool = False


class InvoiceLineItem(BaseModel):
    description: str
    quantity: float = Field(gt=0)
    unit_price: float = Field(ge=0)

    @property
    def total(self) -> float:
        return round(self.quantity * self.unit_price, 2)


class WorkOrder(BaseModel):
    work_order_id: str
    dispatch: DispatchRecord
    photos: List[WorkOrderPhoto]
    technician_follow_up: Optional[TechnicianFollowUp] = None
    line_items: List[InvoiceLineItem]


class IssueInvoiceRequest(BaseModel):
    customer: Customer
    work_order: WorkOrder


class InvoiceDecision(BaseModel):
    ready_to_invoice: bool
    reason: str


class IssuedInvoice(BaseModel):
    invoice_number: str
    customer_email: str
    total_amount: float
    message_id: str
