# -*- coding: utf-8 -*-
"""邮件发送服务 - 支持 SMTP 异步发送"""

import logging
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailService:
    """异步邮件发送服务"""
    
    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: int = 587,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        use_tls: bool = True,
        from_email: Optional[str] = None
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.use_tls = use_tls
        self.from_email = from_email or smtp_username
        
        # 如果配置为空，使用 Mock 模式
        self.mock_mode = not (smtp_host and smtp_username)
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """发送 HTML 邮件"""
        
        if self.mock_mode:
            logger.info(f"\n========== 邮件发送 (Mock 模式) ==========\n收件人: {to_email}\n主题: {subject}\n内容: {html_content[:200]}...\n========================================\n")
            return True
        
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.from_email
            message["To"] = to_email
            
            if text_content:
                message.attach(MIMEText(text_content, "plain", "utf-8"))
            message.attach(MIMEText(html_content, "html", "utf-8"))
            
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_username,
                password=self.smtp_password,
                use_tls=self.use_tls
            )
            
            logger.info(f"邮件发送成功: {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"邮件发送失败: {to_email}, 错误: {str(e)}")
            return False


def get_password_reset_email_html(reset_link: str, expires_in_hours: int = 1) -> str:
    """生成密码重置邮件 HTML 模板"""
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #4CAF50; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 30px 20px; background: #f9f9f9; }}
        .button {{ display: inline-block; padding: 15px 30px; background: #4CAF50; color: white; 
                   text-decoration: none; border-radius: 5px; font-weight: bold; }}
        .warning {{ color: #ff9800; font-size: 14px; margin-top: 20px; }}
        .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🦜 ParrotCare 密码重置</h1>
        </div>
        <div class="content">
            <p>您好，</p>
            <p>我们收到了您的密码重置请求。请点击下方按钮重置您的密码：</p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{reset_link}" class="button">重置密码</a>
            </p>
            <p class="warning">⚠️ 此链接将在 <strong>{expires_in_hours} 小时</strong> 后失效（约 {expires_in_hours * 60} 秒）</p>
            <p>如果您没有请求重置密码，请忽略此邮件。</p>
            <p>如果按钮无法点击，请复制以下链接到浏览器：</p>
            <p style="background: #eee; padding: 10px; word-break: break-all;">{reset_link}</p>
        </div>
        <div class="footer">
            <p>© {datetime.now().year} ParrotCare - 智能鹦鹉健康管理平台</p>
            <p>此邮件由系统自动发送，请勿回复</p>
        </div>
    </div>
</body>
</html>
"""
    return html


async def send_password_reset_email(
    email_service: EmailService,
    to_email: str,
    reset_link: str
) -> bool:
    """发送密码重置邮件"""
    
    subject = "ParrotCare 密码重置请求"
    html_content = get_password_reset_email_html(reset_link)
    text_content = f"请访问以下链接重置密码: {reset_link} (链接1小时后失效)"
    
    return await email_service.send_email(to_email, subject, html_content, text_content)
