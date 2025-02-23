function updateFavoriteButton(message) {
    const favoriteForm = document.querySelector('form[action*="toggle-favorite"]');
    if (favoriteForm) {
        const btn = favoriteForm.querySelector('button');
        if (message.includes('已添加到收藏')) {
            btn.className = 'btn btn-warning';
            btn.innerHTML = '<i class="bi bi-star-fill"></i> 取消收藏';
        } else if (message.includes('已取消收藏')) {
            btn.className = 'btn btn-outline-warning';
            btn.innerHTML = '<i class="bi bi-star"></i> 收藏职位';
        }
    }
}

function handleClaimJob(event) {
    const form = event.target.closest('form');
    if (form && form.getAttribute('action').includes('claim-job')) {
        const confirmClaim = confirm('确定要认领这个职位吗？');
        if (!confirmClaim) {
            event.preventDefault();
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const claimForms = document.querySelectorAll('form[action*="claim-job"]');
    claimForms.forEach(form => {
        form.addEventListener('submit', handleClaimJob);
    });
});