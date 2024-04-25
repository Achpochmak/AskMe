function getCSRFToken() {
    const csrfCookie = document.cookie.split(';').find(cookie => cookie.trim().startsWith('csrftoken='));
    if (csrfCookie) {
        return csrfCookie.split('=')[1];
    }
    return null;
}

let items = document.getElementsByClassName('likes-section');

for (let item of items) {
    const inputElement = item.querySelector('.form-control');
    const [button, , counter] = item.children;
    button.addEventListener('click', () => {
    const request = new Request('/like', {
    method: 'POST',
    body: JSON.stringify({
    id: button.dataset.id,
    type: button.dataset.type
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
                inputElement.value = data.key;
            });
    });
}
