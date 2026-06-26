from wsgiref.util import setup_testing_defaults

from docx import Document
from docxtpl import DocxTemplate

'''
doc = DocxTemplate('test.docx')
place1 = 'haha'
place2 = 'hehe'
data = [
    {'Value1': 'A1', 'Value2': 'B1', 'Value3': 'C1\n Value33', 'Value4': 'D1'},
    {'Value1': 'A2', 'Value2': 'B2', 'Value3': 'C2', 'Value4': 'D2'},
    {'Value1': 'A3', 'Value2': 'B3', 'Value3': 'C3', 'Value4': 'D3'}
    # Добавьте сколько угодно строк в таблицу в соответствии с вашими данными
]

context = {'place1': place1, 'place2': place2, 'data': data}

doc.render(context)
doc.save('newdoc.docx')
'''


categories = {
    'fulltime_cat1': 'Руководители органов местного самоуправления',
    'fulltime_cat2': 'Руководители организаций',
    'fulltime_cat3': 'Руководители (работники) органов, уполномоченных на решение задач в области защиты населения и территорий от чрезвычайных ситуаций и (или) гражданской обороны муниципальных образований',
    'fulltime_cat4': 'Руководители (работники) структурных подразделений, уполномоченных на решение задач в области защиты населения и территорий от чрезвычайных ситуаций и (или) гражданской обороны в организациях',
    'fulltime_cat5': 'Члены комиссии по предупреждению и ликвидации чрезвычайных ситуаций и обеспечению пожарной безопасности Иркутской области',
    'fulltime_cat6': 'Председатели и члены комиссий по предупреждению и ликвидации чрезвычайных ситуаций и обеспечению пожарной безопасности муниципальных образований',
    'fulltime_cat7': 'Председатели и члены комиссий по предупреждению и ликвидации чрезвычайных ситуаций и обеспечению пожарной безопасности организаций',
    'fulltime_cat8': 'Руководители и специалисты единых дежурно-диспетчерских служб муниципальных образований',
    'fulltime_cat9': 'Руководители и специалисты дежурно-диспетчерских служб организаций',
    'fulltime_cat10': 'Должностные лица, входящие в состав эвакуационной комиссии Иркутской области',
    'fulltime_cat11': 'Должностные лица, входящие в составы эвакуационных комиссий органов местного самоуправления',
    'fulltime_cat12': 'Должностные лица, входящие в составы эвакоприемных комиссий органов местного самоуправления',
    'fulltime_cat13': 'Должностные лица, входящие в составы сборных и приемных эвакуационных пунктов, промежуточных пунктов эвакуации органов местного самоуправления',
    'fulltime_cat14': 'Должностные лица, входящие в составы эвакуационных комиссий организаций',
    'fulltime_cat15': 'Должностные лица, входящие в составы сборных и приемных эвакуационных пунктов, промежуточных пунктов эвакуации организаций',
    'fulltime_cat16': 'Должностные лица, входящие в состав комиссии по повышению устойчивого функционирования объектов экономики Иркутской области',
    'fulltime_cat17': 'Должностные лица, входящие в составы комиссий по повышению устойчивости функционирования органов местного самоуправления',
    'fulltime_cat18': 'Должностные лица, входящие в составы комиссий по повышению устойчивости функционирования организаций, отнесенных к категориям по гражданской обороне, а также продолжающих работу в военное время',
    'fulltime_cat19': 'Руководители спасательных служб муниципальных образований',
    'fulltime_cat20': 'Руководители спасательных служб, нештатных формирований гражданской обороны, нештатных аварийно-спасательных формирований организаций',
    'fulltime_cat21': 'Преподаватели учебного предмета «Основы безопасности и защиты Родины»',
    'fulltime_cat22': 'Преподаватели дисциплины «Безопасность жизнедеятельности»',
    'fulltime_cat23': 'Руководители, педагогические работники и инструкторы гражданской обороны курсов гражданской обороны муниципальных образований',
    'fulltime_cat24': 'Руководители, инструкторы гражданской обороны, консультанты учебно-консультационных пунктов муниципальных образований',
    'fulltime_cat25': 'Руководители и педагогические работники, осуществляющие обучение по дополнительным профессиональным программам в области гражданской обороны, организаций, осуществляющих образовательную деятельность по дополнительным профессиональным программам в области гражданской обороны',
    'fulltime_cat26': 'Руководители занятий по ГОЧС',
    'fulltime_fire_cat27': 'ДПП повышения квалификации для руководителей организаций, лиц, назначенных руководителем организации ответственными за обеспечение пожарной безопасности на объектах защиты, в которых могут одновременно находиться 50 и более человек, объектах защиты, отнесенных к категориям повышенной взрывопожароопасности, взрывопожароопасности, пожароопасности (30 часов)',
    'fulltime_fire_cat28': 'ДПП повышения квалификации для руководителей эксплуатирующих и управляющих организаций, осуществляющих хозяйственную деятельность, связанную с обеспечением пожарной безопасности на объектах защиты, лиц, назначенных ими ответственными за обеспечение пожарной безопасности (20 часов)',
    'fulltime_fire_cat29': 'ДПП повышения квалификации для ответственных должностных лиц, занимающих должности главных специалистов технического и производственного профиля, должностных лиц, исполняющих их обязанности, на объектах защиты, в которых могут одновременно находиться 50 и более человек, объектах защиты, отнесенных к категориям повышенной взрывопожароопасности, взрывопожароопасности, пожароопасности (30 часов)',
    'fulltime_fire_cat30': 'ДПП повышения квалификации для лиц, на которых возложена трудовая функция по проведению противопожарного инструктажа (18 часов)',
    'fulltime_fire_cat31': 'ДПП профессиональной переподготовки для получения квалификации "Специалист по пожарной профилактике" (250 часов)',
    'fulltime_cat32': 'ДПП профессиональной переподготовки операторского персонала системы обеспечения вызова экстренных оперативных служб по единому номеру «112» для получения квалификации «Специалист по приему и обработке экстренных вызовов» (250 часов)',
    'fulltime_cat33': 'ДПП повышения квалификации «Подготовка операторского персонала системы обеспечения вызова экстренных оперативных служб по единому номеру «112» (76 часов)',
    'distance_cat1': 'Заочная категория 1',
    'distance_cat2': 'Заочная категория 2',
    'distance_cat3': 'Заочная категория 3'
}

delivery = {'personal': 'Лично', 'mail': 'По почте'}
#fire_document = {'diploma': 'Диплом', 'certificate': 'Удостоверение'}

templates = {'112.docx': [''],
             'antiterror.docx': ['']
             }

def format_form(form_data):
    data = {}
    organization = {
        'organization_full_name': form_data.organization_full_name.data,
        'organization_short_name': form_data.organization_short_name.data,
        'boss_firstname': form_data.boss_firstname.data,
        'boss_lastname': form_data.boss_lastname.data,
        'boss_patronymic': form_data.boss_patronymic.data,
        'doljnost_boss': form_data.doljnost_boss.data,
        'polnamochia_boss': form_data.polnamochia_boss.data,
        'ogrn': form_data.ogrn.data,
        'inn': form_data.inn.data,
        'kpp': form_data.kpp.data,
        'bank_name': form_data.bank_name.data,
        'rasch_schot': form_data.rasch_schot.data,
        'bik': form_data.bik.data,
        'fakt_address': form_data.fakt_address.data,
        'yur_address': form_data.yur_address.data,
        'telephone': form_data.telephone.data,
        'email': form_data.email.data,
        'doljnost_executor': form_data.doljnost_executor.data,
        'fio_executor': form_data.fio_executor.data,
        'telephone_executor': form_data.telephone_executor.data
    }
    students = []
    
    for student in form_data.students:
        students.append({
            'firstname': student.student_firstname.data,
            'lastname': student.student_lastname.data,
            'patronymic': student.student_patronymic.data,
            'birthdate': student.student_birthdate.data,
            'citizenship': student.citizenship.data,
            'education': student.education.data,
            'institute_name': student.institute_name.data,
            'diploma_seriesnumber': student.diploma_seriesnumber.data,
            'diploma_date': student.diploma_date.data,
            'diploma_lastname': student.diploma_lastname.data,
            'snils': student.snils.data,
            'student-position': student.position.data,
            'student_category': student.category.data,
            # 'fire_safety_document_type': student.fire_safety_document_type.data,
            # 'fire_institution': student.fire_institution.data,
            # 'fire_series': student.fire_series.data,
            # 'fire_number': student.fire_number.data,
            # 'fire_date': student.fire_date.data,
            'student_telephone': student.student_telephone.data,
            'email': student.student_email.data,
            'phone': student.student_telephone.data
        })

def generate_docx(form_data):
    print('Это из gen_docx: ', form_data)
    context = {}

    students_data = []

    print('students: ', form_data.students)

    context['organization_name'] = form_data.organization_full_name.data + ', ' + form_data.organization_short_name.data
    context['fio_boss'] = form_data.boss_lastname.data + ' ' + form_data.boss_firstname.data + ' ' + form_data.boss_patronymic.data + ', ' + form_data.doljnost_boss.data + form_data.doljnost_boss.data + form_data.polnamochia_boss.data
    context['ogrn'] = 'ОГРН: ' + form_data.ogrn.data +'\n' + 'ИНН: ' + form_data.inn.data + '\n' + 'КПП: ' + form_data.kpp.data + '\n' + 'Банк: ' + form_data.bank_name.data + '\n' + 'р/с: ' + form_data.rasch_schot.data + '\n' + 'БИК: ' + form_data.bik.data
    context['fakt_address'] = form_data.fakt_address.data
    context['yur_address'] = form_data.yur_address.data
    context['telephone'] = form_data.telephone.data
    context['email'] = form_data.email.data
    context['doljnost_executor'] = form_data.doljnost_executor.data + form_data.fio_executor.data + form_data.telephone_executor.data


    context['people_kol'] = len(form_data.students)

    new_student = {}
    count = 1
    #print(students)
    for student in form_data.students:
        new_student.clear()

        new_student['category'] = ''
        new_student['date'] = ''

        new_student['num'] = count
        print(student.student_lastname.data)
        new_student['name'] = student.student_lastname.data + ' ' + student.student_firstname.data + ' ' + student.student_patronymic.data + '\n\n' + student.student_birthdate.data + '\n\n' + student.citizenship.data
        print(new_student['name'])

        new_student['education'] = student.education.data + '\n\n' +student.institute_name.data + ' ' + student.diploma_seriesnumber.data + ', ' + student.diploma_date.data + '\n\n' + student.diploma_lastname.data + '\n\n' + student.snils.data
        new_student['position'] = student.student_position.data


        start_dates = []
        end_dates = []

        for category in student.student_categories:
            new_student['category'] += categories[category.category.data] + '\n\n'

            start_dates.append(category.start_date.data)
            end_dates.append(category.end_date.data)


        for i in range(len(start_dates)):
            new_student['date']  += str(start_dates[i]) + ' - ' + str(end_dates[i])


        new_student['phone'] =  student.student_telephone.data + '\n\n' + delivery[student.diploma_delivery.data]
        if student.diploma_delivery.data == 'mail':
            new_student['phone'] += '\n\n' + student.delivery_address.data

        new_student['email'] = student.student_email.data

       # if 'fire' in student['category']:
           # new_student['fire'] = student['fire_institution'] + '\n\n'
            #new_student['fire'] += fire_document[student['fire_safety_document_type']]
            #new_student['fire'] += '\n\n'
            #if new_student['fire_safety_document_type'] == 'diploma':
             #   new_student['fire'] += student['fire_series']
              #  new_student['fire'] += ' '
            #new_student['fire'] += student['fire_number']
            #new_student['fire'] += '\n'
            #new_student['fire'] += student['fire_date']

        #print(students_data)
        students_data.append(new_student.copy())
        count += 1

    #print(students_data)

    context['data'] = students_data

    #print(context)

    doc = DocxTemplate('docx_templates/gochs-dist.docx')
    doc.render(context)
    doc.save('newdoc.docx')

    #print('конец генератора')
    return 'newdoc.docx'


#generate_docx({'organization': {'org_name': 'sfsf', 'director_name': 'sfafsa', 'actual_address': 'aaaaaaaaaa', 'legal_address': 'ffffffffff', 'org_phone': '222222222222', 'org_email': 'dputiata@gmail.com', 'org_requisites': 'f2fqfq\n2f1ff', 'executor_name': 'ffffffffff'}, 'students': [{'firstname': 'Светлана', 'lastname': 'Шленникова', 'patronymic': 'Николаевна', 'birthdate': '2025-02-02', 'citizenship': 'fsdfsf', 'education': 'dsdsd', 'institute_name': 'sfsf', 'diploma_seriesnumber': 'sfsfsf 4545', 'diploma_date': '2025-02-01', 'diploma_lastname': 'ывыв', 'snils': '23424234', 'position': 'роро', 'category': 'fulltime_cat6', 'fire_safety_document_type': None, 'certificate_institution': '', 'diploma_series': '', 'certificate_number': '', 'certificate_date': '', 'begindate': '2025-01-30', 'enddate': '2025-01-31', 'phone': '9842709405', 'diploma_delivery': 'mail', 'delivery_address': 'hhhhhhhhhhhhhhh', 'email': 'schlennikowa.sveta@yandex.ru'}]})
