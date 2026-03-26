function addStudent() {
    const container = document.getElementById('students-container');
    const studentForm = container.children[0].cloneNode(true);

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
        console.log(element);
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


    container.appendChild(studentForm);
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
        } else {
            alert('Должен быть хотя бы один слушатель');
        }
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
       return;
   }

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
});

