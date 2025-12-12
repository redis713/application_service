from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FieldList, FormField, SelectField
from wtforms.validators import DataRequired, Regexp, Email, ValidationError
import re

categories = [
    ('', 'Выберите категорию', {'disabled selected': True}),
    ('fulltime_cat1', 'Руководители \n органов местного самоуправления'),
    ('fulltime_cat2', 'Руководители организаций'),
    ('fulltime_cat3', 'Руководители (работники) органов, уполномоченных на решение задач в области защиты населения и территорий от чрезвычайных ситуаций и (или) гражданской обороны муниципальных образований'),
    ('fulltime_cat4', 'Руководители (работники) структурных подразделений, уполномоченных на решение задач в области защиты населения и территорий от чрезвычайных ситуаций и (или) гражданской обороны в организациях'),
    ('fulltime_cat5', 'Члены комиссии по предупреждению и ликвидации чрезвычайных ситуаций и обеспечению пожарной безопасности Иркутской области'),
    ('fulltime_cat6', 'Председатели и члены комиссий по предупреждению и ликвидации чрезвычайных ситуаций и обеспечению пожарной безопасности муниципальных образований'),
    ('fulltime_cat7', 'Председатели и члены комиссий по предупреждению и ликвидации чрезвычайных ситуаций и обеспечению пожарной безопасности организаций'),
    ('fulltime_cat8', 'Руководители и специалисты единых дежурно-диспетчерских служб муниципальных образований'),
    ('fulltime_cat9', 'Руководители и специалисты дежурно-диспетчерских служб организаций'),
    ('fulltime_cat10', 'Должностные лица, входящие в состав эвакуационной комиссии Иркутской области'),
    ('fulltime_cat11', 'Должностные лица, входящие в составы эвакуационных комиссий органов местного самоуправления'),
    ('fulltime_cat12', 'Должностные лица, входящие в составы эвакоприемных комиссий органов местного самоуправления'),
    ('fulltime_cat13', 'Должностные лица, входящие в составы сборных и приемных эвакуационных пунктов, промежуточных пунктов эвакуации органов местного самоуправления'),
    ('fulltime_cat14', 'Должностные лица, входящие в составы эвакуационных комиссий организаций'),
    ('fulltime_cat15', 'Должностные лица, входящие в составы сборных и приемных эвакуационных пунктов, промежуточных пунктов эвакуации организаций'),
    ('fulltime_cat16', 'Должностные лица, входящие в состав комиссии по повышению устойчивого функционирования объектов экономики Иркутской области'),
    ('fulltime_cat17', 'Должностные лица, входящие в составы комиссий по повышению устойчивости функционирования органов местного самоуправления'),
    ('fulltime_cat18', 'Должностные лица, входящие в составы комиссий по повышению устойчивости функционирования организаций, отнесенных к категориям по гражданской обороне, а также продолжающих работу в военное время'),
    ('fulltime_cat19', 'Руководители спасательных служб муниципальных образований'),
    ('fulltime_cat20', 'Руководители спасательных служб, нештатных формирований гражданской обороны, нештатных аварийно-спасательных формирований организаций'),
    ('fulltime_cat21', 'Преподаватели учебного предмета «Основы безопасности и защиты Родины»'),
    ('fulltime_cat22', 'Преподаватели дисциплины «Безопасность жизнедеятельности»'),
    ('fulltime_cat23', 'Руководители, педагогические работники и инструкторы гражданской обороны курсов гражданской обороны муниципальных образований'),
    ('fulltime_cat24', 'Руководители, инструкторы гражданской обороны, консультанты учебно-консультационных пунктов муниципальных образований'),
    ('fulltime_cat25', 'Руководители и педагогические работники, осуществляющие обучение по дополнительным профессиональным программам в области гражданской обороны, организаций, осуществляющих образовательную деятельность по дополнительным профессиональным программам в области гражданской обороны'),
    ('fulltime_cat26', 'Руководители занятий по ГОЧС'),
    ('fulltime_fire_cat27', 'ДПП повышения квалификации для руководителей организаций, лиц, назначенных руководителем организации ответственными за обеспечение пожарной безопасности на объектах защиты, в которых могут одновременно находиться 50 и более человек, объектах защиты, отнесенных к категориям повышенной взрывопожароопасности, взрывопожароопасности, пожароопасности (30 часов)'),
    ('fulltime_fire_cat28', 'ДПП повышения квалификации для руководителей эксплуатирующих и управляющих организаций, осуществляющих хозяйственную деятельность, связанную с обеспечением пожарной безопасности на объектах защиты, лиц, назначенных ими ответственными за обеспечение пожарной безопасности (20 часов)'),
    ('fulltime_fire_cat29', 'ДПП повышения квалификации для ответственных должностных лиц, занимающих должности главных специалистов технического и производственного профиля, должностных лиц, исполняющих их обязанности, на объектах защиты, в которых могут одновременно находиться 50 и более человек, объектах защиты, отнесенных к категориям повышенной взрывопожароопасности, взрывопожароопасности, пожароопасности (30 часов)'),
    ('fulltime_fire_cat30', 'ДПП повышения квалификации для лиц, на которых возложена трудовая функция по проведению противопожарного инструктажа (18 часов)'),
    ('fulltime_fire_cat31', 'ДПП профессиональной переподготовки для получения квалификации "Специалист по пожарной профилактике" (250 часов)'),
    ('fulltime_cat32', 'ДПП профессиональной переподготовки операторского персонала системы обеспечения вызова экстренных оперативных служб по единому номеру «112» для получения квалификации «Специалист по приему и обработке экстренных вызовов» (250 часов)'),
    ('fulltime_cat33', 'ДПП повышения квалификации «Подготовка операторского персонала системы обеспечения вызова экстренных оперативных служб по единому номеру «112» (76 часов)'),
    ('distance_cat1', 'Заочная категория 1'),
    ('distance_cat2', 'Заочная категория 2'),
    ('distance_cat3', 'Заочная категория 3')
]

NAME_REGEX = r"^[А-ЯЁ][а-яё]+(?:[- ][А-ЯЁ][а-яё]+)*$"
INN_REGEX = r'\d{10}'
OGRN_REGEX = r'\d{13}'
KPP_REGEX = r'\d{9}'
SNILS_REGEX = r'\d{11}'


def validate_fio(form, field):
    if not re.match(NAME_REGEX, field.data):
        raise ValidationError("ФИО должны начинаться с заглавной буквы и содержать только буквы, пробелы и тире!")


def validate_inn(form, field):
    if not re.match(INN_REGEX, field.data):
        raise ValidationError("ИНН должен содержать только числа, не более 10!")

def validate_ogrn(form, field):
    if not re.match(OGRN_REGEX, field.data):
        raise ValidationError("ОГРН должен содержать только числа, не более 13!")

def validate_snils(form, field):
    if not re.match(SNILS_REGEX, field.data):
        raise ValidationError("Снилс должен содержать только 11 цифр!")

def validate_kpp(form, field):
    if not re.match(KPP_REGEX, field.data):
        raise ValidationError("КПП должен содержать только 9 цифр!")

class StudentForm(FlaskForm):
    student_firstname = StringField('Имя слушателя', validators=[DataRequired(message='Имя слушателя, поле обязательно для заполнения'), validate_fio])
    student_lastname = StringField('Фамилия слушателя',
                                    validators=[DataRequired(message='Фамилия слушателя, поле обязательно для заполнения'), validate_fio])
    student_patronymic = StringField('Отчество слушателя',
                                   validators=[validate_fio])
    student_birthdate = StringField('Дата рождения', validators=[
        DataRequired(message='Укажите дату рождения')
    ])
    citizenship = StringField('Гражданство', validators=[
        DataRequired(message='Поле Гражданство обязательно')
    ])
    education = StringField('Образование', validators=[
        DataRequired(message='Поле Образование обязательно')
    ])
    institute_name = StringField('Полное наименование образовательного учреждения', validators=[
        DataRequired(message='Поле Полное наименование образовательного учреждения обязательно')
    ])
    diploma_seriesnumber = StringField('Серия и номер диплома', validators=[
        DataRequired(message='Поле Серия и номер диплома обязательно')
    ])
    diploma_date = StringField('Дата выдачи диплома', validators=[
        DataRequired(message='Поле Дата выдачи диплома обязательно')
    ])
    diploma_lastname = StringField('Фамилия, указанная в дипломе', validators=[
        DataRequired(message='Поле Фамилия, указанная в дипломе обязательно')
    ])
    snils = StringField('Номер СНИЛС', validators=[
        DataRequired(message='Поле Номер СНИЛС обязательно'),
        validate_snils
    ])
    student_position = StringField('Должность', validators=[
        DataRequired(message='Поле Должность обязательно')
    ])
    student_category = SelectField('Категория обучения',
                                   choices=categories,
                                   validators=[DataRequired(message='Выберите категорию обучения')]
                                   )
    start_date = StringField('Дата начала обучения', validators=[
        DataRequired(message='Укажите дату начала обучения')
    ])
    end_date = StringField('Дата окончания обучения', validators=[
        DataRequired(message='Укажите дату окончания обучения')
    ])
    student_telephone = StringField('Телефон (обязательно)',
                            validators=[DataRequired(message='Телефон, поле обязательно для заполнения'),
                                        Regexp(r'^(\+7|8)\d{10}$', message='Неверный формат телефона')])
    diploma_delivery = SelectField('Способ получения диплома',
                                   choices=[
                                       ('', 'Выберите способ получения', {'disabled selected': True}),
                                       ('personal', 'Лично'),
                                       ('mail', 'По почте')
                                   ],
                                   validators=[DataRequired(message='Выберите способ получения диплома')])
    delivery_address = StringField('Адрес доставки',
                                   validators=[
                                       DataRequired(message='Укажите адрес доставки')
                                   ])

    student_email = StringField('Email', validators=[
        DataRequired(message='Поле Email обязательно'),
        Email(message='Неверный формат email')
    ])



class ApplicationForm(FlaskForm):
    organization_full_name = StringField('Наименование организации (полное)', validators=[DataRequired(message='Наименование организации, поле обязательно для заполнения')])
    organization_short_name = StringField('Наименование организации (сокращенное)', validators=[
        DataRequired(message='Наименование организации сокращенное, поле обязательно для заполнения')])
    boss_firstname = StringField('Имя руководителя',
                                    validators=[DataRequired(message='Имя руководителя, поле обязательно для заполнения'), validate_fio])
    boss_lastname = StringField('Фамилия руководителя',
                           validators=[DataRequired(message='Фамилия руководителя, поле обязательно для заполнения'), validate_fio])
    boss_patronymic = StringField('Отчество руководителя',
                           validators=[validate_fio])
    doljnost_boss = StringField('должность руководителя',
                                    validators=[DataRequired(message='должность руководителя, поле обязательно для заполнения')])
    polnamochia_boss = StringField('действует на основании (указать название (наименование) документа)',
                                    validators=[DataRequired(message='действует на основании (указать название (наименование) документа), поле обязательно для заполнения')])
    ogrn = StringField('ОГРН',
                                    validators=[DataRequired(message='ОГРН, поле обязательно для заполнения'), validate_ogrn])
    inn = StringField('ИНН',
                                    validators=[DataRequired(message='ИНН, поле обязательно для заполнения'), validate_inn])
    kpp = StringField('КПП',
                                    validators=[DataRequired(message='КПП, поле обязательно для заполнения'), validate_kpp])
    bank_name = StringField('Наименование банка',
                                    validators=[DataRequired(message='Наименование банка, поле обязательно для заполнения')])
    rasch_schot = StringField('Расчетный счет',
                                    validators=[DataRequired(message='Расчетный счет, поле обязательно для заполнения')])
    bik = StringField('БИК',
                                    validators=[DataRequired(message='БИК, поле обязательно для заполнения')])
    fakt_address = StringField('Фактический адрес',
                                    validators=[DataRequired(message='Фактический адрес, поле обязательно для заполнения')])
    yur_address = StringField('Юридический адрес',
                                    validators=[DataRequired(message='Юридический адрес, поле обязательно для заполнения')])
    telephone = StringField('Телефон (обязательно)',
                                    validators=[DataRequired(message='Телефон, поле обязательно для заполнения'), Regexp(r'^(\+7|8)\d{10}$', message='Неверный формат телефона')])
    email = StringField('Адрес электронной почты (e-mail) (обязательно)',
                                    validators=[DataRequired(message='Адрес электронной почты (e-mail), поле обязательно для заполнения'), Email(message='Неверный формат email')])
    doljnost_executor = StringField('должность исполнителя',
                                    validators=[DataRequired(message='должность исполнителя, поле обязательно для заполнения')])
    fio_executor = StringField('ФИО исполнителя',
                                    validators=[DataRequired(message='ФИО исполнителя, поле обязательно для заполнения')])
    telephone_executor = StringField('телефон исполнителя',
                                    validators=[DataRequired(message='телефон исполнителя, поле обязательно для заполнения'), Regexp(r'^(\+7|8)\d{10}$', message='Неверный формат телефона')
    ])

    students = FieldList(FormField(StudentForm), min_entries=1)

    submit = SubmitField('Отправить')



