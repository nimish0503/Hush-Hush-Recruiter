import os
import logging
import yagmail
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader 
import time 

load_dotenv()

class EmailService:
    """
    A module for sending various types of emails using yagmail.
    """

    def __init__(self, sender_email: str, sender_password: str, logger: logging.Logger = None, template_dir: str = "templates"):
        """
        Initializes the EmailService.

        Args:
            sender_email (str): The sender's email address.
            sender_password (str): The sender's email password (or App Password).
            logger (logging.Logger, optional):  A logger instance. If None, a new logger is created. Defaults to None.
            template_dir (str, optional): The directory containing email templates. Defaults to "templates".
        """
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.logger = logger or self._setup_logger()
        self.template_env = Environment(loader=FileSystemLoader(template_dir))

        try:
            self.yag = yagmail.SMTP(self.sender_email, self.sender_password)
            self.logger.info("Yagmail connection established.")
        except Exception as e:
            self.logger.error(f"Failed to connect to Yagmail: {e}")
            raise

    def _setup_logger(self) -> logging.Logger:
        """
        Sets up a basic logger if one isn't provided.

        Returns:
            logging.Logger: A logger instance.
        """
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def _render_template(self, template_name: str, context: dict) -> str:
        """
        Renders a Jinja2 template with the given context.

        Args:
            template_name (str): The name of the template file (e.g., "shortlist.html").
            context (dict): A dictionary of variables to pass to the template.

        Returns:
            str: The rendered HTML email body.
        """
        try:
            template = self.template_env.get_template(template_name)
            rendered_html = template.render(context)
            self.logger.debug(f"Template '{template_name}' rendered successfully.")
            return rendered_html
        except Exception as e:
            self.logger.error(f"Failed to render template '{template_name}': {e}")
            raise

    def send_email(self, recipient_email: str, subject: str, html_body: str, attachments: list = None):
        """
        Sends an email.

        Args:
            recipient_email (str): The recipient's email address.
            subject (str): The email subject.
            html_body (str): The HTML body of the email.
            attachments (list, optional): A list of file paths to attach. Defaults to None.
        """
        try:
            self.yag.send(
                to=recipient_email,
                subject=subject,
                contents=html_body,
                attachments=attachments or []
            )
            self.logger.info(f"Email sent successfully to {recipient_email} with subject '{subject}'.")
        except Exception as e:
            self.logger.error(f"Failed to send email to {recipient_email} with subject '{subject}': {e}")
            raise

    def send_shortlist_email(self, recipient_email: str, candidate_name: str, questionnaire_link: str, job_title: str):
        """
        Sends an email to a candidate informing them they've been shortlisted,
        including a link to a questionnaire.

        Args:
            recipient_email (str): The candidate's email address.
            candidate_name (str): The candidate's name.
            questionnaire_link (str): The link to the questionnaire.
        """
        subject = "You've been shortlisted for the Technical Round!"
        context = {
            "candidate_name": candidate_name,
            "questionnaire_link": questionnaire_link,
            "job_title": job_title,
            "deadline": time.strftime("%B %d, %Y", time.localtime(time.time() + 2 * 24 * 60 * 60)),
        }
        try:
            html_body = self._render_template("shortlist.html", context)
            self.send_email(recipient_email, subject, html_body)
            self.logger.info(f"Shortlist email sent to {recipient_email} for candidate '{candidate_name}'.")
        except Exception as e:
            self.logger.error(f"Failed to send shortlist email to {recipient_email} for candidate '{candidate_name}': {e}")
            raise

    def send_rejection_email(self, recipient_email: str, candidate_name: str):
        """
        Sends an email to a candidate informing them that they have been rejected
        after the technical round.

        Args:
            recipient_email (str): The candidate's email address.
            candidate_name (str): The candidate's name.
        """
        subject = "Update on Your Application"
        context = {
            "candidate_name": candidate_name,
        }
        try:
            html_body = self._render_template("rejection.html", context)
            self.send_email(recipient_email, subject, html_body)
            self.logger.info(f"Rejection email sent to {recipient_email} for candidate '{candidate_name}'.")
        except Exception as e:
            self.logger.error(f"Failed to send rejection email to {recipient_email} for candidate '{candidate_name}': {e}")
            raise
    
    def send_hr_interview_invitation(self, hr_email: str, candidate_email: str, candidate_name: str, interview_dates):

        candidate_subject = "Invitation to HR Interview - Choose Your Date"
        candidate_context = {
            "candidate_name": candidate_name,
            "interview_dates": interview_dates,
            "hr_email": hr_email
        }
        try:
            attachments = []
            candidate_html_body = self._render_template("hr_interview_invite.html", candidate_context)
            self.send_email(candidate_email, candidate_subject, [candidate_html_body], attachments)
            self.logger.info(f"HR interview invitation sent to {candidate_email} for candidate '{candidate_name}'. Interview dates: {interview_dates}")
        except Exception as e:
            self.logger.error(f"Failed to send HR interview invitation to {candidate_email} for candidate '{candidate_name}': {e}. Interview dates: {interview_dates}")
            raise

        hr_subject = "Schedule HR Interview - Candidate: " + candidate_name
        hr_context = {
            "candidate_name": candidate_name,
            "candidate_email": candidate_email,
            "interview_dates": interview_dates
        }
        try:
            hr_html_body = self._render_template("hr_interview_notification.html", hr_context)
            self.send_email(hr_email, hr_subject, hr_html_body)
            self.logger.info(f"HR notification email sent to {hr_email} for candidate '{candidate_name}'.  Candidate email: {candidate_email}. Interview dates: {interview_dates}")
        except Exception as e:
            self.logger.error(f"Failed to send HR notification email to {hr_email} for candidate '{candidate_name}': {e}. Candidate email: {candidate_email}. Interview dates: {interview_dates}")
            raise
    

if __name__ == "__main__":
    sender_email = os.getenv("EMAIL_ADDRESS")
    sender_password = os.getenv("EMAIL_PASSWORD")
    recipient_email = ["ashwin.apps00@gmail.com", "prajwalnaik28@gmail.com",
 "samhithakalinganahallisuresh@gmail.com"
]

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        email_service = EmailService(sender_email, sender_password, logger=logger)
    except Exception as e:
        logger.error(f"Failed to initialize EmailService: {e}")
        exit(1)

    try:
        email_service.send_shortlist_email(
            recipient_email=recipient_email,
            candidate_name="John Doe",
            questionnaire_link="https://example.com/questionnaire",
            job_title="Software Engineer"
            )
        logger.info("Shortlist email sending process initiated successfully.")
        email_service.send_rejection_email(
            recipient_email=recipient_email,
            candidate_name="John Doe"
        )
        logger.info("Rejection email sending process initiated successfully.")
        email_service.send_hr_interview_invitation(
            hr_email=["ashwin.apps00@gmail.com", "prajwalnaik28@gmail.com",
 "samhithakalinganahallisuresh@gmail.com"
],
            candidate_email=recipient_email,
            candidate_name="John Doe",
            interview_dates=["January 26, 2024", "January 27, 2024"]
        )
        logger.info("HR interview invitation email sending process initiated successfully.")
    except Exception as e:
        logger.error(f"Error sending shortlist email: {e}")