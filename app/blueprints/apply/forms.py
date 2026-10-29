import re
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import (
    StringField,
    SubmitField,
    FieldList,
    FormField,
    SelectField,
    DateField,
    HiddenField,
)
from wtforms.validators import DataRequired, Email, Optional, ValidationError, Length
from app.constants import FIRE_DOCUMENT_CHOICES

NAME_REGEX = r"^[А-ЯЁ][а-яёА-ЯЁ'’`]*(?:[- ][а-яёА-ЯЁ'’`]+)*$"

def validate_fio(form, field):
    if field.data and not re.match(NAME_REGEX, field.data.strip()):
        raise ValidationError("Должно начинаться с заглавной русской буквы и содержать только русские буквы, пробелы или дефис.")

def validate_inn(form, field):
    if field.data:
        val = re.sub(r"\D", "", field.data)
        if len(val) not in (10, 12):
            raise ValidationError("ИНН должен содержать 10 цифр (для юрлиц) или 12 цифр (для ИП).")

def validate_ogrn(form, field):
    if field.data:
        val = re.sub(r"\D", "", field.data)
        if len(val) not in (13, 15):
            raise ValidationError("ОГРН должен содержать 13 цифр (для юрлиц) или 15 цифр (ОГРНИП).")

def validate_kpp(form, field):
    if field.data:
        val = re.sub(r"\D", "", field.data)
        if len(val) != 9:
            raise ValidationError("КПП должен состоять из 9 цифр.")

def validate_snils(form, field):
    if field.data:
        val = re.sub(r"\D", "", field.data)
        if len(val) != 11:
            raise ValidationError("СНИЛС должен содержать ровно 11 цифр (например, 123-456-789 01).")

def validate_phone(form, field):
    if field.data:
        val = re.sub(r"\D", "", field.data)
        if len(val) != 11 or val[0] not in ("7", "8"):
            raise ValidationError("Укажите корректный номер телефона (например, +7 999 123-45-67).")

def validate_bik(form, field):
    if field.data:
        val = re.sub(r"\D", "", field.data)
        if len(val) != 9:
            raise ValidationError("БИК должен содержать ровно 9 цифр.")

def validate_account_number(form, field):
    if field.data:
        val = re.sub(r"\D", "", field.data)
        if len(val) != 20:
            raise ValidationError("Расчетный счет должен содержать ровно 20 цифр.")


class CategoryForm(FlaskForm):
    class Meta:
        csrf = False  # CSRF контролируется главной формой

    category = SelectField(
        "Категория обучения",
        validators=[DataRequired(message="Выберите категорию обучения")]
    )
    start_date = DateField(
        "Дата начала обучения",
        format=["%Y-%m-%d", "%d.%m.%Y"],
        validators=[DataRequired(message="Укажите дату начала")]
    )
    end_date = DateField(
        "Дата окончания обучения",
        format=["%Y-%m-%d", "%d.%m.%Y"],
        validators=[DataRequired(message="Укажите дату окончания")]
    )

    def validate_end_date(self, field):
        if self.start_date.data and field.data:
            if field.data < self.start_date.data:
                raise ValidationError("Дата окончания не может быть раньше даты начала.")


class StudentForm(FlaskForm):
    class Meta:
        csrf = False

    student_lastname = StringField("Фамилия", validators=[DataRequired(message="Укажите фамилию"), validate_fio, Length(max=100)])
    student_firstname = StringField("Имя", validators=[DataRequired(message="Укажите имя"), validate_fio, Length(max=100)])
    student_patronymic = StringField("Отчество", validators=[Optional(), validate_fio, Length(max=100)])
    student_birthdate = DateField("Дата рождения", format=["%Y-%m-%d", "%d.%m.%Y"], validators=[DataRequired(message="Укажите дату рождения")])
    citizenship = StringField("Гражданство", default="РФ", validators=[DataRequired(message="Укажите гражданство"), Length(max=100)])

    student_position = StringField("Должность в организации", validators=[DataRequired(message="Укажите должность"), Length(max=255)])

    # Базовое образование
    education = SelectField(
        "Уровень базового образования",
        choices=[
            ("", "Выберите уровень образования"),
            ("Высшее образование", "Высшее образование"),
            ("Среднее профессиональное", "Среднее профессиональное образование"),
            ("Неоконченное высшее (студент)", "Неоконченное высшее (справка об обучении)")
        ],
        validators=[DataRequired(message="Выберите уровень образования")]
    )
    institute_name = StringField("Наименование учебного заведения", validators=[DataRequired(message="Укажите учебное заведение"), Length(max=500)])
    diploma_seriesnumber = StringField("Серия и номер диплома", validators=[Optional(), Length(max=100)])
    diploma_date = DateField("Дата выдачи диплома", format=["%Y-%m-%d", "%d.%m.%Y"], validators=[Optional()])
    diploma_lastname = StringField("Фамилия в дипломе", validators=[Optional(), Length(max=100)])

    def validate_diploma_seriesnumber(self, field):
        if self.education.data in ("Высшее образование", "Среднее профессиональное"):
            if not field.data or not field.data.strip():
                raise ValidationError("Укажите серию и номер диплома")

    def validate_diploma_date(self, field):
        if self.education.data in ("Высшее образование", "Среднее профессиональное"):
            if not field.data:
                raise ValidationError("Укажите дату выдачи диплома")

    def validate_diploma_lastname(self, field):
        if self.education.data in ("Высшее образование", "Среднее профессиональное"):
            if not field.data or not field.data.strip():
                raise ValidationError("Укажите фамилию в дипломе")

    # Поля квалификации в области пожарной безопасности (заполняются при направлении 'fire')
    fire_safety_document_type = SelectField(
        "Основание пожарного образования",
        choices=FIRE_DOCUMENT_CHOICES,
        validators=[Optional()]
    )
    fire_institution = StringField("Образовательное учреждение, выдавшее документ", validators=[Optional(), Length(max=500)])
    fire_series = StringField("Серия документа", validators=[Optional(), Length(max=50)])
    fire_number = StringField("Номер документа", validators=[Optional(), Length(max=50)])
    fire_date = DateField("Дата выдачи документа", format=["%Y-%m-%d", "%d.%m.%Y"], validators=[Optional()])

    snils = StringField("СНИЛС", validators=[DataRequired(message="Укажите СНИЛС"), validate_snils])
    student_telephone = StringField("Телефон слушателя", validators=[DataRequired(message="Укажите телефон"), validate_phone, Length(max=50)])
    student_email = StringField("Электронная почта слушателя", validators=[DataRequired(message="Укажите email"), Email(message="Неверный формат email"), Length(max=100)])

    # Способ получения удостоверения
    diploma_delivery = SelectField(
        "Способ получения документа",
        choices=[
            ("personal", "Лично в учебном центре"),
            ("mail", "Почтой России")
        ],
        default="personal",
        validators=[DataRequired()]
    )
    delivery_address = StringField("Адрес почтовой доставки", validators=[Optional(), Length(max=500)])

    # Категории обучения слушателя
    student_categories = FieldList(FormField(CategoryForm), min_entries=1)


class ApplicationForm(FlaskForm):
    # Данные организации
    organization_full_name = StringField("Полное наименование организации", validators=[DataRequired(message="Укажите полное наименование организации"), Length(max=500)])
    organization_short_name = StringField("Краткое наименование организации", validators=[DataRequired(message="Укажите краткое наименование"), Length(max=255)])

    inn = StringField("ИНН", validators=[DataRequired(message="Укажите ИНН"), validate_inn, Length(max=20)])
    kpp = StringField("КПП", validators=[Optional(), validate_kpp, Length(max=20)])
    ogrn = StringField("ОГРН / ОГРНИП", validators=[DataRequired(message="Укажите ОГРН"), validate_ogrn, Length(max=20)])

    bank_name = StringField("Наименование банка", validators=[DataRequired(message="Укажите банк"), Length(max=255)])
    bik = StringField("БИК", validators=[DataRequired(message="Укажите БИК"), validate_bik, Length(max=20)])
    rasch_schot = StringField("Расчетный счет", validators=[DataRequired(message="Укажите расчетный счет"), validate_account_number, Length(max=30)])

    boss_lastname = StringField("Фамилия руководителя", validators=[DataRequired(message="Укажите фамилию руководителя"), validate_fio, Length(max=100)])
    boss_firstname = StringField("Имя руководителя", validators=[DataRequired(message="Укажите имя руководителя"), validate_fio, Length(max=100)])
    boss_patronymic = StringField("Отчество руководителя", validators=[Optional(), validate_fio, Length(max=100)])
    doljnost_boss = StringField("Должность руководителя", validators=[DataRequired(message="Укажите должность руководителя"), Length(max=255)])
    polnamochia_boss = StringField("Действует на основании", default="Устава", validators=[DataRequired(message="Укажите основание полномочий"), Length(max=255)])

    yur_address = StringField("Юридический адрес", validators=[DataRequired(message="Укажите юридический адрес"), Length(max=500)])
    fakt_address = StringField("Фактический адрес", validators=[DataRequired(message="Укажите фактический адрес"), Length(max=500)])

    telephone = StringField("Телефон организации", validators=[DataRequired(message="Укажите телефон организации"), validate_phone, Length(max=50)])
    email = StringField("Email организации", validators=[DataRequired(message="Укажите email"), Email(message="Неверный email"), Length(max=100)])

    # Исполнитель (составитель заявки)
    fio_executor = StringField("ФИО исполнителя", validators=[DataRequired(message="Укажите ФИО исполнителя"), Length(max=255)])
    doljnost_executor = StringField("Должность исполнителя", validators=[DataRequired(message="Укажите должность исполнителя"), Length(max=255)])
    telephone_executor = StringField("Телефон исполнителя", validators=[DataRequired(message="Укажите телефон исполнителя"), validate_phone, Length(max=50)])

    # Список слушателей
    students = FieldList(FormField(StudentForm), min_entries=1)

    # Кнопки
    download_docx = SubmitField("Скачать официальное заявление (.docx)")
    save_draft = SubmitField("Сохранить черновик и получить бланк")


class ScanUploadForm(FlaskForm):
    scan_file = FileField(
        "Скан-копия подписанного и заверенного печатью заявления (PDF, JPG, PNG)",
        validators=[
            FileRequired(message="Пожалуйста, выберите файл со сканом заявления"),
            FileAllowed(["pdf", "jpg", "jpeg", "png", "tif", "tiff"], "Разрешены только документы форматов PDF, JPG, PNG, TIFF")
        ]
    )
    submit_scan = SubmitField("Прикрепить скан и окончательно отправить заявку")
