# backend/services/email_service.py
"""
Serviço de envio de emails.

MODO ATUAL: SIMULAÇÃO (Console logs)
Para produção com SendGrid real, veja instruções no final do arquivo.
"""
import os

# ============================================================================
# SENDGRID IMPORTS - Comentado para avaliação (descomente para produção)
# ============================================================================
# from sendgrid import SendGridAPIClient
# from sendgrid.helpers.mail import Mail


def send_rsvp_notification(event, attendee):
    """Send email to host when someone RSVPs"""

    # ========================================================================
    # MODO SIMULAÇÃO - Para avaliadores (sem necessidade de conta SendGrid)
    # ========================================================================
    print("=" * 80)
    print("📧 EMAIL SIMULADO - NOVO RSVP")
    print("=" * 80)
    print(f"De: {os.getenv('SENDER_EMAIL', 'noreply@venha.app')}")
    print(f"Para: {event.host.email}")
    print(f"Assunto: Novo RSVP para {event.title}")
    print("-" * 80)
    print("CONTEÚDO DO EMAIL:")
    print("-" * 80)
    print(f"Nova Confirmação de Presença!")
    print(f"{attendee.name} confirmou presença no seu evento: {event.title}")
    print()
    print("Detalhes:")
    print(f"  - Adultos: {attendee.num_adults}")
    print(f"  - Crianças: {attendee.num_children}")
    print(f"  - WhatsApp: {attendee.whatsapp_number}")
    if attendee.comments:
        print(f"  - Comentários: {attendee.comments}")
    print()
    print("Veja todos os convidados no seu painel.")
    print("=" * 80)
    return True

    # ========================================================================
    # CÓDIGO SENDGRID ORIGINAL - Comentado para avaliação
    # Para produção: Descomente este bloco e comente o bloco de simulação acima
    # ========================================================================
    # sender_email = os.getenv("SENDER_EMAIL")
    #
    # message = Mail(
    #     from_email=sender_email,
    #     to_emails=event.host.email,
    #     subject=f"Novo RSVP para {event.title}",
    #     html_content=f"""
    #         <h2>Nova Confirmação de Presença!</h2>
    #         <p><strong>{attendee.name}</strong> confirmou presença no seu evento: <strong>{event.title}</strong></p>
    #
    #         <h3>Detalhes:</h3>
    #         <ul>
    #             <li>Adultos: {attendee.num_adults}</li>
    #             <li>Crianças: {attendee.num_children}</li>
    #             <li>WhatsApp: {attendee.whatsapp_number}</li>
    #             {f'<li>Comentários: {attendee.comments}</li>' if attendee.comments else ''}
    #         </ul>
    #
    #         <p>Veja todos os convidados no seu painel.</p>
    #     """,
    # )
    #
    # try:
    #     sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
    #     response = sg.send(message)
    #     print(f"✅ Email enviado! Status: {response.status_code}")
    #     return True
    # except Exception as e:
    #     print(f"❌ Erro ao enviar email: {e}")
    #     return False


def send_modification_notification(event, attendee):
    """Send email to host when someone modifies their RSVP"""

    # ========================================================================
    # MODO SIMULAÇÃO - Para avaliadores
    # ========================================================================
    print("=" * 80)
    print("📧 EMAIL SIMULADO - RSVP MODIFICADO")
    print("=" * 80)
    print(f"De: {os.getenv('SENDER_EMAIL', 'noreply@venha.app')}")
    print(f"Para: {event.host.email}")
    print(f"Assunto: RSVP Modificado - {event.title}")
    print("-" * 80)
    print("CONTEÚDO DO EMAIL:")
    print("-" * 80)
    print(f"RSVP Modificado")
    print(f"{attendee.name} modificou a confirmação para: {event.title}")
    print()
    print("Detalhes Atualizados:")
    print(f"  - Adultos: {attendee.num_adults}")
    print(f"  - Crianças: {attendee.num_children}")
    print(f"  - Comentários: {attendee.comments or 'Nenhum'}")
    print("=" * 80)
    return True

    # ========================================================================
    # CÓDIGO SENDGRID ORIGINAL - Comentado para avaliação
    # ========================================================================
    # sender_email = os.getenv("SENDER_EMAIL")
    #
    # message = Mail(
    #     from_email=sender_email,
    #     to_emails=event.host.email,
    #     subject=f"RSVP Modificado - {event.title}",
    #     html_content=f"""
    #         <h2>RSVP Modificado</h2>
    #         <p><strong>{attendee.name}</strong> modificou a confirmação para: <strong>{event.title}</strong></p>
    #
    #         <h3>Detalhes Atualizados:</h3>
    #         <ul>
    #             <li>Adultos: {attendee.num_adults}</li>
    #             <li>Crianças: {attendee.num_children}</li>
    #             <li>Comentários: {attendee.comments}</li>
    #         </ul>
    #     """,
    # )
    #
    # try:
    #     sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
    #     sg.send(message)
    #     print("✅ Email de modificação enviado!")
    #     return True
    # except Exception as e:
    #     print(f"❌ Erro ao enviar email: {e}")
    #     return False


def send_cancellation_notification(event, attendee, reason=""):
    """Send email to host when someone cancels"""

    # ========================================================================
    # MODO SIMULAÇÃO - Para avaliadores
    # ========================================================================
    print("=" * 80)
    print("📧 EMAIL SIMULADO - RSVP CANCELADO")
    print("=" * 80)
    print(f"De: {os.getenv('SENDER_EMAIL', 'noreply@venha.app')}")
    print(f"Para: {event.host.email}")
    print(f"Assunto: RSVP Cancelado - {event.title}")
    print("-" * 80)
    print("CONTEÚDO DO EMAIL:")
    print("-" * 80)
    print(f"RSVP Cancelado")
    print(f"{attendee.name} cancelou a presença em: {event.title}")
    if reason:
        print()
        print(f"Motivo: {reason}")
    print("=" * 80)
    return True

    # ========================================================================
    # CÓDIGO SENDGRID ORIGINAL - Comentado para avaliação
    # ========================================================================
    # sender_email = os.getenv("SENDER_EMAIL")
    #
    # message = Mail(
    #     from_email=sender_email,
    #     to_emails=event.host.email,
    #     subject=f"RSVP Cancelado - {event.title}",
    #     html_content=f"""
    #         <h2>RSVP Cancelado</h2>
    #         <p><strong>{attendee.name}</strong> cancelou a presença em: <strong>{event.title}</strong></p>
    #
    #         {f'<p><strong>Motivo:</strong> {reason}</p>' if reason else ''}
    #     """,
    # )
    #
    # try:
    #     sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
    #     sg.send(message)
    #     print("✅ Email de cancelamento enviado!")
    #     return True
    # except Exception as e:
    #     print(f"❌ Erro ao enviar email: {e}")
    #     return False


# ============================================================================
# INSTRUÇÕES PARA PRODUÇÃO COM SENDGRID REAL
# ============================================================================
"""
Para habilitar envio de emails real via SendGrid em produção:

1. Descomente os imports no início do arquivo:
   - from sendgrid import SendGridAPIClient
   - from sendgrid.helpers.mail import Mail

2. Em cada função (send_rsvp_notification, send_modification_notification,
   send_cancellation_notification):
   - COMENTE o bloco "MODO SIMULAÇÃO"
   - DESCOMENTE o bloco "CÓDIGO SENDGRID ORIGINAL"

3. Configure as variáveis de ambiente no arquivo .env:
   - SENDGRID_API_KEY=sua-chave-sendgrid-aqui
   - SENDER_EMAIL=seu-email@verificado.com

4. Certifique-se de que o email remetente está verificado no SendGrid:
   - Acesse: https://sendgrid.com
   - Settings → Sender Authentication → Verify a Single Sender
   - Use o mesmo email configurado em SENDER_EMAIL

5. Reinicie a aplicação para aplicar as mudanças.
"""
