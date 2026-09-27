from field_invoice_service.service_invoice import issue_invoice_for_work_order
from field_invoice_service.models import (
    Customer,
    DispatchRecord,
    InvoiceLineItem,
    IssueInvoiceRequest,
    TechnicianFollowUp,
    WorkOrder,
    WorkOrderPhoto,
)


def build_sample_request() -> IssueInvoiceRequest:
    return IssueInvoiceRequest(
        customer=Customer(
            name="Oak & Shore Property Management",
            email="chenhua@changba.com",
            service_address="18 Harbor Lane, Monterey, CA",
        ),
        work_order=WorkOrder(
            work_order_id="WO-2048",
            dispatch=DispatchRecord(status="completed", scheduled_date="2026-09-12"),
            photos=[
                WorkOrderPhoto(
                    caption="Condensate drain clog before service",
                    image_url="https://example.com/photos/wo-2048-before.jpg",
                ),
                WorkOrderPhoto(
                    caption="System restored and drain cleared",
                    image_url="https://example.com/photos/wo-2048-after.jpg",
                ),
            ],
            technician_follow_up=TechnicianFollowUp(
                summary="Cleared the condensate line, tested cooling cycle, and confirmed normal drain flow.",
                recommend_return_visit=False,
            ),
            line_items=[
                InvoiceLineItem(description="HVAC diagnostics", quantity=1, unit_price=125.0),
                InvoiceLineItem(description="Drain line clearing", quantity=1, unit_price=185.0),
                InvoiceLineItem(description="Condensate tablets", quantity=1, unit_price=18.0),
            ],
        ),
    )


if __name__ == "__main__":
    result = issue_invoice_for_work_order(build_sample_request())
    print(f"Invoice issued: {result.invoice_number}")
    print(f"Email message id: {result.message_id}")
    print(f"Customer: {result.customer_email}")
