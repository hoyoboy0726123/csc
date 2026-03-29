from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import Case, User
from backend.services.email_service import EmailService
from backend.utils.logger import logger


class NotificationService:
    """
    負責逾期提醒與指派通知的排程服務。
    所有方法均為類別方法，可直接調用，無須實例化。
    """

    @classmethod
    def remind_overdue(cls, db: Session) -> List[int]:
        """
        找出逾期超過 24 小時且仍為「待處理 / 處理中」的案件，
        發信提醒承辦人及其主管，並回傳已通知的案件 ID 列表。
        """
        now = datetime.utcnow()
        threshold = now - timedelta(hours=24)

        stmt = (
            select(Case)
            .where(Case.status.in_(["待處理", "處理中"]))
            .where(Case.suggested_close_date < threshold)
            .where(Case.assignee_id.is_not(None))
        )
        overdue_cases: List[Case] = db.execute(stmt).scalars().all()
        notified_case_ids: List[int] = []

        for case in overdue_cases:
            assignee: Optional[User] = case.assignee
            if not assignee or not assignee.email:
                logger.warning(f"Case {case.id} 無有效承辦人 Email，跳過通知")
                continue

            # 組信
            subject = f"[逾期提醒] 案件 #{case.id} 已超過 24 小時未結案"
            body_text = (
                f"親愛的 {assignee.name}：\n\n"
                f"案件「{case.summary}」已逾期，請儘速處理。\n"
                f"建議結案日：{case.suggested_close_date.strftime('%Y-%m-%d')}\n"
                f"案件連結：https://ai-csm.example.com/cases/{case.id}\n\n"
                "系統自動通知，毋須回覆。"
            )
            recipients = [assignee.email]

            # 若主管 Email 存在，一併 CC
            manager_email = getattr(assignee, "manager_email", None)
            if manager_email:
                recipients.append(manager_email)

            try:
                EmailService.send(
                    to_emails=recipients,
                    subject=subject,
                    body_text=body_text,
                )
                notified_case_ids.append(case.id)
                logger.info(f"已發送逾期提醒信給案件 {case.id} 相關人員")
            except Exception as exc:
                logger.error(f"發送逾期提醒信失敗（案件 {case.id}）: {exc}")

        return notified_case_ids

    @classmethod
    def notify_assignment(cls, db: Session, case_id: int) -> bool:
        """
        當案件被指派或重派時，立即發信通知新承辦人。
        回傳 True 表示成功；False 表示失敗或無需發信。
        """
        case: Optional[Case] = db.get(Case, case_id)
        if not case or not case.assignee or not case.assignee.email:
            logger.warning(f"案件 {case_id} 無有效承辦人，無法發送指派通知")
            return False

        assignee = case.assignee
        subject = f"[新指派] 案件 #{case.id} 待處理"
        body_text = (
            f"親愛的 {assignee.name}：\n\n"
            f"您已被指派處理以下案件：\n"
            f"客戶名稱：{case.customer_name}\n"
            f"產品編號：{case.product_id}\n"
            f"摘要：{case.summary}\n"
            f"建議結案日：{case.suggested_close_date.strftime('%Y-%m-%d')}\n"
            f"案件連結：https://ai-csm.example.com/cases/{case.id}\n\n"
            "系統自動通知，祝順利！"
        )

        try:
            EmailService.send(
                to_emails=[assignee.email],
                subject=subject,
                body_text=body_text,
            )
            logger.info(f"已發送指派通知信給 {assignee.email}（案件 {case.id}）")
            return True
        except Exception as exc:
            logger.error(f"發送指派通知信失敗（案件 {case.id}）: {exc}")
            return False