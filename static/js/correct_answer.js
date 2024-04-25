function getCSRFToken() {
    const csrfCookie = document.cookie.split(';').find(cookie => cookie.trim().startsWith('csrftoken='));
    if (csrfCookie) {
        return csrfCookie.split('=')[1];
    }
    return null;
}

let checkboxes = document.getElementsByClassName('form-check-input');

for (let item of checkboxes) {
    item.addEventListener('click', () => {
    const request = new Request('/correct_answer', {
    method: 'POST',
    body: JSON.stringify({
    id: item.dataset.id,
    }),
    headers: {
    'Accept': 'application/json, text/plain',
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken()
    },
});
        fetch(request)
            .then(response => {
                return response.json();
            })
.then(data => {
    console.log(data);
    if (data.key == 'false') {
        item.removeAttribute('checked');
    } else {
        item.checked = true;
    }
});

    });
}
