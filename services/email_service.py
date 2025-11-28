import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def send_rsvp_notification(event, attendee):
    """Send email to host when someone RSVPs"""

    message = Mail(
        from_email="ferfrancodias@gmail.com",  # Change this
        to_emails=event.host.email,
        subject=f"New RSVP for {event.title}",
        html_content=f"""
            <h2>New RSVP Received!</h2>
            <p><strong>{attendee.name}</strong> has RSVP'd to your event: <strong>{event.title}</strong></p>
            
            <h3>Details:</h3>
            <ul>
                <li>Adults: {attendee.num_adults}</li>
                <li>Children: {attendee.num_children}</li>
                <li>WhatsApp: {attendee.whatsapp_number}</li>
                {f'<li>Comments: {attendee.comments}</li>' if attendee.comments else ''}
            </ul>
            
            <p>View all attendees in your dashboard.</p>
        """,
    )

    try:
        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        response = sg.send(message)
        print(f"Email sent! Status code: {response.status_code}")
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


def send_modification_notification(event, attendee, changes):
    """Send email to host when someone modifies their RSVP"""

    message = Mail(
        from_email="noreply@yourdomain.com",
        to_emails=event.host.email,
        subject=f"RSVP Modified - {event.title}",
        html_content=f"""
            <h2>RSVP Modified</h2>
            <p><strong>{attendee.name}</strong> has modified their RSVP for: <strong>{event.title}</strong></p>
            
            <h3>Updated Details:</h3>
            <ul>
                <li>Adults: {attendee.num_adults}</li>
                <li>Children: {attendee.num_children}</li>
                <li>Comments: {attendee.comments}</li>
            </ul>
        """,
    )

    try:
        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        sg.send(message)
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


def send_cancellation_notification(event, attendee, reason=""):
    """Send email to host when someone cancels"""

    message = Mail(
        from_email="noreply@yourdomain.com",
        to_emails=event.host.email,
        subject=f"RSVP Cancelled - {event.title}",
        html_content=f"""
            <h2>RSVP Cancelled</h2>
            <p><strong>{attendee.name}</strong> has cancelled their RSVP for: <strong>{event.title}</strong></p>
            
            {f'<p><strong>Reason:</strong> {reason}</p>' if reason else ''}
        """,
    )

    try:
        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        sg.send(message)
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False
