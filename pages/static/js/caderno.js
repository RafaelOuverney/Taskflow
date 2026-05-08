const notebookTitle = document.getElementById('notebookTitle');
const editorContent = document.getElementById('editorContent');
const btnBold = document.getElementById('btnBold');
const btnItalic = document.getElementById('btnItalic');
const btnUnderline = document.getElementById('btnUnderline');
const btnCode = document.getElementById('btnCode');
const btnList = document.getElementById('btnList');
const btnLink = document.getElementById('btnLink');
const notebooksList = document.getElementById('notebooksList');
const btnNewNotebook = document.getElementById('btnNewNotebook');
const saveStatus = document.getElementById('saveStatus');
const visibilitySelect = document.getElementById('visibilitySelect');
const btnDetails = document.getElementById('btnDetails');

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

let saveTimeout;
let currentNotebookId = null;
let isModified = false;

function updateSaveStatus(status) {
    if (status === 'saving') {
        saveStatus.textContent = 'Salvando...';
        saveStatus.classList.add('saving');
        saveStatus.classList.remove('saved');
    } else if (status === 'saved') {
        saveStatus.textContent = 'Salvo';
        saveStatus.classList.add('saved');
        saveStatus.classList.remove('saving');
    } else {
        const now = new Date();
        const time = now.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
        saveStatus.textContent = `Último salvo: ${time}`;
        saveStatus.classList.remove('saved', 'saving');
    }
}

function saveNotebook() {
    if (!currentNotebookId || !isModified) return;

    updateSaveStatus('saving');

    fetch('/api/notebook/save/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            notebook_id: currentNotebookId,
            title: notebookTitle.value,
            content: editorContent.innerHTML
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateSaveStatus('saved');
            isModified = false;
            setTimeout(() => {
                updateSaveStatus('last');
            }, 2000);
        } else {
            console.error('Erro ao salvar:', data.message);
            updateSaveStatus('error');
            showToast('Erro ao salvar caderno', 'error');
        }
    })
    .catch(error => {
        console.error('Erro na requisição:', error);
        showToast('Erro ao salvar caderno', 'error');
    });
}

function debouncedSave() {
    isModified = true;
    clearTimeout(saveTimeout);
    updateSaveStatus('saving');
    saveTimeout = setTimeout(saveNotebook, 1500);
}

function formatText(command, value = null) {
    editorContent.focus();
    
    if (value) {
        document.execCommand(command, false, value);
    } else {
        document.execCommand(command, false, null);
    }
    
    updateToolbarButtons();
    debouncedSave();
}

function updateToolbarButtons() {
    btnBold.classList.toggle('active', document.queryCommandState('bold'));
    btnItalic.classList.toggle('active', document.queryCommandState('italic'));
    btnUnderline.classList.toggle('active', document.queryCommandState('underline'));
}

if (btnBold) {
    btnBold.addEventListener('mousedown', (e) => {
        e.preventDefault();
        formatText('bold');
    });
}

if (btnItalic) {
    btnItalic.addEventListener('mousedown', (e) => {
        e.preventDefault();
        formatText('italic');
    });
}

if (btnUnderline) {
    btnUnderline.addEventListener('mousedown', (e) => {
        e.preventDefault();
        formatText('underline');
    });
}

if (btnCode) {
    btnCode.addEventListener('mousedown', (e) => {
        e.preventDefault();
        formatText('formatBlock', '<pre>');
    });
}

if (btnList) {
    btnList.addEventListener('mousedown', (e) => {
        e.preventDefault();
        formatText('insertUnorderedList');
    });
}

if (btnLink) {
    btnLink.addEventListener('mousedown', (e) => {
        e.preventDefault();
        showModalAddLink();
    });
}

if (editorContent) {
    editorContent.addEventListener('input', () => {
        isModified = true;
        debouncedSave();
    });

    editorContent.addEventListener('paste', (e) => {
        setTimeout(() => {
            isModified = true;
            debouncedSave();
        }, 10);
    });

    editorContent.addEventListener('mouseup', updateToolbarButtons);
    editorContent.addEventListener('keyup', updateToolbarButtons);
}

if (notebookTitle) {
    notebookTitle.addEventListener('change', debouncedSave);
    notebookTitle.addEventListener('input', () => {
        isModified = true;
    });
}

if (btnNewNotebook) {
    btnNewNotebook.addEventListener('click', showModalCreateNotebook);
}

function showModalCreateNotebook() {
    const modal = document.getElementById('modalCreateNotebook');
    const input = document.getElementById('inputNotebookTitle');
    const btnCancel = document.getElementById('btnCancelNotebook');
    const btnConfirm = document.getElementById('btnConfirmNotebook');

    modal.classList.add('active');
    input.value = '';
    input.focus();

    const handleConfirm = () => {
        const title = input.value.trim();
        if (!title) {
            showToast('Por favor, digite um nome para o caderno', 'error');
            return;
        }

        btnConfirm.disabled = true;
        btnConfirm.textContent = 'Criando...';

        fetch('/api/notebook/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ title: title })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Caderno criado com sucesso!', 'success');
                setTimeout(() => {
                    window.location.href = '/caderno/' + data.notebook.id + '/';
                }, 500);
            } else {
                showToast('Erro ao criar caderno: ' + data.message, 'error');
                btnConfirm.disabled = false;
                btnConfirm.textContent = 'Criar Caderno';
            }
        })
        .catch(error => {
            console.error('Erro na requisição:', error);
            showToast('Erro ao criar caderno', 'error');
            btnConfirm.disabled = false;
            btnConfirm.textContent = 'Criar Caderno';
        });
    };

    const handleCancel = () => {
        modal.classList.remove('active');
        btnCancel.removeEventListener('click', handleCancel);
        btnConfirm.removeEventListener('click', handleConfirm);
        input.removeEventListener('keypress', handleKeyPress);
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter') {
            handleConfirm();
        } else if (e.key === 'Escape') {
            handleCancel();
        }
    };

    btnCancel.addEventListener('click', handleCancel);
    btnConfirm.addEventListener('click', handleConfirm);
    input.addEventListener('keypress', handleKeyPress);
}

function showModalAddLink() {
    const modal = document.getElementById('modalAddLink');
    const input = document.getElementById('inputLinkUrl');
    const btnCancel = document.getElementById('btnCancelLink');
    const btnConfirm = document.getElementById('btnConfirmLink');

    modal.classList.add('active');
    input.value = 'https://';
    input.focus();
    input.select();

    const handleConfirm = () => {
        const url = input.value.trim();
        if (!url || url === 'https://') {
            showToast('Por favor, digite uma URL válida', 'error');
            return;
        }

        formatText('createLink', url);
        showToast('Link adicionado com sucesso!', 'success');
        handleCancel();
    };

    const handleCancel = () => {
        modal.classList.remove('active');
        btnCancel.removeEventListener('click', handleCancel);
        btnConfirm.removeEventListener('click', handleConfirm);
        input.removeEventListener('keypress', handleKeyPress);
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter') {
            handleConfirm();
        } else if (e.key === 'Escape') {
            handleCancel();
        }
    };

    btnCancel.addEventListener('click', handleCancel);
    btnConfirm.addEventListener('click', handleConfirm);
    input.addEventListener('keypress', handleKeyPress);
}

function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toastContainer');
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let icon = 'fa-info-circle';
    if (type === 'success') icon = 'fa-check-circle';
    else if (type === 'error') icon = 'fa-exclamation-circle';
    
    toast.innerHTML = `
        <i class="fas ${icon} toast-icon"></i>
        <span class="toast-message">${message}</span>
        <button class="toast-close" title="Fechar">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(toast);
    
    const closeBtn = toast.querySelector('.toast-close');
    const removeToast = () => {
        toast.classList.add('removing');
        setTimeout(() => {
            toast.remove();
        }, 300);
    };
    
    closeBtn.addEventListener('click', removeToast);
    
    if (duration > 0) {
        setTimeout(removeToast, duration);
    }
    
    return toast;
}

function createNewNotebook() {
    showModalCreateNotebook();
}

function showModalConfirm(title, message, isDangerous = false) {
    return new Promise((resolve) => {
        const modal = document.getElementById('modalConfirm');
        const modalTitle = document.getElementById('confirmTitle');
        const modalMessage = document.getElementById('confirmMessage');
        const btnCancel = document.getElementById('btnConfirmCancel');
        const btnOk = document.getElementById('btnConfirmOk');

        modalTitle.textContent = title;
        modalMessage.textContent = message;

        if (isDangerous) {
            btnOk.className = 'modal-btn modal-btn-danger';
            btnOk.textContent = 'Deletar';
        } else {
            btnOk.className = 'modal-btn modal-btn-primary';
            btnOk.textContent = 'Confirmar';
        }

        modal.classList.add('active');
        btnOk.focus();

        const handleConfirm = () => {
            modal.classList.remove('active');
            cleanup();
            resolve(true);
        };

        const handleCancel = () => {
            modal.classList.remove('active');
            cleanup();
            resolve(false);
        };

        const handleKeyPress = (e) => {
            if (e.key === 'Enter') {
                handleConfirm();
            } else if (e.key === 'Escape') {
                handleCancel();
            }
        };

        const cleanup = () => {
            btnCancel.removeEventListener('click', handleCancel);
            btnOk.removeEventListener('click', handleConfirm);
            document.removeEventListener('keydown', handleKeyPress);
        };

        btnCancel.addEventListener('click', handleCancel);
        btnOk.addEventListener('click', handleConfirm);
        document.addEventListener('keydown', handleKeyPress);
    });
}

function loadNotebook(notebookId) {
    window.location.href = '/caderno/' + notebookId + '/';
}

async function deleteNotebook(notebookId) {
    const confirmed = await showModalConfirm(
        'Deletar Caderno',
        'Tem certeza que deseja deletar este caderno? Esta ação não pode ser desfeita.',
        true
    );
    
    if (!confirmed) return;

    fetch('/api/notebook/delete/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            notebook_id: notebookId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Caderno deletado com sucesso!', 'success');
            setTimeout(() => {
                window.location.href = '/caderno/';
            }, 500);
        } else {
            showToast('Erro ao deletar caderno: ' + data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Erro na requisição:', error);
        showToast('Erro ao deletar caderno', 'error');
    });
}

// ===== Event Listeners for Notebook Items =====
document.querySelectorAll('.notebook-item').forEach(item => {
    item.addEventListener('click', (e) => {
        if (e.target.closest('.btn-delete-notebook')) return;
        
        const notebookId = item.dataset.notebookId;
        loadNotebook(notebookId);
    });
});

document.querySelectorAll('.btn-delete-notebook').forEach(btn => {
    btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const notebookId = btn.dataset.notebookId;
        deleteNotebook(notebookId);
    });
});

function getCurrentNotebookId() {
    const titleInput = document.getElementById('notebookTitle');
    if (titleInput) {
        const activeItem = document.querySelector('.notebook-item.active');
        if (activeItem) {
            return activeItem.dataset.notebookId;
        }
    }
    return null;
}

document.addEventListener('DOMContentLoaded', () => {
    const activeItem = document.querySelector('.notebook-item.active');
    if (activeItem) {
        currentNotebookId = activeItem.dataset.notebookId;
    }

    if (!currentNotebookId) {
        const firstItem = document.querySelector('.notebook-item');
        if (firstItem) {
            currentNotebookId = firstItem.dataset.notebookId;
        }
    }

    if (notebookTitle && notebookTitle.value) {
        updateSaveStatus('last');
    }

    if (editorContent) {
        editorContent.addEventListener('drag', (e) => {
            e.preventDefault();
        });
        
        editorContent.addEventListener('drop', (e) => {
            e.preventDefault();
            const text = e.dataTransfer.getData('text/plain');
            if (text) {
                document.execCommand('insertText', false, text);
            }
        });
    }

    console.log('Caderno JS initialized - Notebook ID:', currentNotebookId);
});

document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        saveNotebook();
    }

    if (editorContent && editorContent.contains(e.target)) {
    }
});

window.addEventListener('beforeunload', (e) => {
    if (isModified) {
        e.preventDefault();
        e.returnValue = 'Você tem alterações não salvas. Tem certeza que deseja sair?';
    }
});

if (visibilitySelect) {
    visibilitySelect.addEventListener('change', (e) => {
        const visibility = e.target.value;
        console.log('Visibilidade alterada para:', visibility);
    });
}

if (btnDetails) {
    btnDetails.addEventListener('click', () => {
        console.log('Menu de detalhes clicado');
    });
}

const btnCreateFirstNotebook = document.getElementById('btnCreateFirstNotebook');
if (btnCreateFirstNotebook) {
    btnCreateFirstNotebook.addEventListener('click', createNewNotebook);
}

console.log('Caderno JS fully loaded with WYSIWYG editor');
