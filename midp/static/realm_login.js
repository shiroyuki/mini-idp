window.addEventListener('load', () => {
  let formContainer = document.querySelector('.form-container')
  let feedback = formContainer.querySelector('.feedback');
  let form = formContainer.querySelector('form');
  form.addEventListener('submit', e => {
    e.preventDefault();
    e.stopPropagation()

    let formData = new FormData(form);
    let formInputs = form.querySelectorAll('input[type="text"],input[type="password"],button');

    form.style.display = 'none';
    feedback.classList.add('in-flight');
    feedback.classList.remove('ok');
    feedback.classList.remove('error');
    feedback.innerHTML = '⏳ Signing in...';
    formInputs.forEach(input => input.disabled = true);

    fetch(
      `/realms/${realmId}/login`,
      {
        method: 'post',
        headers: { 'Accept': 'application/json' },
        body: formData,
      }
    )
      .then(async response => {
        if (response.status === 200) {
          data = await response.json();
          console.log(data);
          if (data.error === null) {
            feedback.classList.add('ok');
            feedback.innerHTML = '✅ Authenticated';
            formContainer.querySelector('h1').style.display = 'none';
          } else {
            form.style.display = 'flex';
            feedback.classList.add('error');
            feedback.innerHTML = data.error_description || `🔥 Error Code: ${data.error}`;
            formInputs.forEach(input => input.disabled = false);
          }
        } else {
          form.style.display = 'flex';
          feedback.classList.add('error');
          feedback.innerHTML = `🔥 Unexpected Error (HTTP ${response.status})`
          formInputs.forEach(input => input.disabled = false);
          return;
        }
      })
      .finally(() => {
        feedback.classList.remove('in-flight');
      });
  });
});
