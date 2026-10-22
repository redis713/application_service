const NAME_REGEX = /^[А-ЯЁ][а-яё]+(?:[- ][А-ЯЁ][а-яё]+)*$/;
const INN_REGEX = /^\d{10}$/;
const OGRN_REGEX = /^\d{13}$/;
const KPP_REGEX = /^\d{9}$/;
const SNILS_REGEX = /^\d{11}$/;

let studentTemplate;
let categoryTemplate;

function addStudent() {
    const container = document.getElementById('students-container');
   //const studentForm = container.children[0].cloneNode(true);

    const studentForm = studentTemplate.cloneNode(true);

    const newIndex = container.children.length;
    console.log(newIndex);

    // Новый номер слушателя
    studentForm.querySelectorAll("div.counter").forEach(element => {
        element.innerHTML = '№ ' + (newIndex + 1);
    });

    studentForm.querySelectorAll("div.destroy_button").forEach(btn => {
        btn.addEventListener('click', function() {
            removeStudent(this);
        });
    });

    //Эта штука меняет id у всех полей
    studentForm.querySelectorAll('[id]').forEach(element => {
        const oldId = element.id;
        const newId = oldId.replace(/\d+/, newIndex);
        element.id = newId;

        // Обновляем также связанные label элементы
        const labels = studentForm.querySelectorAll(`label[for="${oldId}"]`);
        labels.forEach(label => {
            label.setAttribute('for', newId);
        });
    });


    // Очищаем значения полей
    const inputs = studentForm.querySelectorAll('input');
    inputs.forEach(input => {
        if (input.type != 'radio')
            input.value = '';

        // Обновляем name атрибут для нового индекса
        const newIndex = container.children.length;
        input.name = input.name.replace(/\d+/, newIndex);
    });

    // Очищаем select
    const selects = studentForm.querySelectorAll('select');
    selects.forEach(select => {
        select.selectedIndex = 0;
        // Обновляем name атрибут
        const newIndex = container.children.length;
        select.name = select.name.replace(/\d+/, newIndex);
    });

    //превращаем чистый select в tom select
    select = studentForm.querySelector('.category-select');
    initCategorySelect(select);

    container.appendChild(studentForm);

    rebuildNavigation();
}



function removeStudent(button) {
    //alert(1);
    const studentsContainer = document.getElementById('students-container');
        if (studentsContainer.children.length > 1) {
            button.closest('.student-form').remove();

            // Обновляем индексы для всех оставшихся форм
            const forms = studentsContainer.children;
            for (let i = 0; i < forms.length; i++) {
                const form = forms[i];

                // Обновляем номера слушателей
                form.querySelectorAll("div.counter").forEach(element => {
                    element.innerHTML = '№' + (i + 1);
                     element.id = 'student-' + i;
                });

                // Обновляем все input и select элементы
                form.querySelectorAll('input, select').forEach(element => {
                    // Обновляем name атрибут
                    if (element.name) {
                        element.name = element.name.replace(/students-\d+/, `students-${i}`);
                    }
                    // Обновляем id атрибут
                    if (element.id) {
                        element.id = element.id.replace(/students-\d+/, `students-${i}`);
                    }
                });

                // Обновляем все label элементы
                form.querySelectorAll('label').forEach(label => {
                    const forAttr = label.getAttribute('for');
                    if (forAttr) {
                        label.setAttribute('for', forAttr.replace(/students-\d+/, `students-${i}`));
                    }
                });

                // Обновляем все div с error-message
                form.querySelectorAll('.error-message').forEach(errorDiv => {
                    if (errorDiv.id) {
                        errorDiv.id = errorDiv.id.replace(/students-\d+/, `students-${i}`);
                    }
                });
            }
            rebuildNavigation();
        }
        else {
            alert('Должен быть хотя бы один слушатель');
        }
}

function validate_fio(fio) {
    // функция проверки имени
    if(!NAME_REGEX.test(fio))
        return "ФИО должны начинаться с заглавной буквы и содержать только буквы, пробелы и тире!";
}
function validate_inn(inn) {
    // функция проверки ИНН
    if(!INN_REGEX.test(inn))
        return "ИНН должен содержать только числа, не более 10!";
}
function validate_ogrn(ogrn) {
// функция проверки ОГРН
    if(!OGRN_REGEX.test(ogrn))
        return "ОГРН должен содержать только числа, не более 13!";
}
function validate_snils(snils) {
// функция проверки СНИЛС
    if(!SNILS_REGEX.test(snils))
        return "Снилс должен содержать только 11 цифр!";
}
function validate_kpp(kpp) {
// функция проверки КПП
    if(!KPP_REGEX.test(kpp))
        return "КПП должен содержать только 9 цифр!";
}


function validateAll() {
    const boss_firstname = document.getElementById('boss_firstname');
    const boss_lastname = document.getElementById('boss_lastname');
    const boss_patronymic = document.getElementById('boss_patronymic');
    const ogrn = document.getElementById('ogrn');
    const inn = document.getElementById('inn');
    const kpp = document.getElementById('kpp');

    let allValid = true;

    let error = validate_fio(boss_firstname.value);
    if (error) {
        allValid = false;
    }

    error = validate_fio(boss_lastname.value);
    if (error) {
        allValid = false;
    }

    error = validate_fio(boss_patronymic.value);
    if (error) {
        allValid = false;
    }

    error = validate_ogrn(ogrn.value);
    if (error) {
        allValid = false;
    }

    error = validate_inn(inn.value);
    if (error) {
        allValid = false;
    }

    error = validate_kpp(kpp.value);
    if (error) {
        allValid = false;
    }


    return allValid;
}


function downloadDocx() {
   // Проверяем заполнение всех обязательных полей
   const form = document.querySelector('form');
   const formData = new FormData(form);
   const requiredFields = form.querySelectorAll('[required]');

   let isValid = true;
   requiredFields.forEach(field => {
       if (!field.value) {
           isValid = false;
           field.closest('.form-group').classList.add('has-error');
       }
   });

   if (!isValid) {
       alert('Пожалуйста, заполните все обязательные поля');
       //return;
   }

   if (!validateAll())
        alert("ошибки!!!!!!!!!!!!!!!!");


   //НАДО ДОПИСАТЬ СЮДА ВСЕ ПРОВЕРКИ ПОЛЕЙ!!!!!!!

   // Собираем данные формы
   const formObject = {
       organization: {
           organization_full_name: formData.get('organization_full_name'),
           organization_short_name: formData.get('organization_short_name'),
           boss_firstname: formData.get('boss_firstname'),
           boss_lastname: formData.get('boss_lastname'),
           boss_patronymic: formData.get('boss_patronymic'),
           doljnost_boss: formData.get('doljnost_boss'),
           polnamochia_boss: formData.get('polnamochia_boss'),
           ogrn: formData.get('ogrn'),
           inn: formData.get('inn'),
           kpp: formData.get('kpp'),
           bank_name: formData.get('bank_name'),
           rasch_schot: formData.get('rasch_schot'),
           bik: formData.get('bik'),
           fakt_address: formData.get('fakt_address'),
           yur_address: formData.get('yur_address'),
           telephone: formData.get('telephone'),
           email: formData.get('email'),
           doljnost_executor: formData.get('doljnost_executor'),
           fio_executor: formData.get('fio_executor'),
           telephone_executor: formData.get('telephone_executor')
       },
       students: []
   };

   // Собираем данные слушателей
   const studentForms = document.querySelectorAll('.student-form');
   studentForms.forEach((studentForm, index) => {
       formObject.students.push({
           student_firstname: formData.get(`students-${index}-student_firstname`),
           student_lastname: formData.get(`students-${index}-student_lastname`),
           student_patronymic: formData.get(`students-${index}-student_patronymic`),
           student_birthdate: formData.get(`students-${index}-student_birthdate`),
           citizenship: formData.get(`students-${index}-citizenship`),
           education:formData.get(`students-${index}-education`),
           institute_name: formData.get(`students-${index}-institute_name`),
           diploma_seriesnumber: formData.get(`students-${index}-diploma_seriesnumber`),
           diploma_date: formData.get(`students-${index}-diploma_date`),
           diploma_lastname: formData.get(`students-${index}-diploma_lastname`),
           snils: formData.get(`students-${index}-snils`),
           student_position: formData.get(`students-${index}-student_position`),
           student_category: formData.get(`students-${index}-student_category`),
          // fire_safety_document_type: formData.get(`students-${index}-fire_safety_document_type`),
          // fire_institution: formData.get(`students-${index}-certificate_institution`),
          // fire_series: formData.get(`students-${index}-diploma_series`),
         //  fire_number: formData.get(`students-${index}-certificate_number`),
          // fire_date: formData.get(`students-${index}-certificate_date`),
           start_date: formData.get(`students-${index}-start_date`),
           end_date: formData.get(`students-${index}-end_date`),
           student_telephone: formData.get(`students-${index}-student_telephone`),
           diploma_delivery: formData.get(`students-${index}-diploma_delivery`),
           delivery_address: formData.get(`students-${index}-delivery_address`),
           student_email: formData.get(`students-${index}-student_email`)
       });
   });

   console.log(formObject);

   // Отправляем AJAX запрос
   fetch('/download-docx', {
       method: 'POST',
       headers: {
           'Content-Type': 'application/json',
           'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
       },
       body: JSON.stringify(formObject)
   })
   .then(response => {
       if (!response.ok) {
           throw new Error('Network response was not ok');
       }
       return response.blob();
   })
   .then(blob => {
       // Создаем ссылку для скачивания
       const url = window.URL.createObjectURL(blob);
       const a = document.createElement('a');
       a.href = url;
       a.download = 'application.docx';
       document.body.appendChild(a);
       a.click();
       window.URL.revokeObjectURL(url);
       a.remove();
   })
   .catch(error => {
       console.error('Error:', error);
       alert('Произошла ошибка при скачивании файла');
   });
}


function rebuildNavigation() {
    const navigation = document.getElementById('navigation');

    navigation.querySelectorAll('.navigation-item').forEach(el => el.remove());

    document.querySelectorAll('.student-form').forEach((student, index) => {

        const lastname = student.querySelector('[id$="student_lastname"]')?.value ?? '';
        const firstname = student.querySelector('[id$="student_firstname"]')?.value ?? '';
        const patronymic = student.querySelector('[id$="student_patronymic"]')?.value ?? '';

        const fio = `${lastname} ${firstname} ${patronymic}`.trim();


        const link = document.createElement('a');
        link.href = `#student-${index}`;
        link.classList.add('navigation-item');

        link.innerHTML = `
            <div class="navigation-row">
                ${index + 1}. ${fio}
            </div>
        `;

        navigation.appendChild(link);
    });
}

function addCategoryBlock(event) {

    const studentForm = event.target.closest('.student-form');

    const container = studentForm.querySelector('.categories-container');

    const newRow = categoryTemplate.cloneNode(true);



    const categoryIndex =
        container.querySelectorAll('.category-row').length;

    const studentIndex =
        studentForm.querySelector('.counter')
            .id.match(/\d+/)[0];

    newRow.querySelectorAll('[id]').forEach(element => {

        element.id = element.id.replace(
            /student_categories-\d+/,
            `student_categories-${categoryIndex}`
        );

        element.id = element.id.replace(
            /students-\d+/,
            `students-${studentIndex}`
        );

    });

    newRow.querySelectorAll('[name]').forEach(element => {

        element.name = element.name.replace(
            /student_categories-\d+/,
            `student_categories-${categoryIndex}`
        );

        element.name = element.name.replace(
            /students-\d+/,
            `students-${studentIndex}`
        );

    });

    newRow.querySelectorAll('select').forEach(select => {
        select.selectedIndex = 0;
    });

    newRow.querySelectorAll('input[type="date"]').forEach(input => {
        input.value = '';
    });



    container.appendChild(newRow);

    newRow.querySelectorAll('select').forEach(select => {
        initCategorySelect(select);
    });
}


function reindexStudents() {
    document.querySelectorAll('.counter')
        .forEach((counter, index) => {
            counter.id = `student-${index}`;
            counter.textContent = `№ ${index + 1}`;
        });
}


function reindexCategories(container) {

    container.querySelectorAll('.category-row')
        .forEach((row, index) => {

            row.querySelectorAll('[id]').forEach(element => {

                element.id = element.id.replace(
                    /student_categories-\d+/,
                    `student_categories-${index}`
                );

            });

            row.querySelectorAll('[name]').forEach(element => {

                element.name = element.name.replace(
                    /student_categories-\d+/,
                    `student_categories-${index}`
                );

            });

        });
}




function initCategorySelect(select) {
    if (select.tomselect) return;

    new TomSelect(select, {create: false, closeAfterSelect: true, onItemAdd: function() {this.blur();}});
}



function cleanTemplate(template) {

    // Очистка текстовых полей и дат
    template.querySelectorAll('input').forEach(input => {

        if (
            input.type !== 'hidden' &&
            input.type !== 'radio' &&
            input.type !== 'checkbox'
        ) {
            input.value = '';
        }

    });

    // Очистка select
    template.querySelectorAll('select').forEach(select => {
        select.selectedIndex = 0;
    });

    // Удаление сообщений об ошибках WTForms
    template.querySelectorAll('.error-message')
        .forEach(error => error.remove());

    // Если в шаблон случайно попал Tom Select
    template.querySelectorAll('.ts-wrapper')
        .forEach(wrapper => wrapper.remove());

    return template;
}


document.addEventListener("DOMContentLoaded", () => {
    console.log("Страница загружена");


    document.querySelectorAll('.destroy_button').forEach(btn => {
        btn.addEventListener('click', function() {
            removeStudent(this);
        });
    });

    document.getElementById( "add_button" ).onclick = addStudent;

    document.getElementById( "docx_button" ).onclick = downloadDocx;
    //document.getElementById( "add_button" ).addEventListener('click', addStudent);

    // перестройка навигации при вводе текста
    document.addEventListener('input', function(event) {

        if (!event.target.id.match(/student_(lastname|firstname|patronymic)$/))
            return;

        rebuildNavigation();
    });

    //добавление нового поля категории
    document.addEventListener('click', function(event) {

        if (!event.target.classList.contains('add-category-button'))
            return;

        addCategoryBlock(event);

    });

    // удаление поля категории
    document.addEventListener('click', function(event) {

        if (!event.target.classList.contains('remove-category-button'))
            return;

        const row = event.target.closest('.category-row');

        const container = row.parentElement;

        if (container.children.length === 1)
            return;

        row.remove();

        reindexCategories(container);
    });

//     document.querySelectorAll('select').forEach(select => {
//        new TomSelect(select);
//    });



    studentTemplate =document.querySelector('#students-container').children[0].cloneNode(true);
    categoryTemplate = document.querySelector('.category-row').cloneNode(true);

    console.log(studentTemplate.outerHTML);
    console.log(categoryTemplate.outerHTML);


    cleanTemplate(studentTemplate);
    cleanTemplate(categoryTemplate);

    document.querySelectorAll('.category-row select').forEach(select => {
        initCategorySelect(select);
    });

    //Пересчет номеров слушателей и их id
    reindexStudents();
    rebuildNavigation();


//    document.querySelectorAll(
//        'select[id*="student_categories"]'
//    ).forEach(select => {
//
//        new TomSelect(select);
//
//    });

});

