import enum

class StudyForm(str, enum.Enum):
    DISTANT = "distant"
    OCHNO = "ochno"

    @classmethod
    def label(cls, value: str) -> str:
        labels = {
            cls.DISTANT: "Дистанционное обучение",
            cls.OCHNO: "Очно-заочное обучение",
        }
        return labels.get(value, value)


class TrainingDirection(str, enum.Enum):
    GOCHS = "gochs"
    FIRE = "fire"
    CALL112 = "112"
    ANTITERROR = "antiterror"
    SPECIALIST = "specialist"

    @classmethod
    def label(cls, value: str) -> str:
        labels = {
            cls.GOCHS: "Гражданская оборона и защита от ЧС",
            cls.FIRE: "Пожарная безопасность",
            cls.CALL112: "Система 112",
            cls.ANTITERROR: "Антитеррористическая защищенность",
            cls.SPECIALIST: "Специалист по гражданской обороне (250 часов)",
        }
        return labels.get(value, value)


class ApplicationStatus(str, enum.Enum):
    IN_REVIEW = "in_review"             # Принята в работу, ожидает рассмотрения договорным отделом
    APPROVED = "approved"               # Одобрена договорным отделом (ожидает загрузки скана)
    NEEDS_CORRECTION = "correction"     # Требует доработки (возвращена с замечаниями)
    SUBMITTED = "submitted"             # Скан заявления прикреплен, передана в учебный отдел
    ACCEPTED = "accepted"               # Принята (включена в приказ на зачисление)
    REJECTED = "rejected"               # Отклонена
    DRAFT = "draft"                     # Черновик (для обратной совместимости)

    @classmethod
    def label(cls, value: str) -> str:
        labels = {
            cls.IN_REVIEW: "На рассмотрении договорным отделом",
            cls.APPROVED: "Одобрена (ожидает скан)",
            cls.NEEDS_CORRECTION: "Требует доработки",
            cls.SUBMITTED: "Скан прикреплен (на зачислении)",
            cls.ACCEPTED: "Принята",
            cls.REJECTED: "Отклонена",
            cls.DRAFT: "На рассмотрении договорным отделом",
        }
        return labels.get(value, value)


class DeliveryType(str, enum.Enum):
    PERSONAL = "personal"
    MAIL = "mail"

    @classmethod
    def label(cls, value: str) -> str:
        labels = {
            cls.PERSONAL: "Лично в УМЦ",
            cls.MAIL: "Почтой России",
        }
        return labels.get(value, value)


FIRE_DOCUMENT_CHOICES = [
    ("", "Выберите документ о квалификации в области пожарной безопасности"),
    ("specialty", "1) Диплом по специальности «Пожарная безопасность» или направлению подготовки «Техносферная безопасность»"),
    ("retraining", "2) Диплом по профессиональной переподготовке с получением квалификации «Специалист по противопожарной профилактике»"),
    ("competencies", "3) Диплом и приложение к диплому, подтверждающее получение профессиональных компетенций в области пожарной безопасности (в рамках СПО / ВО)")
]

FIRE_DOCUMENT_LABELS = {
    "specialty": "Диплом по специальности «Пожарная безопасность» или направлению подготовки «Техносферная безопасность»",
    "retraining": "Диплом по профессиональной переподготовке с получением квалификации «Специалист по противопожарной профилактике»",
    "competencies": "Диплом и приложение к диплому, подтверждающее получение профессиональных компетенций в области пожарной безопасности, приобретенных в период получения среднего профессионального образования и (или) высшего образования",
}

