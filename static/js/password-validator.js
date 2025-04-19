/**
 * 密碼確認匹配檢查器
 */
document.addEventListener('DOMContentLoaded', function () {
    const passwordInput = document.getElementById('new_password');
    const confirmInput = document.getElementById('confirm_password');
    const passwordFeedback = document.getElementById('passwordFeedback');
    const form = document.getElementById('passwordForm');
    const submitBtn = document.getElementById('submitBtn');

    if (!passwordInput || !confirmInput || !form || !passwordFeedback) return;

    // 檢查密碼是否匹配
    function checkPasswordsMatch() {
        if (confirmInput.value === '') {
            passwordFeedback.textContent = '';
            passwordFeedback.classList.remove('text-success', 'text-danger');
            confirmInput.classList.remove('border-success', 'border-danger');
            return;
        }

        if (passwordInput.value === confirmInput.value) {
            passwordFeedback.textContent = '密碼匹配';
            passwordFeedback.classList.add('text-success');
            passwordFeedback.classList.remove('text-danger');
            confirmInput.classList.add('border-success');
            confirmInput.classList.remove('border-danger');
            submitBtn.disabled = false;
        } else {
            passwordFeedback.textContent = '密碼不匹配';
            passwordFeedback.classList.add('text-danger');
            passwordFeedback.classList.remove('text-success');
            confirmInput.classList.add('border-danger');
            confirmInput.classList.remove('border-success');
            submitBtn.disabled = true;
        }
    }

    // 監聽輸入事件
    passwordInput.addEventListener('input', checkPasswordsMatch);
    confirmInput.addEventListener('input', checkPasswordsMatch);

    // 表單提交前驗證
    form.addEventListener('submit', function (e) {
        if (passwordInput.value !== confirmInput.value) {
            e.preventDefault();
            alert('確認密碼與新密碼不符');
            return false;
        }
    });
}); 