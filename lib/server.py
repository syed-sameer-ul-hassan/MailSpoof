from __future__ import annotations

import re
import signal
import socket
import smtplib
import sys
import threading
import http.server
import json
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from typing import List

from lib.core import Config, LOG_FILE, CONFIG_DIR, __version__
from lib.banner import print_server_banner

TRACKING_LOG_FILE = CONFIG_DIR / "tracking.log"

class TrackingHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass # Suppress default logging

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/track"):
            qs = parse_qs(parsed.query)
            target = qs.get("t", [""])[0]
            sid = qs.get("id", [""])[0]
            if target:
                ts = datetime.now().isoformat()
                log_entry = json.dumps({
                    "timestamp": ts,
                    "target": target,
                    "id": sid,
                    "ip": self.client_address[0],
                    "user_agent": self.headers.get('User-Agent', '')
                })
                try:
                    with open(TRACKING_LOG_FILE, "a") as f:
                        f.write(log_entry + "\n")
                except Exception:
                    pass
            
            self.send_response(200)
            self.send_header('Content-type', 'image/gif')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            self.wfile.write(b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;')
            return
        
        self.send_response(404)
        self.end_headers()


class SMTPSession:

    def __init__(self, client_sock, addr, server):
        self.sock = client_sock
        self.addr = addr
        self.server = server
        self.client_id = f"{addr[0]}:{addr[1]}"
        self.mail_from = ""
        self.rcpt_to: List[str] = []
        self.last_relay_error = ""

    def run(self):
        cfg = self.server.config
        logger = cfg.logger
        logger.info(f"[{self.client_id}] New connection")

        self._send(f"220 MailSpoof-{__version__} SMTP Server Ready")

        while self.server.running:
            try:
                data = self._recv_line()
                if not data:
                    break
                if not self._handle_command(data.strip(), logger):
                    break
            except socket.timeout:
                break
            except Exception as exc:
                logger.error(f"[{self.client_id}] Error: {exc}")
                break

        self.sock.close()
        logger.info(f"[{self.client_id}] Disconnected")

    def _recv_line(self) -> str:
        buf = b""
        while True:
            chunk = self.sock.recv(1)
            if not chunk:
                return ""
            buf += chunk
            if buf.endswith(b"\r\n"):
                return buf.decode("utf-8", errors="ignore")

    def _recv_data(self) -> str:
        chunks: List[str] = []
        while True:
            part = self.sock.recv(4096).decode("utf-8", errors="ignore")
            chunks.append(part)
            if "\r\n.\r\n" in part:
                break
        return "".join(chunks).split("\r\n.\r\n")[0]

    def _send(self, text: str):
        self.sock.sendall(f"{text}\r\n".encode())

    def _handle_command(self, cmd: str, logger) -> bool:
        upper = cmd.upper()

        if upper.startswith("EHLO") or upper.startswith("HELO"):
            self._send(f"250-MailSpoof Hello {self.addr[0]}")
            self._send("250 HELP")

        elif upper.startswith("MAIL FROM:"):
            self.mail_from = self._extract_email(cmd)
            logger.info(f"[{self.client_id}] MAIL FROM: {self.mail_from}")
            self._send("250 OK")

        elif upper.startswith("RCPT TO:"):
            rcpt = self._extract_email(cmd)
            self.rcpt_to.append(rcpt)
            logger.info(f"[{self.client_id}] RCPT TO: {rcpt}")
            self._send("250 OK")

        elif upper == "DATA":
            self._send("354 End data with <CR><LF>.<CR><LF>")
            email_data = self._recv_data()
            self.last_relay_error = ""
            success = self._process_email(email_data, logger)
            self.server.emails_processed += 1
            if success:
                self._send("250 OK Message queued for delivery")
            else:
                err = self.last_relay_error or "Delivery failed"
                self._send(f"550 {err}")
            self.mail_from = ""
            self.rcpt_to = []

        elif upper == "QUIT":
            self._send("221 Bye")
            return False

        elif upper.startswith("RSET"):
            self.mail_from = ""
            self.rcpt_to = []
            self._send("250 OK")

        else:
            self._send("500 Command not recognized")

        return True

    @staticmethod
    def _extract_email(smtp_line: str) -> str:
        match = re.search(r"<(.+?)>", smtp_line)
        if match:
            return match.group(1)
        parts = smtp_line.split()
        return parts[-1].strip("<>").strip() if len(parts) > 1 else ""

    def _process_email(self, email_data: str, logger) -> bool:
        if not self.mail_from or not self.rcpt_to:
            return False

        successes = 0
        for rcpt in self.rcpt_to:
            if self._relay(self.mail_from, rcpt, email_data, logger):
                successes += 1

        logger.info(
            f"[{self.client_id}] Processed from={self.mail_from} "
            f"targets={len(self.rcpt_to)} success={successes}"
        )
        return successes > 0

    def _relay(self, mail_from: str, rcpt_to: str, email_data: str, logger) -> bool:
        try:
            domain = rcpt_to.split("@")[1]
        except IndexError:
            self.last_relay_error = "Invalid recipient domain"
            return False

        mx_servers = self._resolve_mx(domain, logger)
        if not mx_servers:
            self.last_relay_error = f"No MX records found for {domain}"
            logger.error(self.last_relay_error)
            return False

        for mx in mx_servers:
            try:
                with smtplib.SMTP(mx, 25, timeout=15) as server:
                    payload = f"From: {mail_from}\r\nTo: {rcpt_to}\r\n{email_data}"
                    server.sendmail(mail_from, [rcpt_to], payload.encode("utf-8"))
                logger.info(f"Relayed to {rcpt_to} via {mx}")
                return True
            except smtplib.SMTPRecipientsRefused as exc:
                err = str(exc)
                self.last_relay_error = f"Recipient refused: {err[:120]}"
                logger.warning(f"Relay via {mx} failed: {err[:200]}")
            except smtplib.SMTPResponseException as exc:
                err = f"{exc.smtp_code} {exc.smtp_error}" if hasattr(exc, "smtp_code") else str(exc)
                self.last_relay_error = f"Relay rejected: {err[:120]}"
                logger.warning(f"Relay via {mx} failed: {err[:200]}")
            except Exception as exc:
                err = str(exc)
                self.last_relay_error = f"Relay failed: {err[:120]}"
                logger.warning(f"Relay via {mx} failed: {err[:200]}")
            continue

        logger.error(f"All MX relays failed for {rcpt_to}")
        return False

    def _resolve_mx(self, domain: str, logger) -> List[str]:
        try:
            import dns.resolver
            answers = dns.resolver.resolve(domain, "MX")
            servers = [str(r.exchange).rstrip(".") for r in sorted(answers, key=lambda x: x.preference)]
            logger.debug(f"MX for {domain}: {servers}")
            return servers
        except ImportError:
            logger.warning("dnspython not available")
        except Exception as exc:
            logger.warning(f"MX lookup failed for {domain}: {exc}")

        fallbacks = [f"mail.{domain}", f"mx.{domain}", f"mx1.{domain}"]
        working = []
        for host in fallbacks:
            try:
                socket.gethostbyname(host)
                working.append(host)
            except Exception:
                pass
        return working if working else [domain]

class SMTPServer:

    def __init__(self, host: str, port: int, config: Config):
        self.host = host
        self.port = port
        self.config = config
        self.running = False
        self.connections = 0
        self.emails_processed = 0

    def _bind(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen(10)
        self.running = True

    def _serve(self):
        while self.running:
            try:
                client, addr = self.sock.accept()
                self.connections += 1
                session = SMTPSession(client, addr, self)
                t = threading.Thread(target=session.run, daemon=True)
                t.start()
            except OSError:
                if self.running:
                    raise

    def start(self):
        try:
            self._bind()
            signal.signal(signal.SIGINT, self._shutdown)

            # Start HTTP tracking server
            self.httpd = http.server.ThreadingHTTPServer(('0.0.0.0', 8080), TrackingHandler)
            self.httpd_thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
            self.httpd_thread.start()

            print_server_banner(
                self.host,
                self.port,
                str(self.config.logger.handlers[0].baseFilename),
            )
            print("  HTTP Tracking Server running on port 8080")

            self._serve()

        except PermissionError:
            print(f"[!] Permission denied on port {self.port}.")
            print(f"    Try:  mailspoof server --port 2525")
            sys.exit(1)
        except Exception as exc:
            print(f"[!] Server error: {exc}")
            sys.exit(1)
        finally:
            if hasattr(self, "sock"):
                self.sock.close()
            if hasattr(self, "httpd"):
                self.httpd.shutdown()

    def start_background(self):
        try:
            self._bind()
        except PermissionError:
            print(f"[!] Permission denied on port {self.port}.")
            sys.exit(1)
        except Exception as exc:
            print(f"[!] Server error: {exc}")
            sys.exit(1)

        srv_thread = threading.Thread(target=self._serve, daemon=True)
        srv_thread.start()
        return srv_thread

    def _shutdown(self, signum, frame):
        print(f"\n[!] Shutting down server...")
        print(f"    Connections: {self.connections}")
        print(f"    Emails processed: {self.emails_processed}")
        self.running = False
        if hasattr(self, "sock"):
            self.sock.close()
        if hasattr(self, "httpd"):
            self.httpd.shutdown()
        sys.exit(0)
