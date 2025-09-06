# pip install pywin32
import pathlib
from typing import Iterable, Optional, Sequence
import win32com.client as win32

def send_mail_outlook(
    subject: str,
    to: Sequence[str],
    html_body: str,
    *,
    plain_body: Optional[str] = None,   # if you want a text version, prepend below
    cc: Optional[Sequence[str]] = None,
    bcc: Optional[Sequence[str]] = None,
    attachments: Optional[Iterable[str]] = None,
    display_only: bool = False          # True = open compose window; False = send immediately
) -> None:
    """
    Sends an email using the locally installed Outlook (current profile).
    No credentials are needed; it uses the signed-in Outlook profile.
    """
    outlook = win32.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)  # 0 = olMailItem

    mail.Subject = subject
    # Outlook expects semicolon-separated recipients
    mail.To = "; ".join(to)
    if cc:
        mail.CC = "; ".join(cc)
    if bcc:
        mail.BCC = "; ".join(bcc)

    if plain_body:
        # Put a simple text part first (Outlook will still send HTML as the body)
        mail.Body = plain_body

    mail.HTMLBody = html_body  # HTML body

    for path in attachments or []:
        mail.Attachments.Add(str(pathlib.Path(path).resolve()))

    # Optionally select a specific account:
    # for acct in outlook.Session.Accounts:
    #     if acct.SmtpAddress.lower() == "you@your-domain.com":
    #         # mail.SendUsingAccount = acct  # works in VBA; in pywin32 often:
    #         mail._oleobj_.Invoke(64209, 0, 8, 0, acct)  # 64209 = DISPID for SendUsingAccount
    #         break

    if display_only:
        mail.Display(True)   # show compose UI
    else:
        mail.Send()          # send immediately

# --- Example ---
if __name__ == "__main__":
    import glob
    from datetime import datetime
    
    # Find the latest multiple POS CSV file
    import os
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_pattern = os.path.join(parent_dir, "multiple_pos_words_*.csv")
    csv_files = glob.glob(csv_pattern)
    latest_csv = max(csv_files, key=lambda x: os.path.getctime(x)) if csv_files else None
    
    if latest_csv:
        with open(latest_csv, 'r', encoding='utf-8') as f:
            total_words = len(f.readlines()) - 1
        
        send_mail_outlook(
            subject=f"Multiple POS Words Analysis - {datetime.now().strftime('%Y-%m-%d')}",
            to=["heyeqiu1210@gmail.com"],
            cc=[],
            bcc=[],
            plain_body=f"Multiple POS Words Analysis Report\n\nTotal words: {total_words}\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\nPlease see attached CSV file for details.",
            html_body=f"""<h2>Multiple POS Words Analysis</h2>
<p>Please find attached the CSV file with all {total_words} words that have multiple POS tags.</p>
<p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<p>The CSV contains lemma, POS combinations, CEFR levels, frequency, and notes.</p>""",
            attachments=[latest_csv],
            display_only=False
        )
        print(f"Email sent with attachment: {latest_csv}")
    else:
        print("No CSV file found!")
