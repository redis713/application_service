#from smtpd import program

from flask import Flask, render_template, request, flash, send_file, redirect, url_for
from flask_wtf import CSRFProtect
from forms import ApplicationForm
from docxgenerator import generate_docx
from config import Config
from models import db, Application, Listener, Organization, Person, ListenerProgram, Program

app = Flask(__name__)

#app.config['SECRET_KEY'] = 'superfrog'
app.config.from_object(Config)
csrf = CSRFProtect(app)

db.init_app(app)
with app.app_context():
    db.create_all()


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/distant")
def distant():
    return render_template("distant.html")

@app.route("/ochnoe")
def ochnoe():
    return render_template("ochka.html")

@app.route("/distant/gochs",methods=["GET","POST"])
def gochs():
    form = ApplicationForm()
    #if request.method == "POST":
    #    print(111)
    #    print(request.form.get('ogrn'))
    if form.validate_on_submit():
        print('Мы прошли проверку!!!')
        organization = Organization.query.filter_by(ogrn=form.ogrn.data).first()
        if not organization:
            print('Мы создаем организацию!!!')
            organization = Organization(
                organization_full_name=form.organization_full_name.data,
                organization_short_name=form.organization_short_name.data,
                fio_boss=form.fio_boss.data,
                doljnost_boss=form.doljnost_boss.data,
                polnamochia_boss=form.polnamochia_boss.data,
                ogrn=form.ogrn.data,
                inn=form.inn.data,
                kpp=form.kpp.data,
                bank_name=form.bank_name.data,
                rasch_schot=form.rasch_schot.data,
                bik=form.bik.data,
                fakt_address=form.fakt_address.data,
                yur_address=form.yur_address.data,
                telephone=form.telephone.data,
                email=form.email.data,
                doljnost_executor=form.doljnost_executor.data,
                fio_executor=form.fio_executor.data,
                telephone_executor=form.telephone_executor.data
            )
            db.session.add(organization)
            print('Добавили организацию!!!')

        application = Application(
            organization = organization,
            status = 'Новая'
        )
        db.session.add(application)
        print('Добавили заявку!!!')

        for sluhach in form.students:
            print(sluhach.student_lastname.data)
            person = Person(
                firstname = sluhach.student_firstname.data,
                lastname = sluhach.student_lastname.data,
                patronymic = sluhach.student_patronymic.data,
                birthdate = sluhach.student_birthdate.data,
                citizenship = sluhach.citizenship.data,
                education = sluhach.education.data,
                institute_name = sluhach.institute_name.data,
                diploma_seriesnumber = sluhach.diploma_seriesnumber.data,
                diploma_date = sluhach.diploma_date.data,
                diploma_lastname = sluhach.diploma_lastname.data,
                snils = sluhach.snils.data,
                student_telephone = sluhach.student_telephone.data,
                fire_safety_document_type = "xt yb,elm",
                certificate_institution = 'tydyt',
                diploma_series = 'tgyjyuiuyi',
                certificate_number = 'tgjjyjjytj',
                certificate_date = 'zsffdhggyu',
                email = sluhach.student_email.data,
                phone = sluhach.student_telephone.data
            )
            db.session.add(person)

            listener = Listener(
                application = application,
                person = person,
                position = sluhach.student_position.data,
                diploma_delivery = sluhach.diploma_delivery.data,
                delivery_address = sluhach.delivery_address.data
            )
            db.session.add(listener)

            program = Program.query.get(1)

            lp = ListenerProgram(
                listener = listener,
                program = program,
                start_date = sluhach.start_date.data,
                end_date = sluhach.end_date.data
            )

            db.session.add(lp)

        db.session.commit()
        flash("Заявка успешно создана!", "success")
        return redirect(url_for("gochs"))

    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{error}', 'error')
    return render_template("gochs.html", form=form)

@app.route("/download-docx",methods=["GET","POST"])
def download_docx():
    try:
        # Получаем данные формы из JSON

        print('до json')
        form_data = request.get_json()
        print('после json')
        # Здесь используем ваш существующий метод для создания docx
        # Предполагаю, что он называется generate_docx и принимает данные формы
        docx_file = generate_docx(form_data)

        # Отправляем файл клиенту
        print('отправка')
        return send_file(
            docx_file,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name='application.docx'
        )
    except Exception as e:
        return {'error': str(e)}, 400


if __name__ == "__main__":
    app.run(debug=True)