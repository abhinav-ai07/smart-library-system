// Generic reusable API call wrapper
async function apiCall(url, method='GET', body=null) {
    const options = {
        method,
        headers: { 'Content-Type': 'application/json' }
    };
    if (body) {
        options.body = JSON.stringify(body);
    }
    const res = await fetch(url, options);
    return res.json();
}

function issueBook(bookId) {
    if(!confirm("Are you sure you want to issue this book?")) return;
    
    apiCall('/api/issue', 'POST', { book_id: bookId })
    .then(data => {
        if(data.status === 'success') {
            alert(data.msg);
            location.reload();
        } else {
            let msg = data.msg;
            if(data.alternative) {
                msg += `\nWould you like to try our recommendation instead?\nAlternative: ${data.alternative.title} (${data.alternative.genre})`;
            }
            alert(msg);
            // Optionally redirect to recommend or search
        }
    }).catch(err => {
        console.error(err);
        alert('An error occurred.');
    });
}

function returnBook(bookId) {
    if(!confirm("Are you sure you want to return this book?")) return;
    
    apiCall('/api/return', 'POST', { book_id: bookId })
    .then(data => {
        if(data.status === 'success') {
            alert(data.msg);
            location.reload();
        } else {
            alert(data.msg);
        }
    }).catch(err => {
        console.error(err);
        alert('An error occurred.');
    });
}

// Dark Mode Toggle
function toggleDarkMode() {
    document.documentElement.classList.toggle('dark');
    const isDark = document.documentElement.classList.contains('dark');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
}

// Check theme on load
document.addEventListener('DOMContentLoaded', () => {
    if (localStorage.getItem('theme') === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
});
