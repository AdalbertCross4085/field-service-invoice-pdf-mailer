from unittest.mock import patch

from field_invoice_service.models import (
    Customer,
    DispatchRecord,
    InvoiceLineItem,
    IssueInvoiceRequest,
    TechnicianFollowUp,
    WorkOrder,
    WorkOrderPhoto,
)
from field_invoice_service.service_invoice import decide_invoice_ready, issue_invoice_for_work_order


def make_request() -> IssueInvoiceRequest:
    return IssueInvoiceRequest(
        customer=Customer(
            name="Oak & Shore Property Management",
            email="accounts@oakandshore.example",
            service_address="18 Harbor Lane, Monterey, CA",
        ),
        work_order=WorkOrder(
            work_order_id="WO-2048",
            dispatch=DispatchRecord(status="completed", scheduled_date="2026-09-12"),
            photos=[
                WorkOrderPhoto(
                    caption="Restored cooling output",
                    image_url="https://example.com/photos/after.jpg",
                )
            ],
            technician_follow_up=TechnicianFollowUp(
                summary="Replaced failed capacitor and tested normal startup.",
                recommend_return_visit=False,
            ),
            line_items=[
                InvoiceLineItem(description="Capacitor replacement", quantity=1, unit_price=220.0),
                InvoiceLineItem(description="Service call", quantity=1, unit_price=125.0),
            ],
        ),
    )


def test_decision_marks_completed_photo_backed_followup_job_as_ready():
    decision = decide_invoice_ready(make_request())
    assert decision.ready_to_invoice is True
    assert decision.reason == "ready to invoice"


def test_issue_invoice_calls_pdf_then_email_with_expected_fields():
    request = make_request()

    with patch("field_invoice_service.service_invoice.infrai.pdf.generate") as mock_pdf_generate, patch(
        "field_invoice_service.service_invoice.infrai.email.send"
    ) as mock_email_send:
        mock_pdf_generate.return_value = {
            "ok": True,
            "data": {"url": "https://example.com/generated-pdf"},
            "error": None,
            "metadata": {},
        }
        mock_email_send.return_value = {
            "ok": True,
            "data": {"message_id": "msg_123"},
            "error": None,
            "metadata": {},
        }

        result = issue_invoice_for_work_order(request)

    assert result.invoice_number == "INV-WO-2048"
    assert result.message_id == "msg_123"

    _, pdf_kwargs = mock_pdf_generate.call_args
    assert set(pdf_kwargs.keys()) == {"html", "page_size", "orientation", "store"}
    assert pdf_kwargs["page_size"] == "A4"
    assert pdf_kwargs["orientation"] == "portrait"
    assert pdf_kwargs["store"] is False
    assert "Field Service Invoice" in pdf_kwargs["html"]

    _, email_kwargs = mock_email_send.call_args
    assert set(email_kwargs.keys()) == {"to", "subject", "html", "attachments"}
    assert email_kwargs["to"] == "accounts@oakandshore.example"
    assert "Invoice INV-WO-2048" in email_kwargs["subject"]
    assert email_kwargs["attachments"] == [
        {"filename": "INV-WO-2048.pdf", "url": "https://example.com/generated-pdf"}
    ]
