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
    DRAFT = "draft"                     # Черновик (документ сформирован, ожидает подписания и скана)
    SUBMITTED = "submitted"             # Заявка подана со сканом, ожидает проверки методистом
    IN_REVIEW = "in_review"             # В обработке
    ACCEPTED = "accepted"               # Принята (включена в приказ на зачисление)
    NEEDS_CORRECTION = "correction"     # Требует исправления/уточнения данных
    REJECTED = "rejected"               # Отклонена

    @classmethod
    def label(cls, value: str) -> str:
        labels = {
            cls.DRAFT: "Черновик (ожидает скан с подписью)",
            cls.SUBMITTED: "Подана (на проверке)",
            cls.IN_REVIEW: "В обработке методистом",
            cls.ACCEPTED: "Принята",
            cls.NEEDS_CORRECTION: "Требует уточнений",
            cls.REJECTED: "Отклонена",
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

