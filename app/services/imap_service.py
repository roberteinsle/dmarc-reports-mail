"""
IMAP service for fetching DMARC reports from email.
"""
import imaplib
import email
from email import policy
from email.message import EmailMessage
import gzip
import zipfile
import io
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class IMAPService:
    """Service for handling IMAP operations."""

    def __init__(self, host: str, port: int, user: str, password: str, folder: str = 'INBOX'):
        """
        Initialize IMAP service.

        Args:
            host: IMAP server hostname
            port: IMAP server port (typically 993 for SSL)
            user: IMAP username
            password: IMAP password
            folder: IMAP folder to monitor (default: INBOX)
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.folder = folder
        self.connection: Optional[imaplib.IMAP4_SSL] = None

    def connect(self) -> bool:
        """
        Establish IMAP SSL connection.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.connection = imaplib.IMAP4_SSL(self.host, self.port)
            self.connection.login(self.user, self.password)
            self.connection.select(self.folder)
            logger.info(f"Connected to IMAP server {self.host}")
            return True
        except Exception as e:
            logger.error(f"IMAP connection failed: {e}", exc_info=True)
            return False

    def search_dmarc_reports(self) -> List[bytes]:
        """
        Search for unread DMARC report emails.

        Returns:
            List of email message IDs
        """
        if not self.connection:
            raise ConnectionError("Not connected to IMAP server")

        try:
            # Search for unread emails with DMARC report indicators
            status, messages = self.connection.search(None, 'UNSEEN')

            if status != 'OK':
                logger.warning("Failed to search for emails")
                return []

            message_ids = messages[0].split()
            logger.info(f"Found {len(message_ids)} unread email(s)")
            return message_ids

        except Exception as e:
            logger.error(f"Failed to search emails: {e}", exc_info=True)
            return []

    def fetch_email(self, msg_id: bytes) -> Optional[EmailMessage]:
        """
        Fetch email by message ID.

        Args:
            msg_id: Email message ID

        Returns:
            EmailMessage object or None if fetch fails
        """
        if not self.connection:
            raise ConnectionError("Not connected to IMAP server")

        try:
            status, data = self.connection.fetch(msg_id, '(RFC822)')

            if status != 'OK':
                logger.warning(f"Failed to fetch email {msg_id}")
                return None

            email_body = data[0][1]
            message = email.message_from_bytes(email_body, policy=policy.default)
            return message

        except Exception as e:
            logger.error(f"Failed to fetch email {msg_id}: {e}", exc_info=True)
            return None

    def extract_attachments(self, message: EmailMessage) -> List[Tuple[str, bytes]]:
        """
        Extract all attachments from email.

        Args:
            message: EmailMessage object

        Returns:
            List of tuples (filename, file_bytes)
        """
        attachments = []

        try:
            for part in message.walk():
                if part.get_content_disposition() == 'attachment':
                    filename = part.get_filename()
                    if filename:
                        file_data = part.get_payload(decode=True)
                        attachments.append((filename, file_data))
                        logger.debug(f"Extracted attachment: {filename}")

        except Exception as e:
            logger.error(f"Failed to extract attachments: {e}", exc_info=True)

        return attachments

    def decompress_file(self, file_bytes: bytes, filename: str) -> Optional[bytes]:
        """
        Decompress .gz or .zip files.

        Args:
            file_bytes: Compressed file bytes
            filename: Filename to determine compression type

        Returns:
            Decompressed bytes or original bytes if not compressed
        """
        try:
            if filename.endswith('.gz'):
                return gzip.decompress(file_bytes)
            elif filename.endswith('.zip'):
                with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
                    # Extract first file from zip
                    names = zf.namelist()
                    if names:
                        return zf.read(names[0])
                    else:
                        logger.warning(f"Empty zip file: {filename}")
                        return None
            else:
                # Return as-is if not compressed
                return file_bytes

        except Exception as e:
            logger.error(f"Failed to decompress {filename}: {e}", exc_info=True)
            return None

    def delete_email(self, msg_id: bytes) -> bool:
        """
        Delete email by message ID.

        Args:
            msg_id: Email message ID

        Returns:
            True if deletion successful, False otherwise
        """
        if not self.connection:
            raise ConnectionError("Not connected to IMAP server")

        try:
            # Mark for deletion
            self.connection.store(msg_id, '+FLAGS', '\\Deleted')
            # Expunge to permanently delete
            self.connection.expunge()
            logger.info(f"Deleted email {msg_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete email {msg_id}: {e}", exc_info=True)
            return False

    def close(self):
        """Close IMAP connection."""
        if self.connection:
            try:
                self.connection.close()
                self.connection.logout()
                logger.info("IMAP connection closed")
            except Exception as e:
                logger.error(f"Error closing IMAP connection: {e}", exc_info=True)
            finally:
                self.connection = None

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
